"""Action to clear differences in encoding objects."""

# Standard Python Libraries
import logging
from typing import Any, Tuple

# Third-Party Libraries
import fitz
from pydantic import BaseModel, ConfigDict, ValidationError

from .. import ActionBase


class ClearEncodingDifferencesActionArgs(BaseModel):
    """Arguments for the ClearEncodingDifferencesAction."""

    model_config = ConfigDict(extra="forbid")

    # No arguments are needed for this action.


class ClearEncodingDifferencesAction(ActionBase):
    """Clear differences in encoding objects."""

    registry_id = "clear-encoding-differences"

    @classmethod
    def apply(cls, doc: fitz.Document, **kwargs: Any) -> Tuple[int, bool]:
        """Clear differences in encoding objects.

        Args:
            doc: The document to modify.
            **kwargs: The arguments for the action.

        Returns:
            A tuple containing the number of changes made and a boolean indicating if processing should continue.
        """
        try:
            ClearEncodingDifferencesActionArgs(**kwargs)
        except ValidationError as e:
            print(f"Error validating arguments: {e}")
            return (0, False)
        change_count = 0
        for xref_num in range(1, doc.xref_length()):
            stream_keys = doc.xref_get_keys(xref_num)
            if {"Differences", "BaseEncoding"} <= set(stream_keys):
                logging.debug("Clearing differences in object %s", xref_num)
                change_count += 1
                _, diffs = doc.xref_get_key(xref_num, "Differences")
                diff_count = len(diffs.split("/")) - 1
                doc.xref_set_key(
                    xref_num, "Differences", "[ 1" + " /space" * diff_count + "]"
                )
        return (change_count, True)
