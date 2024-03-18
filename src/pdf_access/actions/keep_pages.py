"""Action to keep only the specified pages."""

# Standard Python Libraries
from typing import Any, List, Tuple

# Third-Party Libraries
import fitz
from pydantic import BaseModel, ConfigDict, ValidationError

from .. import ActionBase


class KeepPagesActionArgs(BaseModel):
    """Arguments for the KeepPagesAction."""

    model_config = ConfigDict(extra="forbid")

    pages: List[int]


class KeepPagesAction(ActionBase):
    """Keep only the specified pages."""

    registry_id = "keep-pages"

    @classmethod
    def apply(cls, doc: fitz.Document, **kwargs: Any) -> Tuple[int, bool]:
        """Keep only the specified pages.

        Args:
            doc: The document to modify.
            **kwargs: The arguments for the action.

        Returns:
            A tuple containing the number of changes made and a boolean indicating if processing should continue.
        """
        try:
            args = KeepPagesActionArgs(**kwargs)
        except ValidationError as e:
            print(f"Error validating arguments: {e}")
            return (0, False)
        doc.select(args.pages)
        return (1, True)
