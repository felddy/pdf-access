# Standard Python Libraries
import re
from typing import Any, List, Tuple

# Third-Party Libraries
import fitz
from pydantic import BaseModel, ValidationError, field_validator, model_validator

from .. import ActionBase


class KeepPagesActionArgs(BaseModel):
    pages: List[int]

    class Config:
        extra = "forbid"


class KeepPagesAction(ActionBase):
    """Keep only the specified pages."""

    nice_name = "keep-pages"

    @classmethod
    def apply(cls, doc: fitz.Document, **kwargs: Any) -> Tuple[int, bool]:
        try:
            args = KeepPagesActionArgs(**kwargs)
        except ValidationError as e:
            print(f"Error validating arguments: {e}")
            return (0, False)
        doc.select(args.pages)
        return (1, True)
