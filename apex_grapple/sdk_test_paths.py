"""Optional installed SDK input for integration tests; no machine-specific checkout paths."""

import os
from pathlib import Path


def console_menu_archive():
    folder = os.environ.get("BL4_SDK_MODS")
    if not folder:
        print("SKIP | set BL4_SDK_MODS to run this test against the installed console menu")
        raise SystemExit(0)
    path = Path(folder).expanduser() / "console_mod_menu.sdkmod"
    if not path.is_file():
        raise RuntimeError("BL4_SDK_MODS must contain console_mod_menu.sdkmod")
    return path
