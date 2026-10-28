# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Copies of the game's own UI files for the browser test: the pieces' scripts and markup, read from the game's paks by
the game_files reader, kept in build/test_game_ui/ (never committed: Gearbox's files). The test then runs the
game's code, not a stand-in (a stand-in once hid a fault the game showed, trial 2).

copies(refresh) -> {file name: path}; refresh=True reads the paks again (after a game update). available() says
whether they can be had at all: the reader lives in the private workshop only, not in the public copy."""

import shutil
import subprocess
from pathlib import Path

from game_tools import GAME_FILES, GAME_FILES_TIMEOUT_S

HERE = Path(__file__).resolve().parent
CACHE = HERE / "build" / "test_game_ui"
ROOT = "OakGame/Content/uiresources/"
# The reader takes 16 paths a call.
CALL_SIZE = 16
FILES = (
    "_shared/js/custom_elements.js", "_shared/js/cursorhandler.js",
    "_shared/js/glyph_manager.js", "_shared/js/glyph_element.js", "Glyphs/js/glyph_map_keyboard_mouse.js",
    # The scrollbar and the focus-scroll the page borrows (scroll.js); the test's InputMgr reaches the game's
    # own InputManager.DirectionalNavigationItemFocusHelper.
    "_shared/js/oakscroll.js", "_shared/js/input_manager.js",
    "components/slider/js/slider.js", "components/toggle/js/toggle.js", "components/stepper/js/stepper.js",
    "components/dropdown/js/dropdown.js", "components/dropdown_options/js/dropdown_options.js",
    "components/rebind_entry/js/rebind_entry.js",
    "components/slider/slider_alt.html", "components/toggle/toggle.html", "components/stepper/stepper_alt.html",
    "components/dropdown_options/dropdown_options_alt.html", "components/rebind_entry/rebind_entry.html",
    "components/oak_option_button/oak_option_button.html", "components/list_button/list_button.html",
    "components/main_menu_button/main_menu_button.html", "menu_options/menu_options.html",
    # The page is laid out by the game's stylesheets (page.js): the two every menu has, then the page's own.
    "_shared/css/gbx.css", "_shared/css/oakgame.css", "_shared/css/oakscroll.css",
    "menu_options/css/menu_options.css", "navigationbar/css/navigationbar.css",
    "components/category_divider/css/category_divider.css",
)
SCRIPTS = tuple(Path(path).name for path in FILES if path.endswith(".js"))
MENU_STYLESHEETS = ("gbx.css", "oakgame.css")
# The keyboard key table fills the glyph manager the game creates first (gbxmain.js: var GlyphMgr = new GlyphManager).
GLYPH_TABLE = "glyph_map_keyboard_mouse.js"


def _wanted() -> dict:
    return {Path(path).name: CACHE / Path(path).name for path in FILES}


def available() -> bool:
    return GAME_FILES.is_file() or all(path.is_file() for path in _wanted().values())


def copies(refresh: bool = False) -> dict:
    wanted = _wanted()
    if refresh or not all(path.is_file() for path in wanted.values()):
        fetch()
    missing = [name for name, path in wanted.items() if not path.is_file()]
    if missing:
        raise RuntimeError(f"game files missing: {missing}")
    return wanted


def fetch() -> None:
    if not GAME_FILES.is_file():
        raise RuntimeError("game_files is missing (see its README to build it)")
    if CACHE.exists():
        shutil.rmtree(CACHE)
    CACHE.parent.mkdir(exist_ok=True)
    for index in range(0, len(FILES), CALL_SIZE):
        output = f"part{index // CALL_SIZE}"
        paths = [ROOT + path for path in FILES[index:index + CALL_SIZE]]
        # The reader only writes under its working folder, so it runs from build/.
        result = subprocess.run([str(GAME_FILES), output, *paths], cwd=CACHE.parent, capture_output=True,
                                timeout=GAME_FILES_TIMEOUT_S, check=False)
        if result.returncode != 0:
            raise RuntimeError("game_files refused: " + result.stdout.decode("utf-8", "replace").strip()[-200:])
        CACHE.mkdir(exist_ok=True)
        for file in (CACHE.parent / output).iterdir():
            shutil.move(str(file), CACHE / file.name)
        (CACHE.parent / output).rmdir()
