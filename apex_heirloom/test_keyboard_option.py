"""Tests the keyboard key's option: the camera runtime's shortcut rules, and never the mouse wheel."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()

from apex_heirloom import keys  # noqa: E402
from apex_heirloom.controller_option import normalize_key  # noqa: E402
from apex_heirloom.keyboard_option import normalize_put_away_key  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def refused(value, check_key=normalize_put_away_key) -> bool:
    try:
        check_key(value)
    except ValueError:
        return True
    return False


check("a key or a mouse side button is kept",
      normalize_put_away_key("A") == "A" and normalize_put_away_key("ThumbMouseButton") == "ThumbMouseButton")
check("no key is a valid empty value", normalize_put_away_key(None) is None and normalize_put_away_key("None") is None)
check("the wheel is refused, up and down", refused("MouseScrollUp") and refused("MouseScrollDown"))
check("the shortcut rules still hold: left click and controller refused",
      refused("LeftMouseButton") and refused("Gamepad_FaceButton_Left"))
keys.keyboard_key.value = "MouseScrollDown"
check("the wheel typed in the SDK's menu, or loaded from disk, unbinds the key",
      keys.keyboard_key.value is None and keys.keyboard_bind.key is None)
keys.keyboard_key.value = "A"
check("the window refuses the wheel too", normalize_key(keys.keyboard_key, "Q") == "Q"
      and refused("MouseScrollUp", lambda value: normalize_key(keys.keyboard_key, value)))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
