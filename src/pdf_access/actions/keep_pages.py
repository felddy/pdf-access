# Third-Party Libraries
import fitz
from typing import Tuple

from .. import ActionBase


class KeepPagesAction(ActionBase):
    nice_name = "keep-pages"

    @classmethod
    def apply(cls, doc: fitz.Document, pages: list[int]) -> Tuple[int, bool]:
        doc.select(pages)
        return (1, True)
