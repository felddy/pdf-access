# Third-Party Libraries
import fitz

from .. import TechniqueBase


class KeepPagesTechnique(TechniqueBase):
    nice_name = "keep-pages"

    @classmethod
    def apply(cls, doc: fitz.Document, pages: list[int]) -> int:
        doc.select(pages)
        return 1
