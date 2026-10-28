"""Load packaged UI modules in isolation without bootstrapping the game's mod registration."""

import importlib
from pathlib import Path
import sys
from types import ModuleType

PACKAGE = "_grapple_ui_test"


def load(name):
    if PACKAGE not in sys.modules:
        package = ModuleType(PACKAGE)
        package.__path__ = [str(Path(__file__).with_name("apex_grapple"))]
        sys.modules[PACKAGE] = package
    return importlib.import_module(f"{PACKAGE}.{name}")
