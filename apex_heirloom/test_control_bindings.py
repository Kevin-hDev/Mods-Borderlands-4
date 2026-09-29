"""Tests the CONTROLS page's service: a key captured is saved to its own device, with Grapple's refusals."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import panel_fixture as pf  # noqa: E402

from apex_heirloom import control_bindings, control_reserved, keys  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


bindings = control_bindings.Bindings()
check("a controller button is saved on the controller's key",
      bindings.save(("Gamepad_FaceButton_Top",)) == (True, "Saved: gamepad - Gamepad_FaceButton_Top")
      and keys.controller_bind.key == "Gamepad_FaceButton_Top")
check("a keyboard key is saved on the keyboard's key, the controller's kept",
      bindings.save(("Q",))[0] and keys.keyboard_bind.key == "Q" and keys.controller_bind.key == "Gamepad_FaceButton_Top")
check("a mouse button counts as the keyboard's", bindings.save(("ThumbMouseButton",))[0]
      and keys.keyboard_bind.key == "ThumbMouseButton")
check("Escape and Tilde are reserved", bindings.save(("Escape",)) == (False, control_bindings.RESERVED)
      and bindings.save(("Tilde",)) == (False, control_bindings.RESERVED))
check("the game's console key is reserved", bindings.save(("F10",)) == (False, control_bindings.RESERVED)
      and keys.keyboard_bind.key == "ThumbMouseButton")
check("a stick as an axis, or the left click, is refused",
      bindings.save(("Gamepad_LeftX",)) == (False, control_bindings.INVALID)
      and bindings.save(("LeftMouseButton",)) == (False, control_bindings.INVALID))
check("two keys at once are refused: one key per device", bindings.save(("Q", "E")) == (False, control_bindings.INVALID))
pf.state["refuse_saves"] = True
check("a failed save keeps the previous key", bindings.save(("E",)) == (False, control_bindings.FAILED)
      and keys.keyboard_bind.key == "ThumbMouseButton")
check("the defaults cannot be put back either while the disk refuses", bindings.reset() == (False, control_bindings.FAILED))
pf.state["refuse_saves"] = False
check("RESET CONTROLS puts both default keys back", bindings.reset() == (True, control_bindings.RESET)
      and keys.keyboard_bind.key == keys.keyboard_bind.default_key and keys.controller_bind.key == "Gamepad_FaceButton_Left")


def unreadable():
    raise RuntimeError("no input settings")


control_reserved.console_keys = unreadable
check("a key whose conflict with the console cannot be checked is not saved",
      bindings.save(("E",)) == (False, control_bindings.FAILED)
      and sum("console shortcuts" in line for line in pf.state["errors"]) == 1)
check("the summary names each device's key", bindings.summary().startswith("keyboard: ")
      and bindings.summary().endswith("gamepad: Gamepad_FaceButton_Left"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
