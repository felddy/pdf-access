"""Action to detect text in pages and metadata matching a regular expression."""

# Standard Python Libraries
import logging
import re
from typing import Any, Dict, Tuple

# Third-Party Libraries
import fitz
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    field_validator,
    model_validator,
)

from .. import ActionBase


class DetectTextActionArgs(BaseModel):
    """Arguments for the DetectTextAction."""

    model_config = ConfigDict(extra="forbid")

    regex: re.Pattern
    stop_if_found: bool = False
    stop_if_not_found: bool = False

    @field_validator("regex", mode="before")
    def compile_path_regex(cls, value: Any) -> re.Pattern[str]:
        """Compile the regex pattern."""
        if isinstance(value, str):
            return re.compile(value)
        elif isinstance(value, re.Pattern):
            return value
        else:
            # Handle other unexpected types, or raise an exception
            raise ValueError(
                "Unexpected type for 'regex'. Expected 'str' or compiled regex pattern."
            )

    @model_validator(mode="before")
    def check_bools(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Check that at least one of 'stop_if_found' or 'stop_if_not_found' is True."""
        if not values.get("stop_if_found") and not values.get("stop_if_not_found"):
            raise ValueError(
                "At least one of 'stop_if_found' or 'stop_if_not_found' must be True"
            )
        return values


class DetectTextAction(ActionBase):
    """Detect text in pages and metadata matching a regular expression."""

    registry_id = "detect-text"

    @classmethod
    def apply(cls, doc: fitz.Document, **kwargs: Any) -> Tuple[int, bool]:
        """Detect text in pages and metadata matching a regular expression.

        Args:
            doc: The document to modify.
            **kwargs: The arguments for the action.

        Returns:
            A tuple containing the number of changes made and a boolean indicating if processing should continue.
        """
        try:
            args = DetectTextActionArgs(**kwargs)
        except ValidationError as e:
            print(f"Error validating arguments: {e}")
            return (0, False)
        found_text: bool = False
        # Search text on pages
        for page in doc:
            text = page.get_text()
            if args.regex.search(text):
                if args.stop_if_found:
                    logging.warning("Text found on page %s", page.number + 1)
                found_text = True
        # Search text in metadata
        for key, value in doc.metadata.items():
            if not value:
                continue
            if args.regex.search(value):
                if args.stop_if_found:
                    logging.warning('Text found in metadata key: "%s"', key)
                found_text = True
        if found_text and args.stop_if_found:
            return (1, False)
        if not found_text and args.stop_if_not_found:
            logging.warning("Text not found")
            return (1, False)
        return (1, True)
