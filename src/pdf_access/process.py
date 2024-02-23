# Standard Python Libraries
import logging
from pathlib import Path
import re
from typing import Any, Dict, Optional
import tempfile
import uuid

# Third-Party Libraries
import fitz

from . import PostProcessBase, TechniqueBase


def verify_paths(in_path: Path, out_path: Path) -> bool:
    if not in_path.exists():
        logging.error("Input path does not exist: %s", in_path)
        return False
    if not out_path.exists():
        logging.error("Output path does not exist: %s", out_path)
        return False
    return True


def do_authentication(doc: fitz.Document, publishers: Dict[str, Any]) -> bool:
    """Attempt to authenticate the document using the passwords for the publishers."""
    if not doc.is_encrypted:
        logging.debug("Document is not encrypted")
        return True
    logging.info("Password required. Attempting to authenticate")

    for publisher_name, publisher in publishers.items():
        passwords = publisher.get("passwords", [])
        for password in passwords:
            logging.debug("Attempting password for %s", publisher_name)
            if doc.authenticate(password):
                logging.info("Authenticated with password for %s", publisher_name)
                return True
    return False


def select_publishers(
    source: Dict[str, Dict], publishers: Dict[str, Dict]
) -> Dict[str, Dict]:
    # If the source defines publishers, use them; otherwise, use all
    publisher_keys = source.get("publishers", None)
    if publisher_keys is None:
        logging.debug("All publishers are in scope for this source")
        return publishers
    # select the publishers that are in scope for this source
    selected_publishers = {
        key: value for key, value in publishers.items() if key in publisher_keys
    }
    logging.debug(
        "Publishers in scope for this source: %s", ", ".join(selected_publishers)
    )
    return selected_publishers


def choose_publisher(
    doc: fitz.Document, publishers: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Check the metadata to determine the publisher of the document."""
    logging.debug("Metadata: %s", doc.metadata)
    for publisher_name, publisher in publishers.items():
        matches_failed = False
        logging.debug("Evaluating publisher for selection: %s", publisher_name)
        for field, regex in publisher.get("metadata_search", {}).items():
            if matches_failed:
                logging.debug(
                    "Search failure occurred, skipping publisher: %s", publisher_name
                )
                break
            logging.debug('Searching field "%s" for regex "%s"', field, regex)
            if field not in doc.metadata:
                logging.debug("Metadata field not found: %s", field)
                matches_failed = True
                continue
            if not re.search(regex, doc.metadata[field]):
                logging.debug(
                    "Metadata regex %s does not match: %s: %s",
                    regex,
                    field,
                    doc.metadata[field],
                )
                matches_failed = True
                continue
            logging.debug("All metadata regexes matched for %s", publisher_name)
            return publisher
    logging.debug("No publishers matched")
    return None


def apply_techniques(
    doc: fitz.Document,
    config: Dict[str, Any],
    publisher: Dict[str, Any],
    tech_registry: dict[str, TechniqueBase],
) -> None:
    # Get the list of plans for this publisher
    plan_names = publisher.get("plans", [])
    for plan_name in plan_names:
        if not (plan := config["plans"].get(plan_name)):
            logging.warn('Skipping unknown plan "%s"', plan_name)
            continue
        if not (tech_function := tech_registry.get(plan["technique"])):
            logging.warn('Skipping unknown technique "%s"', plan)
            continue
        logging.info("Running plan: %s", plan_name)
        logging.info("Applying technique: %s", tech_function.nice_name)
        logging.debug("Calling technique with: %s, %s", doc, plan.get("args", {}))
        tech_function.apply(doc=doc, **plan.get("args", {}))


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
        doc.scrub()
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
    source: Dict[str, Any],
    post_process_registry: Dict[str, PostProcessBase],
):
    # loop through post-processors
    for post_processor_name in source.get("post-process", []):
        if not (post_processor := post_process_registry.get(post_processor_name)):
            logging.warn(
                'Skipping unknown post-processor "%s"',
                post_processor_name,
            )
            continue
        logging.info("Applying post-processor: %s", post_processor.nice_name)
        post_processor.apply(in_path=in_file, out_path=out_file)


def process(
    config: Dict[str, Any],
    tech_registry: dict[str, TechniqueBase],
    post_process_registry: dict[str, PostProcessBase],
    debug: bool = False,
    dry_run: bool = False,
) -> None:
    """Process the PDF files according to the configuration."""

    logging.debug(
        "%s sources found: %s", len(config["sources"]), ", ".join(config["sources"])
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir: Path = Path(temp_dir)
        # loop through sources
        for source_name, source in config["sources"].items():
            logging.info("Processing source: %s", source_name)
            in_path = Path(source["in_path"])
            out_path = Path(source["out_path"])
            out_suffix = source.get("out_suffix", "")
            if not verify_paths(in_path, out_path):
                logging.warn("Skipping source %s", source_name)
                continue
            # determine which publishers are in scope for this source
            publishers = select_publishers(source, config["publishers"])
            # recursively process the input path
            for in_file in in_path.glob("**/*.pdf"):
                logging.info("Processing file: %s", in_file)
                # calculate the output path for the file
                out_file = out_path / in_file.relative_to(in_path).with_stem(
                    in_file.stem + out_suffix
                )
                logging.info("Output file:     %s", out_file)
                # create the output directory if it doesn't exist
                out_file.parent.mkdir(parents=True, exist_ok=True)

                # if the out_file already exists and it's newer than the in_file, skip it
                if (
                    out_file.exists()
                    and out_file.stat().st_mtime > in_file.stat().st_mtime
                ):
                    logging.info("Output file is already up to date")
                    continue
                # Create a temporary file to save the output
                temp_out_file: Path = temp_dir / (str(uuid.uuid4()) + ".pdf")
                # process the file
                with fitz.open(in_file) as doc:
                    if not do_authentication(doc, publishers):
                        logging.warn("Skipping file since no password found")
                        continue
                    if not (publisher := choose_publisher(doc, publishers)):
                        logging.warn("Skipping file since no publisher found")
                        continue

                    apply_techniques(doc, config, publisher, tech_registry)

                    save_pdf(doc, temp_out_file, debug=debug)

                    apply_post_processing(
                        in_file, temp_out_file, source, post_process_registry
                    )

                    if dry_run:
                        logging.warn("Dry run: not saving file %s", out_file)
                        temp_out_file.unlink()
                    else:
                        logging.debug("Saving final output to %s", out_file)
                        temp_out_file.replace(out_file)
