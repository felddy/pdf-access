# Standard Python Libraries
import logging
from typing import Any, Tuple

# Third-Party Libraries
import fitz
from pydantic import BaseModel, ValidationError

from .. import ActionBase


class ClearEncodingDifferencesActionArgs(BaseModel):
    # No fields
    class Config:
        extra = "forbid"


class ClearEncodingDifferencesAction(ActionBase):
    """Clear differences in encoding objects."""

    nice_name = "clear-encoding-differences"

    @classmethod
    def apply(cls, doc: fitz.Document, **kwargs: Any) -> Tuple[int, bool]:
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
