"""Process PDF files according to a configuration."""

# Standard Python Libraries
import logging
from pathlib import Path
import re
import tempfile
from typing import Dict, Optional
import uuid

# Third-Party Libraries
import fitz
import humanize
from rich.progress import MofNCompleteColumn, Progress, SpinnerColumn

from . import ActionBase, Config, Plan, PostProcessBase, Source


def verify_paths(in_path: Path, out_path: Path) -> bool:
    """Verify that the input and output paths exist."""
    if not in_path.exists():
        logging.error("Input path does not exist: %s", in_path)
        return False
    if not out_path.exists():
        logging.error("Output path does not exist: %s", out_path)
        return False
    return True


def do_authentication(doc: fitz.Document, plans: Dict[str, Plan]) -> bool:
    """Attempt to authenticate the document using the passwords for the plans."""
    if not doc.is_encrypted:
        logging.debug("Document is not encrypted")
        return True
    logging.info("Password required. Attempting to authenticate")

    for plan_name, plan in plans.items():
        for password in plan.passwords:
            logging.debug("Attempting password for %s", plan_name)
            if doc.authenticate(password):
                logging.info("Authenticated with password for %s", plan_name)
                return True
    return False


def select_plans_for_source(source: Source, plans: Dict[str, Plan]) -> Dict[str, Plan]:
    """Select the plans that are in scope for this source."""
    # If the source defines plans, use them; otherwise, use all
    if len(source.plans) == 0:
        logging.debug("All plans are in scope for this source")
        return plans
    # select the plans that are in scope for this source
    selected_plans = {key: value for key, value in plans.items() if key in source.plans}
    logging.debug("Plans in scope for this source: %s", ", ".join(selected_plans))
    return selected_plans


