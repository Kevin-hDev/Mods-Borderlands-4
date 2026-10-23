"""It Follows' tests: the game's fakes are the characters' package's (characters/source/sdk_stubs.py, decision 69 of
docs/renforts), their one source. This file puts that folder on the path, gives its fakes under this name, and mounts
the package as it_follows.characters, where the built .sdkmod places it (outils/deploy_sdkmods.py, SHARED_PACKAGES).
"""

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
# The shared folder sits beside the mods: characters/source in the workshop, characters in the public copy.
SHARED = next((path for path in (_HERE.parent.parent / "characters" / "source", _HERE.parent / "characters")
               if path.is_dir()), _HERE.parent.parent / "characters" / "source")
if str(SHARED) not in sys.path:
    sys.path.insert(1, str(SHARED))
_spec = importlib.util.spec_from_file_location("characters_sdk_stubs", SHARED / "sdk_stubs.py")
_shared = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _shared
_spec.loader.exec_module(_shared)
globals().update({name: value for name, value in vars(_shared).items() if not name.startswith("__")})

import characters_fixture  # noqa: E402


def install(character=None) -> dict:
    """The shared fakes installed, then the package mounted as It Follows carries it."""
    state = _shared.install(character)
    characters_fixture.mount("it_follows")
    return state
