"""PDF Access Python library and tool.
"""

# Standard Python Libraries
import argparse
import logging
import os
import pprint
import sys
import tomllib

# Third-Party Libraries
from pydantic import ValidationError
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.traceback import install as traceback_install

from . import ActionBase, Config, PostProcessBase, discover_and_register, process
from ._version import __version__


def read_config(config_file: str) -> Config:
    """Read the configuration file and return its contents as a dictionary."""
    pp = pprint.PrettyPrinter(indent=4)

    if not os.path.isfile(config_file):
        logging.error("Config file not found: %s", config_file)
        sys.exit(1)

    try:
        logging.debug("Reading config file: %s", config_file)
        with open(config_file, "rb") as f:
            config_dict = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logging.error("Error decoding toml file: %s", e)
        sys.exit(1)

    try:
        config = Config(**config_dict)
        logging.debug("Parsed configuration:\n%s", pp.pformat(config.dict()))
        return config
    except ValidationError as e:
        logging.error(e)
        sys.exit(1)


def get_registries():
    # Discover and register the actions
    action_registry: dict[str, type[ActionBase]] = discover_and_register(
        "actions", ActionBase
    )
    logging.debug("Techniques: %s", action_registry.keys())

    # Discover and register the post-processors
    post_process_registry: dict[str, type[PostProcessBase]] = discover_and_register(
        "post_process", PostProcessBase
    )
    logging.debug("Post-processors: %s", post_process_registry.keys())
    return action_registry, post_process_registry


class PrintConfTable(argparse.Action):
    def __init__(self, option_strings, dest, nargs=0, **kwargs):
        super().__init__(option_strings, dest, nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        console = Console()
        action_registry, post_process_registry = get_registries()

        # Table for Actions
        action_table = Table(
            show_header=True, header_style="bold magenta", row_styles=["none", "dim"]
        )
        action_table.add_column("Action")
        action_table.add_column("Description")

        for k, v in action_registry.items():
            action_table.add_row(k, v.__doc__ or "No description available")

        console.print(action_table)

        # Table for Post-processors
        post_processor_table = Table(
            show_header=True, header_style="bold magenta", row_styles=["none", "dim"]
        )
        post_processor_table.add_column("Post-Processor")
        post_processor_table.add_column("Description")

        for k, v in post_process_registry.items():
            post_processor_table.add_row(k, v.__doc__ or "No description available")

        console.print(post_processor_table)
        parser.exit()


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
        "--force", "-f", help="ignore existing file timestamps", action="store_true"
    )
    parser.add_argument(
        "--log-level",
        "-l",
        help="set the logging level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
    )
    parser.add_argument(
        "--show-ids",
        "-s",
        help="display action and post-process id tables and exit.",
        action=PrintConfTable,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        help="increase verbosity (shortcut for --log-level debug)",
        action="store_true",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    args = parser.parse_args()

    if args.verbose:
        args.log_level = "debug"

    # Set up logging
    logging.basicConfig(
        format="%(message)s",
        # datefmt="%Y-%m-%d %H:%M:%S",
        level=args.log_level.upper(),
        handlers=[
            RichHandler(rich_tracebacks=True, show_path=args.log_level == "debug")
        ],
    )

    # Set up tracebacks
    traceback_install(show_locals=True)

    if args.dry_run:
        logging.warn("Dry run: no files will be modified")

    # Read the configuration file
    config = read_config(args.config_file)

    action_registry, post_process_registry = get_registries()

    # Process the PDF files
    process(
        config,
        action_registry,
        post_process_registry,
        debug=args.debug,
        dry_run=args.dry_run,
        force=args.force,
    )

    # Stop logging and clean up
    logging.shutdown()
