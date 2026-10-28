# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests and tools only: puts the mod's package folder on the import path. Its modules take their collaborators as
arguments and import none of each other, so they load alone, without mods_base or the running game; the package's
__init__.py, which needs both, is never imported here."""

import sys
from pathlib import Path

PACKAGE = str(Path(__file__).resolve().parent / "mod_settings")
if PACKAGE not in sys.path:
    sys.path.insert(0, PACKAGE)
