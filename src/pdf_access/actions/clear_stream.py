# Standard Python Libraries
from typing import Tuple
import re

# Third-Party Libraries
import fitz

from .. import ActionBase


class ClearStreamAction(ActionBase):
    nice_name = "clear-stream"

    @classmethod
    def apply(cls, doc: fitz.Document, regex: str) -> Tuple[int, bool]:
        regex = re.compile(regex.encode())
        change_count = 0
        for xref_num in range(1, doc.xref_length()):
            if not doc.xref_is_stream(xref_num):
                continue  # skip non-stream objects
            if regex.search(doc.xref_stream(xref_num)):
                change_count += 1
                doc.update_stream(xref_num, b"")
        return (change_count, True)
