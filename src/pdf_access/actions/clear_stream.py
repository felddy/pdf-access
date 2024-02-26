"""Action to clear stream objects matching a regular expression."""

# Standard Python Libraries
import re
from typing import Any, Tuple

# Third-Party Libraries
import fitz
from pydantic import BaseModel, ValidationError, field_validator

from .. import ActionBase


class ClearStreamActionArgs(BaseModel):
    """Arguments for the ClearStreamAction."""

    regex: re.Pattern

    @field_validator("regex", mode="before")
    def compile_path_regex(cls, value: Any) -> re.Pattern[bytes]:
        """Compile the regex pattern."""
        if isinstance(value, str):
            return re.compile(value.encode())
        elif isinstance(value, re.Pattern):
            return value
        else:
            # Handle other unexpected types, or raise an exception
            raise ValueError(
                "Unexpected type for 'regex'. Expected 'str' or compiled regex pattern."
            )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class ClearStreamAction(ActionBase):
    """Clear stream objects matching a regular expression."""

    registry_id = "clear-stream"

    @classmethod
    def apply(cls, doc: fitz.Document, **kwargs: Any) -> Tuple[int, bool]:
        """Clear stream objects matching a regular expression.

        Args:
            doc: The document to modify.
            **kwargs: The arguments for the action.

        Returns:
            A tuple containing the number of changes made and a boolean indicating if processing should continue.
        """
        try:
            args = ClearStreamActionArgs(**kwargs)
        except ValidationError as e:
            print(f"Error validating arguments: {e}")
            return (0, False)
        change_count = 0
        for xref_num in range(1, doc.xref_length()):
            if not doc.xref_is_stream(xref_num):
                continue  # skip non-stream objects
            if args.regex.search(doc.xref_stream(xref_num)):
                change_count += 1
                doc.update_stream(xref_num, b"")
        return (change_count, True)
