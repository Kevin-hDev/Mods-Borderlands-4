# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests and tools only: makes the mod's package importable without running its __init__.py, which needs mods_base
and the running game. Its modules import only the standard library and each other, by relative imports (since the
conflicts' readers, 2 November 2026); mods_base's objects and the game's come in as arguments."""

import sys
import types
from pathlib import Path

NAME = "logs_conflicts"
if NAME not in sys.modules:
    package = types.ModuleType(NAME)
    package.__path__ = [str(Path(__file__).resolve().parent / NAME)]
    sys.modules[NAME] = package
