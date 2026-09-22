"""The window's fonts and picture: copied out of the .sdkmod, because Unreal loads them from a file on disk.

Each file is copied once per game session. A failure hides the picture or keeps the engine font, and is
reported once: the window never shows a broken element (Kevin's rule, 2026-09-21).
"""

import os
from pathlib import Path

import unrealsdk

from . import panel_widgets as w, report

FONTS = ("Anton-Regular.ttf", "BarlowCondensed-Medium.ttf", "BarlowCondensed-SemiBold.ttf",
         "BarlowCondensed-ExtraBold.ttf")
AVATAR = "avatar.png"
NAMES = (*FONTS, AVATAR)
FOLDER = "apex_movement_ui"
# Each shipped file is under 200 kB; anything larger is not ours and is refused.
MAX_BYTES = 1_000_000
SIGNATURES = {".ttf": b"\x00\x01\x00\x00", ".png": b"\x89PNG\r\n\x1a\n"}

_copied = {}  # name -> path, or None after a failure; bounded by NAMES


def _read(name):
    from mods_base import open_in_mod_dir
    with open_in_mod_dir(Path(__file__).with_name("assets") / name, binary=True) as source:
        data = source.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES or not data.startswith(SIGNATURES[Path(name).suffix]):
        raise ValueError("Unexpected asset content")
    return data


def _write(target, data):
    if target.is_file() and target.stat().st_size == len(data) and target.read_bytes() == data:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    # Temporary file then rename: an interrupted copy never leaves a truncated font for Unreal to load.
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, target)


def path(name):
    if name not in NAMES:
        raise ValueError("Unknown window asset")
    if name not in _copied:
        try:
            from mods_base import SETTINGS_DIR
            target = Path(SETTINGS_DIR) / FOLDER / name
            _write(target, _read(name))
            _copied[name] = str(target)
        except (OSError, ValueError, ImportError) as error:
            report.error_once(f"panel:asset:{name}", f"Settings window file {name} unavailable ({type(error).__name__}).")
            _copied[name] = None
    return _copied[name]


def texture(world):
    """The avatar as a texture, or None: Unreal's own importer reads the PNG from the copied file."""
    file = path(AVATAR)
    if file is None:
        return None
    loaded = []

    def load():
        library = unrealsdk.find_class("KismetRenderingLibrary").ClassDefaultObject
        loaded.append(library.ImportFileAsTexture2D(world, file))

    w.cosmetic("avatar", load)
    return loaded[0] if loaded and loaded[0] is not None else None