def select_plan_for_doc(doc: fitz.Document, plans: Dict[str, Plan]) -> Optional[Plan]:
    """Check the metadata to determine the plan of the document."""
    logging.debug("Metadata: %s", doc.metadata)
    for plan_name, plan in plans.items():
        matches_failed = False
        logging.debug('Evaluating plan: "%s"', plan_name)
        # Check to see if filename matches the path_regex
        if not re.search(plan.path_regex, doc.name):
            logging.debug(
                'Path regex "%s" does not match: "%s"',
                plan.path_regex.pattern,
                doc.name,
            )
            matches_failed = True
            continue
        else:
            logging.debug(
                'Path regex "%s" matches: "%s"', plan.path_regex.pattern, doc.name
            )
        for field, regex in plan.metadata_search.items():
            if matches_failed:
                logging.debug('Search failure occurred, skipping plan: "%s"', plan_name)
                break
            logging.debug('Searching field "%s" for regex "%s"', field, regex.pattern)
            if field not in doc.metadata:
                logging.debug('Metadata field not found: "%s"', field)
                matches_failed = True
                continue
            if not regex.search(doc.metadata[field]):
                logging.debug(
                    'Metadata regex "%s" does not match: {"%s": "%s"}',
                    regex.pattern,
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
            logging.debug("All metadata regexes matched.")
            logging.info('Selected plan: "%s"', plan_name)
            if plan.comment:
                logging.info('Plan comment: "%s"', plan.comment)
            return plan
    logging.debug("No plans matched")
    return None


def apply_actions(
    doc: fitz.Document,
    plan: Plan,
    action_registry: dict[str, type[ActionBase]],
) -> bool:
    """Apply the actions from the plan to the document.

    Args:
        doc: The document to modify.
        plan: The plan to apply.
        action_registry: The registry of actions.

    Returns:
        True processing should continue.
        False if processing should stop.
    """
    # Get the list of actions for this plan
    for action in plan.actions:
        if not (action_function := action_registry.get(action.function)):
            logging.warn(
                'Skipping action function not found in registry "%s"', action.function
            )
            continue
        logging.info('Running action: "%s"', action.name)
        logging.debug(
            'Calling action "%s" with: %s, %s',
            action_function.registry_id,
            doc,
            action.args,
        )
        (change_count, should_continue) = action_function.apply(doc=doc, **action.args)
        if not should_continue:
            logging.warn('Action "%s" prevented additional processing', action.name)
            return False
        if change_count:
            logging.debug("Changes made: %s", change_count)
        else:
            logging.warn("No changes made")
    return True


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
        # TODO move scrub to action
        doc.scrub(
            attached_files=True,
            clean_pages=True,
            embedded_files=True,
            hidden_text=True,
            javascript=True,
            metadata=False,
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
            clean=True,
            deflate_fonts=True,
            deflate_images=True,
            deflate=True,
            garbage=4,
            linear=True,
        )


def apply_post_processing(
    in_file: Path,
    out_file: Path,
    plan: Plan,
    post_process_registry: Dict[str, type[PostProcessBase]],
):
    """Apply the post-processing to the output file.

    Args:
        in_file: The input file.
        out_file: The output file.
        plan: The plan that was applied.
        post_process_registry: The registry of post-processors.

    """
    # loop through post-processors
    for post_processor_name in plan.post_process:
        if not (post_processor := post_process_registry.get(post_processor_name)):
            logging.warn(
                'Skipping unknown post-processor "%s"',
                post_processor_name,
            )
            continue
        logging.info('Applying post-processor: "%s"', post_processor.registry_id)
        post_processor.apply(in_path=in_file, out_path=out_file)


def size_report(in_path: Path, out_path: Path):
    """Report the change in size of the files."""
    in_size = in_path.stat().st_size
    out_size = out_path.stat().st_size
    percent = (out_size - in_size) / in_size * 100.0
    log_function = logging.info if percent < 0 else logging.warn
    log_function(
        "Size change: %s -> %s (%s) %.2f%%",
        humanize.naturalsize(in_size, binary=True),
        humanize.naturalsize(out_size, binary=True),
        humanize.naturalsize(out_size - in_size, binary=True),
        percent,
    )


def process(
    config: Config,
    action_registry: dict[str, type[ActionBase]],
    post_process_registry: dict[str, type[PostProcessBase]],
    debug: bool = False,
    dry_run: bool = False,
    force: bool = False,
) -> None:
    """Process the PDF files according to the configuration."""
    logging.debug(
        "%s source%s found: %s",
        len(config.sources),
        "s" if len(config.sources) != 1 else "",
        ",".join(config.sources),
    )
    if force:
        logging.warn("Force mode is enabled.  Timestamps will be ignored.")
    with tempfile.TemporaryDirectory() as temp_dir_context:
        temp_dir: Path = Path(temp_dir_context)
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
                logging.info('Processing source: "%s"', source_name)
                logging.info('Input path:   "%s"', source.in_path)
                logging.info('Output path:  "%s"', source.out_path)
                in_path = Path(source.in_path)
                out_path = Path(source.out_path)
                out_suffix = source.out_suffix
                if not verify_paths(in_path, out_path):
                    logging.warn('Skipping source "%s"', source_name)
                    if source_task:
                        progress.update(source_task, advance=1)
                    continue
                # determine which plans are in scope for this source
                plans = select_plans_for_source(source, config.plans)
                # recursively process the input path
                in_files = list(in_path.glob("**/*.pdf"))
                files_task = progress.add_task(
                    "Files",
                    total=len(in_files),
                )
                for in_file in in_files:
                    logging.debug('Evaluating file: "%s"', in_file)
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
                    logging.info('Processing file: "%s"', in_file)
                    logging.info('Output file:     "%s"', out_file)
                    # Create a temporary file to save the output
                    temp_out_file: Path = temp_dir / (str(uuid.uuid4()) + ".pdf")
                    # process the file
                    with fitz.open(in_file) as doc:
                        if not do_authentication(doc, plans):
                            logging.warn("Skipping file since no password found")
                            progress.update(files_task, advance=1)
                            continue
                        if not (plan := select_plan_for_doc(doc, plans)):
                            logging.warn("Skipping file since no plan found")
                            progress.update(files_task, advance=1)
                            continue
                        if not apply_actions(doc, plan, action_registry):
                            logging.warn("Skipping file since an action failed")
                            progress.update(files_task, advance=1)
                            continue
                        save_pdf(doc, temp_out_file, debug=debug)

                        apply_post_processing(
                            in_file, temp_out_file, plan, post_process_registry
                        )

                        size_report(in_file, temp_out_file)

                        if dry_run:
                            logging.info('Dry run: not saving file "%s"', out_file)
                            temp_out_file.unlink()
                        else:
                            logging.debug('Saving final output to "%s"', out_file)
                            # create the output directory if it doesn't exist
                            out_file.parent.mkdir(parents=True, exist_ok=True)
                            temp_out_file.replace(out_file)
                    progress.update(files_task, advance=1)
                progress.remove_task(files_task)
                if source_task:
                    progress.update(source_task, advance=1)
