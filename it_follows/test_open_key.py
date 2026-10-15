"""Tests the key that opens the window (open_key.py) and the welcome's edition (welcome.py): F5 at first; a key name
valid or refused (Escape, the left button, none, odd characters); a value that is no key read as F5; the SDK's keybind
given the chosen key; the key's press opening the window; the watch that closes the window with F5, deaf until the key
is first up, none for a key Windows has no fixed code for; the welcome due until its edition is seen."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import control_console_keys, control_window, open_key, welcome  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    check("F5 at first (decision 48)", open_key.DEFAULT == "F5" == open_key.key() and open_key.bind.key == "F5")
    check("a key name valid or refused", open_key.valid("F6") and open_key.valid("Gamepad_FaceButton_Bottom")
          and not any(open_key.valid(name) for name in ("Escape", "LeftMouseButton", "", "None", "F 5", 7, None)))
    open_key.option.value = "Escape"
    check("a value that is no key reads as F5", open_key.key() == "F5" and open_key.align() is False)
    open_key.option.value = "F6"
    check("the SDK's keybind given the chosen key, once", open_key.align() is True and open_key.bind.key == "F6"
          and open_key.align() is False)
    opened: list = []
    control_window.start = lambda: opened.append(True)
    open_key.bind.callback()
    check("the key's press opens the window", opened == [True])
    open_key.option.value = "F5"
    watch = open_key.closer()
    check("the watch closes with F5, deaf until it is first up", watch is not None and watch.key
          == control_console_keys.KEY_NAMES["F5"] and watch.muted)
    open_key.option.value = "ThumbMouseButton"
    check("no watch for a key Windows has no fixed code for", "ThumbMouseButton" not in control_console_keys.KEY_NAMES
          and open_key.closer() is None)
    check("the welcome due at first", welcome.due())
    welcome.seen.value = welcome.EDITION
    check("seen, it is due no more", not welcome.due())
    welcome.seen.value = "x"
    check("a value that is no edition: due", welcome.due())
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
