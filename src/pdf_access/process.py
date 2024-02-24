# Standard Python Libraries
import logging
from pathlib import Path
import re
from typing import Any, Dict, Optional
import tempfile
import uuid

# Third-Party Libraries
import fitz
from rich.progress import Progress, SpinnerColumn, MofNCompleteColumn

from . import PostProcessBase, TechniqueBase, Config, Source, Publisher


def verify_paths(in_path: Path, out_path: Path) -> bool:
    if not in_path.exists():
        logging.error("Input path does not exist: %s", in_path)
        return False
    if not out_path.exists():
        logging.error("Output path does not exist: %s", out_path)
        return False
    return True


def do_authentication(doc: fitz.Document, publishers: Dict[str, Publisher]) -> bool:
    """Attempt to authenticate the document using the passwords for the publishers."""
    if not doc.is_encrypted:
        logging.debug("Document is not encrypted")
        return True
    logging.info("Password required. Attempting to authenticate")

    for publisher_name, publisher in publishers.items():
        for password in publisher.passwords:
            logging.debug("Attempting password for %s", publisher_name)
            if doc.authenticate(password):
                logging.info("Authenticated with password for %s", publisher_name)
                return True
    return False


def select_publishers(
    source: Source, publishers: Dict[str, Publisher]
) -> Dict[str, Publisher]:
    # If the source defines publishers, use them; otherwise, use all
    if len(source.publishers) == 0:
        logging.debug("All publishers are in scope for this source")
        return publishers
    # select the publishers that are in scope for this source
    selected_publishers = {
        key: value for key, value in publishers.items() if key in source.publishers
    }
    logging.debug(
        "Publishers in scope for this source: %s", ", ".join(selected_publishers)
    )
    return selected_publishers


def choose_publisher(
    doc: fitz.Document, publishers: Dict[str, Publisher]
) -> Optional[Dict[str, Publisher]]:
    """Check the metadata to determine the publisher of the document."""
    logging.debug("Metadata: %s", doc.metadata)
    for publisher_name, publisher in publishers.items():
        matches_failed = False
        logging.debug('Evaluating publisher: "%s"', publisher_name)
        # Check to see if filename matches the path_regex
        if not re.search(publisher.path_regex, doc.name):
            logging.debug(
                'Path regex "%s" does not match: "%s"',
                publisher.path_regex.pattern,
                doc.name,
            )
            matches_failed = True
            continue
        else:
            logging.debug(
                'Path regex "%s" matches: "%s"', publisher.path_regex.pattern, doc.name
            )
        for field, regex in publisher.metadata_search.items():
            if matches_failed:
                logging.debug(
                    'Search failure occurred, skipping publisher: "%s"', publisher_name
                )
                break
            logging.debug('Searching field "%s" for regex "%s"', field, regex)
            if field not in doc.metadata:
                logging.debug('Metadata field not found: "%s"', field)
                matches_failed = True
                continue
            if not re.search(regex, doc.metadata[field]):
                logging.debug(
                    'Metadata regex "%s" does not match: {"%s": "%s"}',
                    regex,
                    field,
                    doc.metadata[field],
                )
                matches_failed = True
                continue
            logging.debug(
                'Metadata regex "%s" matches: {"%s": "%s"}',
                regex,
                field,
                doc.metadata[field],
            )
        if not matches_failed:
            logging.debug('All metadata regexes matched for "%s"', publisher_name)
            return publisher
    logging.debug("No publishers matched")
    return None


def apply_techniques(
    doc: fitz.Document,
    config: Config,
    publisher: Dict[str, Any],
    tech_registry: dict[str, TechniqueBase],
) -> None:
    # Get the list of plans for this publisher
    for plan_name in publisher.plans:
        if not (plan := config.plans.get(plan_name)):
            logging.warn('Skipping unknown plan "%s"', plan_name)
            continue
        if not (tech_function := tech_registry.get(plan.technique)):
            logging.warn('Skipping unknown technique "%s"', plan)
            continue
        logging.info("Running plan: %s", plan_name)
        logging.info("Applying technique: %s", tech_function.nice_name)
        logging.debug("Calling technique with: %s, %s", doc, plan.args)
        change_count = tech_function.apply(doc=doc, **plan.args)
        if change_count:
            logging.debug("Changes made: %s", change_count)
        else:
            logging.warm("No changes made")


