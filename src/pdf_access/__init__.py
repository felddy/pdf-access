"""The pdf access library."""

# We disable a Flake8 check for "Module imported but unused (F401)" here because
# although this import is not directly used, it populates the value
# package_name.__version__, which is used to get version information about this
# Python package.

from ._version import __version__  # noqa: F401
from .bases import ActionBase, PostProcessBase, Registrable
from .config_model import Action, Config, Plan, Source
from .process import process
from .registry import discover_and_register

# Must be imported last to avoid circular imports
from . import pdf_access  # isort:skip

__all__ = [
    "Action",
    "ActionBase",
    "Config",
    "discover_and_register",
    "pdf_access",
    "Plan",
    "PostProcessBase",
    "process",
    "Registrable",
    "Source",
]
