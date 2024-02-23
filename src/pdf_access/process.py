# Standard Python Libraries
import logging
from pathlib import Path
import re
from typing import Any, Dict

# Third-Party Libraries
import fitz

from . import PostProcessBase, TechniqueBase


def do_authentication(doc: fitz.Document, publishers: Dict[str, Any]) -> bool:
    """Attempt to authenticate the document using the passwords for the publishers."""
    for publisher_name, publisher in publishers.items():
        passwords = publisher.get("passwords", [])
        for password in passwords:
            logging.debug("Attempting password for %s", publisher_name)
            if doc.authenticate(password):
                logging.info("Authenticated with password for %s", publisher_name)
                return True
    return False


def select_publishers(source: Dict[str, Any], publishers: Dict[str, Any]) -> list[str]:
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


def choose_publisher(doc: fitz.Document, publishers: Dict[str, Any]) -> Dict[str, Any]:
    """Check the metadata to determine the publisher of the document."""
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


def save_pdf(
    doc: fitz.Document, out_file: Path, debug: bool = False, dry_run: bool = False
) -> None:
    """Save the document to the output file."""
    if dry_run:
        logging.warn("Dry run: not saving file")
        return

    if debug:
        logging.warn("Saving unoptimized (debug) file to %s", out_file)
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
        logging.info("Saving optimized file to %s", out_file)
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
    # loop through sources
    for source_name, source in config["sources"].items():
        logging.info("Processing source: %s", source_name)
        in_path = Path(source["in_path"])
        out_path = Path(source["out_path"])
        out_suffix = source.get("out_suffix", "")
        # verify that both paths exist
        if not in_path.exists():
            logging.error("Input path does not exist: %s", in_path)
            continue
        if not out_path.exists():
            logging.error("Output path does not exist: %s", out_path)
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
            if out_file.exists() and out_file.stat().st_mtime > in_file.stat().st_mtime:
                logging.info("Output file is already up to date")
                continue
            # process the file
            with fitz.open(in_file) as doc:
                if doc.is_encrypted:
                    logging.info("Password required for %s", in_file)
                    if not do_authentication(doc, publishers):
                        logging.warn("Skipping file since no password found")
                        continue
                # Check metadata to determine publisher
                logging.debug("Metadata: %s", doc.metadata)
                if not (publisher := choose_publisher(doc, publishers)):
                    logging.warn("Skipping file since no publisher found")
                    continue

                # Get the list of rules for this publisher
                rule_names = publisher.get("rules", [])
                for rule_name in rule_names:
                    if not (rule := config["rules"].get(rule_name)):
                        logging.warn('Skipping unknown rule "%s"', rule_name)
                        continue
                    if not (tech_function := tech_registry.get(rule["technique"])):
                        logging.warn('Skipping unknown technique "%s"', rule)
                        continue
                    logging.info("Applying technique: %s", tech_function.nice_name)
                    logging.debug(
                        "Calling technique with: %s, %s", doc, rule.get("args", {})
                    )
                    tech_function.apply(doc=doc, **rule.get("args", {}))

                if not dry_run:
                    save_pdf(doc, out_file, debug=debug, dry_run=dry_run)
                    # loop through post-processors
                    for post_processor_name in source.get("post-process", []):
                        if not (
                            post_processor := post_process_registry.get(
                                post_processor_name
                            )
                        ):
                            logging.warn(
                                'Skipping unknown post-processor "%s"',
                                post_processor_name,
                            )
                            continue
                        logging.info(
                            "Applying post-processor: %s", post_processor.nice_name
                        )
                        post_processor.apply(in_path=in_file, out_path=out_file)
