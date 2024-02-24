# Standard Python Libraries
from typing import Tuple

# Third-Party Libraries
import fitz

from .. import ActionBase


class KeepPagesAction(ActionBase):
    """Keep only the specified pages."""

    nice_name = "keep-pages"

    @classmethod
    def apply(cls, doc: fitz.Document, pages: list[int]) -> Tuple[int, bool]:
        doc.select(pages)
        return (1, True)
