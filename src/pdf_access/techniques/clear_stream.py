# Standard Python Libraries
import logging
import re

# Third-Party Libraries
import fitz

from .. import TechniqueBase


class ClearStreamTechnique(TechniqueBase):
    nice_name = "clear-stream"

    @classmethod
    def apply(cls, doc: fitz.Document, regex: str):
        regex = re.compile(regex.encode())

        logging.debug("Detect regex: %s", regex.pattern)

        for xref_num in range(1, doc.xref_length()):
            if not doc.xref_is_stream(xref_num):
                continue  # skip non-stream objects
            if regex.search(doc.xref_stream(xref_num)):
                # check to see if debug logging is enabled
                doc.update_stream(xref_num, b"")
