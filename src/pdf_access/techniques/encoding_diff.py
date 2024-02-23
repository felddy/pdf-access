# Standard Python Libraries
import logging

# Third-Party Libraries
import fitz

from .. import TechniqueBase


class ClearEncodingDifferencesTechnique(TechniqueBase):
    nice_name = "clear_encoding_differences"

    @classmethod
    def apply(cls, doc: fitz.Document):
        for xref_num in range(1, doc.xref_length()):
            stream_keys = doc.xref_get_keys(xref_num)
            if {"Differences", "BaseEncoding"} <= set(stream_keys):
                logging.debug("Clearing differences in object %s", xref_num)
                _, diffs = doc.xref_get_key(xref_num, "Differences")
                diff_count = len(diffs.split("/")) - 1
                doc.xref_set_key(
                    xref_num, "Differences", "[ 1" + " /space" * diff_count + "]"
                )
