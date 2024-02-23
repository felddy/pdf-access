# Standard Python Libraries
import logging
import re

# Third-Party Libraries
import fitz

from .. import TechniqueBase


class GatedRegexTechnique(TechniqueBase):
    nice_name = "gated-regex"

    @classmethod
    def apply(cls, doc: fitz.Document, gate_re: str, clear_res: list[str]):
        gate_re = re.compile(gate_re.encode())
        clear_res = [re.compile(r.encode()) for r in clear_res]

        logging.debug("Gate regex: %s", gate_re.pattern)
        logging.debug("Clear regexes: %s", [r.pattern for r in clear_res])

        for xref_num in range(1, doc.xref_length()):
            if not doc.xref_is_stream(xref_num):
                continue  # skip non-stream objects
            if gate_re.search(doc.xref_stream(xref_num)):
                # check to see if debug logging is enabled
                if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                    logging.debug("Found watermark in object %s", xref_num)
                # replace all instances of the regex with an empty print statement
                new_stream = doc.xref_stream(xref_num)
                for regex in clear_res:
                    new_stream = re.sub(regex, b"() Tj", new_stream)
                doc.update_stream(xref_num, new_stream)
