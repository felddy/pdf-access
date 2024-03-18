"""Action to delete the ID entry in the file trailer dictionary."""

# Standard Python Libraries
import logging
from typing import Any, Tuple

# Third-Party Libraries
import fitz
from pydantic import BaseModel, ConfigDict, ValidationError

from .. import ActionBase

PDF_TRAILER_XREF = -1


class DeleteTrailerIDActionArgs(BaseModel):
    """Arguments for the ClearEncodingDifferencesAction."""

    model_config = ConfigDict(extra="forbid")

    # No arguments are needed for this action.


class DeleteTrailerIDAction(ActionBase):
    """Clear differences in encoding objects."""

    registry_id = "delete-trailer-id"

    @classmethod
    def apply(cls, doc: fitz.Document, **kwargs: Any) -> Tuple[int, bool]:
        """Delete the ID entry in the file trailer dictionary if present.

        Args:
            doc: The document to modify.
            **kwargs: The arguments for the action.

        Returns:
            A tuple containing the number of changes made and a boolean indicating if processing should continue.
        """
        try:
            DeleteTrailerIDActionArgs(**kwargs)
        except ValidationError as e:
            logging.error("Error validating arguments: %s", e)
            return (0, False)
        change_count = 0
        trailer_keys = doc.xref_get_keys(PDF_TRAILER_XREF)
        if "ID" in trailer_keys:
            logging.debug(
                "Deleting ID entry in file trailer dictionary: %s",
                doc.xref_get_key(PDF_TRAILER_XREF, "ID"),
            )
            doc.xref_set_key(PDF_TRAILER_XREF, "ID", "null")
            change_count += 1
        return (change_count, True)
