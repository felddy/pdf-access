# Third-Party Libraries
import fitz

from .. import ActionBase


class KeepPagesAction(ActionBase):
    nice_name = "keep-pages"

    @classmethod
    def apply(cls, doc: fitz.Document, pages: list[int]) -> int:
        doc.select(pages)
        return 1
