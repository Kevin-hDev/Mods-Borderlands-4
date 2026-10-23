"""Which copy of the characters' package a test reads (decision 69 of docs/renforts): this folder's own, `characters`,
when its tests run; the one a mod carries, mounted as `<mod>.characters` where the built .sdkmod places it, when that
mod's tests run (its sdk_stubs.py calls mount). The shared fakes take the package's modules through part(), so that
they and the code under test hold one module, never two copies of it with two states."""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

SOURCE = Path(__file__).resolve().parent / "characters"
_package = {"name": "characters"}


def mount(mod: str) -> str:
    """The package mounted under that mod's package, once; part() reads it from then on. Its name. A test imports the
    mod's package before any module of this one, as the game does: a module of this one imported first had Python
    load the mod's package in the middle of it (test_companion_pictures_build.py, 23 October 2026)."""
    name = f"{mod}.characters"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, SOURCE / "__init__.py",
                                                      submodule_search_locations=[str(SOURCE)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    _package["name"] = name
    return name


def part(name: str) -> Any:
    """The package's module of that name (reads, companions.follow…), in the copy the test reads."""
    return importlib.import_module(f"{_package['name']}.{name}")
