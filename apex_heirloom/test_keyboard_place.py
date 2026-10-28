"""Tests the keyboard key by default: the key right of Tab, named after the player's layout, or none at all."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


heirloom_stubs.install()

from apex_heirloom import keyboard_place  # noqa: E402

FRENCH, ENGLISH = 0x040C040C, 0x04090409
# What Windows answers for the key right of Tab: A on a French keyboard, Q on an English one.
RIGHT_OF_TAB = {FRENCH: ord("A"), ENGLISH: ord("Q")}


def windows(layout: int, answers: dict = RIGHT_OF_TAB) -> types.SimpleNamespace:
    asked: list[tuple] = []

    def map_key(code: int, kind: int, held_layout: int) -> int:
        asked.append((code, kind, held_layout))
        return answers.get(held_layout, 0)

    return types.SimpleNamespace(GetKeyboardLayout=lambda thread: layout, MapVirtualKeyExW=map_key, asked=asked)


french = windows(FRENCH)
check("a French keyboard gives A", keyboard_place.default_key(french) == "A")
check("the key is asked by its place right of Tab, in the player's layout",
      french.asked == [(0x10, keyboard_place.MAPVK_VSC_TO_VK, FRENCH)])
check("an English keyboard gives Q", keyboard_place.default_key(windows(ENGLISH)) == "Q")
check("a layout with no letter there gives no key", keyboard_place.default_key(windows(0x1, {0x1: 0xDE})) is None)
check("a layout Windows cannot map gives no key", keyboard_place.default_key(windows(0x2, {})) is None)


def broken(_thread: int) -> int:
    raise OSError("no user32")


check("a Windows call that fails gives no key",
      keyboard_place.default_key(types.SimpleNamespace(GetKeyboardLayout=broken)) is None)
check("letters are named as the game names them", keyboard_place.name_for(ord("Z")) == "Z")
check("anything else is not named", keyboard_place.name_for(0x31) is None and keyboard_place.name_for(0x5B) is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
