"""Action to delete PieceInfo dictionaries objects."""

# Standard Python Libraries
import logging
from typing import Any, Tuple

# Third-Party Libraries
import fitz
from pydantic import BaseModel, ConfigDict, ValidationError

from .. import ActionBase


class DeletePieceInfoActionArgs(BaseModel):
    """Arguments for the ClearEncodingDifferencesAction."""

    model_config = ConfigDict(extra="forbid")

    # No arguments are needed for this action.


class DeletePieceInfoAction(ActionBase):
    """Delete PieceInfo dictionaries."""

    registry_id = "delete-piece-info"

    @classmethod
    def apply(cls, doc: fitz.Document, **kwargs: Any) -> Tuple[int, bool]:
        """Delete PieceInfo dictionaries.

        Args:
            doc: The document to modify.
            **kwargs: The arguments for the action.

        Returns:
            A tuple containing the number of changes made and a boolean indicating if processing should continue.
        """
        try:
            DeletePieceInfoActionArgs(**kwargs)
        except ValidationError as e:
            logging.error("Error validating arguments: %s", e)
            return (0, False)
        change_count = 0
        for xref_num in range(1, doc.xref_length()):
            obj_keys = doc.xref_get_keys(xref_num)
            if "PieceInfo" in obj_keys:
                logging.debug("Deleting PieceInfo dictionary in object %s", xref_num)
                change_count += 1
                doc.xref_set_key(xref_num, "PieceInfo", "null")
        return (change_count, True)
