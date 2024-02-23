# Standard Python Libraries
import importlib
from pathlib import Path
import pkgutil

# Project Libraries
from pdf_access import TechniqueBase

base_package_name = "pdf_access.techniques"


def discover_and_register_techniques() -> dict[str, TechniqueBase]:
    technique_registry = {}

    # Use the base package name directly for discovering modules
    for _, module_name, _ in pkgutil.iter_modules(
        [str(Path(__file__).parent / "techniques")]
    ):
        # Full module name includes the base package name
        full_module_name = f"{base_package_name}.{module_name}"
        module = importlib.import_module(full_module_name)

        # Iterate through everything defined in the module
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, TechniqueBase)
                and obj is not TechniqueBase
            ):
                # Found a subclass of TechniqueBase
                nice_name = obj.register()
                if nice_name:
                    technique_registry[nice_name] = obj

    return technique_registry
