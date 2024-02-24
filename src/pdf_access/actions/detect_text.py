# Standard Python Libraries
import logging
import re
from typing import Tuple
import fitz

from .. import ActionBase


class DetectTextAction(ActionBase):
    nice_name = "detect-text"

    @classmethod
    def apply(
        cls,
        doc: fitz.Document,
        regex: str,
        stop_if_found: bool = False,
        stop_if_not_found: bool = False,
    ) -> Tuple[int, bool]:
        if not stop_if_found and not stop_if_not_found:
            logging.warning(
                'One of "stop_if_found" or "stop_if_not_found" should be set to "True"'
            )
            return (0, True)
        regex = re.compile(regex)
        found_text: bool = False
        for page in doc:
            text = page.get_text()
            if regex.search(text):
                if stop_if_found:
                    logging.warning("Text found on page %s", page.number + 1)
                found_text = True
        if found_text and stop_if_found:
            return (1, False)
        if not found_text and stop_if_not_found:
            logging.warning("Text not found")
            return (1, False)
        return (1, True)
