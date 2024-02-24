# Standard Python Libraries
import logging
from typing import Tuple

# Third-Party Libraries
import fitz

from .. import ActionBase


class ClearEncodingDifferencesAction(ActionBase):
    nice_name = "clear_encoding_differences"

    @classmethod
    def apply(cls, doc: fitz.Document) -> Tuple[int, bool]:
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
