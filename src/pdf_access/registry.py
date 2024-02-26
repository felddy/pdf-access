"""Registry for discovering and registering classes in a module."""

# Standard Python Libraries
import importlib
from pathlib import Path
import pkgutil
from typing import Dict, Optional, Type, TypeVar

from . import Registrable

T = TypeVar("T", bound=Registrable)


def discover_and_register(
    module: str, clazz: Type[T], base_path: Optional[Path] = None
) -> Dict[str, Type[T]]:
    """Discover and register classes in a module."""
    registry: Dict[str, Type[T]] = {}
    # Path to the directory containing modules
    if base_path is None:
        base_path = Path(__file__).resolve().parent
    package_path = base_path / module.replace(".", "/")
    package_name = module

    # Discover and import modules
    for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
        full_module_name = f"{base_path.stem}.{package_name}.{module_name}"
        mod = importlib.import_module(full_module_name)

        # Iterate through everything defined in the module
        for name in dir(mod):
            obj = getattr(mod, name)
            # Check if it's a class and a subclass of clazz, but not clazz itself
            if isinstance(obj, type) and issubclass(obj, clazz) and obj is not clazz:
                # Use a class attribute or a method to get a registration key
                nice_name = obj.register()
                if nice_name:
                    if nice_name in registry:
                        raise ValueError(
                            f"Duplicate nice_name {nice_name} found in {module_name}"
                        )
                    registry[nice_name] = obj
                else:
                    raise ValueError(
                        f"Class {obj} does not define a nice_name attribute or register method"
                    )

    return registry