def save_pdf(doc: fitz.Document, out_file: Path, debug: bool = False) -> None:
    """Save the document to the output file."""
    if debug:
        logging.debug("Saving unoptimized (debug) file to %s", out_file)
        doc.save(
            out_file,
            ascii=True,
            clean=True,
            deflate=False,
            expand=255,
            garbage=4,
            linear=False,
            pretty=True,
        )
    else:
        logging.debug("Saving optimized file to %s", out_file)
        # TODO move scrub to technique
        doc.scrub(
            attached_files=True,
            clean_pages=True,
            embedded_files=True,
            hidden_text=True,
            javascript=True,
            metadata=True,
            redactions=True,
            redact_images=0,
            remove_links=True,
            reset_fields=True,
            reset_responses=False,  # causes seg-fault
            thumbnails=True,
            xml_metadata=True,
        )
        doc.save(
            out_file,
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            linear=True,
            clean=True,
        )


def apply_post_processing(
    in_file: Path,
    out_file: Path,
    source: Source,
    post_process_registry: Dict[str, PostProcessBase],
):
    # loop through post-processors
    for post_processor_name in source.post_process:
        if not (post_processor := post_process_registry.get(post_processor_name)):
            logging.warn(
                'Skipping unknown post-processor "%s"',
                post_processor_name,
            )
            continue
        logging.info("Applying post-processor: %s", post_processor.nice_name)
        post_processor.apply(in_path=in_file, out_path=out_file)


def process(
    config: Config,
    tech_registry: dict[str, TechniqueBase],
    post_process_registry: dict[str, PostProcessBase],
    debug: bool = False,
    dry_run: bool = False,
    force: bool = False,
) -> None:
    """Process the PDF files according to the configuration."""

    logging.debug(
        "%s sources found: %s", len(config.sources), ", ".join(config.sources)
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir: Path = Path(temp_dir)
        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            MofNCompleteColumn(),
        ) as progress:
            # loop through sources
            if len(config.sources) > 1:
                source_task = progress.add_task(
                    "Sources",
                    total=len(config.sources),
                )
            else:
                source_task = None
            for source_name, source in config.sources.items():
                logging.info("Processing source: %s", source_name)
                in_path = Path(source.in_path)
                out_path = Path(source.out_path)
                out_suffix = source.out_suffix
                if not verify_paths(in_path, out_path):
                    logging.warn("Skipping source %s", source_name)
                    if source_task:
                        progress.update(source_task, advance=1)
                    continue
                # determine which publishers are in scope for this source
                publishers = select_publishers(source, config.publishers)
                # recursively process the input path
                in_files = list(in_path.glob("**/*.pdf"))
                files_task = progress.add_task(
                    "Files",
                    total=len(in_files),
                )
                for in_file in in_files:
                    logging.debug("Evaluating file: %s", in_file)
                    # calculate the output path for the file
                    out_file = out_path / in_file.relative_to(in_path).with_stem(
                        in_file.stem + out_suffix
                    )
                    # if the out_file already exists and it's newer than the in_file, skip it
                    if (
                        not force
                        and out_file.exists()
                        and out_file.stat().st_mtime > in_file.stat().st_mtime
                    ):
                        logging.debug("Output file is already up to date")
                        progress.update(files_task, advance=1)
                        continue
                    logging.info("-" * 80)
                    logging.info("Processing file: %s", in_file)
                    logging.info("Output file:     %s", out_file)
                    # Create a temporary file to save the output
                    temp_out_file: Path = temp_dir / (str(uuid.uuid4()) + ".pdf")
                    # process the file
                    with fitz.open(in_file) as doc:
                        if not do_authentication(doc, publishers):
                            logging.warn("Skipping file since no password found")
                            progress.update(files_task, advance=1)
                            continue
                        if not (publisher := choose_publisher(doc, publishers)):
                            logging.warn("Skipping file since no publisher found")
                            progress.update(files_task, advance=1)
                            continue
                        apply_techniques(doc, config, publisher, tech_registry)
                        save_pdf(doc, temp_out_file, debug=debug)

                        apply_post_processing(
                            in_file, temp_out_file, source, post_process_registry
                        )

                        if dry_run:
                            logging.info("Dry run: not saving file %s", out_file)
                            temp_out_file.unlink()
                        else:
                            logging.debug("Saving final output to %s", out_file)
                            # create the output directory if it doesn't exist
                            out_file.parent.mkdir(parents=True, exist_ok=True)
                            temp_out_file.replace(out_file)
                    progress.update(files_task, advance=1)
                progress.remove_task(files_task)
                if source_task:
                    progress.update(source_task, advance=1)
