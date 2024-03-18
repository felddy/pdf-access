"""Base classes for post-processors and actions."""

# Standard Python Libraries
from pathlib import Path
from typing import Any, Tuple

# Third-Party Libraries
import fitz


class Registrable:
    """Base class to allow registration of a class in a registry."""

    registry_id: str

    @classmethod
    def register(cls) -> str:
        """Register the class with the system."""
        return cls.registry_id


class PostProcessBase(Registrable):
    """Base class for post-processors."""

    @classmethod
    def apply(self, in_path: Path, out_path: Path) -> None:
        """Apply an post-processing to out_path possibly using the original document.

        Args:
            in_path: Path to the original document.
            out_path: Path to the modified document.
        """
        raise NotImplementedError(
            "Each post processor must implement the apply method."
        )


class ActionBase(Registrable):
    """Base class for actions."""

    @classmethod
    def apply(self, doc: fitz.Document, **kwargs: Any) -> Tuple[int, bool]:
        """Apply an action to a document.

        Args:
            doc: The document to modify.
            **kwargs: The arguments for the action.

        Returns:
            A tuple containing the number of changes made and a boolean indicating if processing should continue.
        """
        raise NotImplementedError("Each action must implement the apply method.")
