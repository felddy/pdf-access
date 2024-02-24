# Standard Python Libraries
from pathlib import Path
from typing import Tuple

# Third-Party Libraries
import fitz


class NiceBase:
    nice_name: str

    @classmethod
    def register(cls) -> str:
        return cls.nice_name


class PostProcessBase(NiceBase):
    # Subclasses should override this with their unique nice name
    nice_name: str

    @classmethod
    def apply(self, in_path: Path, out_path: Path, **kwargs):
        raise NotImplementedError(
            "Each post processor must implement the apply method."
        )


class ActionBase(NiceBase):
    # Subclasses should override this with their unique nice name
    nice_name: str

    @classmethod
    def apply(self, doc: fitz.Document, **kwargs) -> Tuple[int, bool]:
        # Return a tuple of the number of changes made, and whether processing should continue
        raise NotImplementedError("Each action must implement the apply method.")
