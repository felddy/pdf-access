# Standard Python Libraries
import logging
import re

# Third-Party Libraries
import fitz

from .. import ActionBase


class GatedRegexAction(ActionBase):
    nice_name = "gated-regex"

    @classmethod
    def apply(cls, doc: fitz.Document, gate_re: str, clear_res: list[str]) -> None:
        change_count = 0
        gate_re = re.compile(gate_re.encode())
        clear_res = [re.compile(r.encode()) for r in clear_res]

        logging.debug("Gate regex: %s", gate_re.pattern)
        logging.debug("Clear regexes: %s", [r.pattern for r in clear_res])

        for xref_num in range(1, doc.xref_length()):
            if not doc.xref_is_stream(xref_num):
                continue  # skip non-stream objects
            if gate_re.search(doc.xref_stream(xref_num)):
                # replace all instances of the regex with an empty print statement
                new_stream = doc.xref_stream(xref_num)
                for regex in clear_res:
                    new_stream, subs_made = re.subn(regex, b"() Tj", new_stream)
                    change_count += subs_made
                doc.update_stream(xref_num, new_stream)
        return change_count
