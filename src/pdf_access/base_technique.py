# Third-Party Libraries
import fitz


class TechniqueBase:
    # Subclasses should override this with their unique nice name
    nice_name: str = None

    @classmethod
    def apply(self, doc: fitz.Document, **kwargs):
        raise NotImplementedError("Each technique must implement the apply method.")

    @classmethod
    def register(cls) -> str:
        # Assuming subclasses have a 'nice_name'. This could also call a method.
        return cls.nice_name
