"""PDF Access Python library and tool.
"""

# Standard Python Libraries
import argparse
import logging
import os
import pprint
import sys
import tomllib
from typing import Any, Dict

from . import PostProcessBase, TechniqueBase, discover_and_register, process
from ._version import __version__


def read_config(config_file: str) -> Dict[str, Any]:
    """Read the configuration file and return its contents as a dictionary."""
    if not os.path.isfile(config_file):
        logging.error("Config file not found: %s", config_file)
        sys.exit(1)

    try:
        logging.debug("Reading config file: %s", config_file)
        with open(config_file, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logging.error("Error parsing config file: %s", e)
        sys.exit(1)


def main() -> None:
    """Set up logging and call the process function."""
    parser = argparse.ArgumentParser(
        description="Processes PDF files to improve their accessibility"
    )
    parser.add_argument(
        "config_file",
        help="path to the configuration file",
        metavar="config-file",
        type=str,
    )
    parser.add_argument(
        "--debug", "-D", help="save unoptimized pdfs", action="store_true"
    )
    parser.add_argument(
        "--dry-run", "-d", help="do not modify files", action="store_true"
    )
    parser.add_argument(
        "--log-level",
        "-l",
        help="set the logging level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        help="increase verbosity (shortcut for --log-level debug)",
        action="store_true",
    )

    args = parser.parse_args()

    if args.verbose:
        args.log_level = "debug"

    # Set up logging
    logging.basicConfig(
        format="%(asctime)-15s %(levelname)s %(message)s", level=args.log_level.upper()
    )
    pp = pprint.PrettyPrinter(indent=4)

    if args.dry_run:
        logging.warn("Dry run: no files will be modified")

    # Read the configuration file
    config = read_config(args.config_file)
    logging.debug("Configuration:\n%s", pp.pformat(config))
    # TODO verify the configuration schema

    # Discover and register the techniques
    tech_registry: dict[str, TechniqueBase] = discover_and_register(
        "techniques", TechniqueBase
    )
    logging.debug("Techniques:\n%s", pp.pformat(tech_registry))

    # Discover and register the post-processors
    post_process_registry: dict[str, PostProcessBase] = discover_and_register(
        "post_process", PostProcessBase
    )
    logging.debug("Post-processors:\n%s", pp.pformat(post_process_registry))

    # Process the PDF files
    process(
        config,
        tech_registry,
        post_process_registry,
        debug=args.debug,
        dry_run=args.dry_run,
    )

    # Stop logging and clean up
    logging.shutdown()
