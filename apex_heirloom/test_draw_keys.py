"""Tests the weapon keys: read from the player's own key list, only those of the game's weapon actions are listened to,
hidden, every event seen; a press is told, never blocked, and an error in it is written once; stop lets them all go,
and listening again first lets the old ones go."""

import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import heirloom_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = heirloom_stubs.install()
made: list = []
make = sys.modules["mods_base"].keybind
sys.modules["mods_base"].keybind = lambda *args, **kwargs: made.append(make(*args, **kwargs)) or made[-1]

from apex_heirloom import draw_keys  # noqa: E402

made.clear()  # The mod's own put-away keys, bound as it loads.


def mapping(action: str | None, key: str):
    named = None if action is None else types.SimpleNamespace(Name=action)
    return types.SimpleNamespace(Action=named, Key=types.SimpleNamespace(KeyName=key))


# The player's key list as the game gives it (Apex Grapple's input_list.py reads the same, verified in game).
mappings = [mapping("Action_Fire", "LeftMouseButton"), mapping("Action_Weapon1", "One"),
            mapping("Action_NextWeapon", "Gamepad_FaceButton_Top"), mapping("Action_NextWeapon", "MouseScrollDown"),
            mapping("Action_PrevWeapon", "MouseScrollUp"), mapping("Action_WeaponWheel", "Gamepad_DPad_Up"),
            mapping("Action_Reload", "Gamepad_FaceButton_Left"), mapping(None, "Two"),
            mapping("Action_Weapon2", "Bad Name!")]
state["pc"] = types.SimpleNamespace(PlayerInput=types.SimpleNamespace(EnhancedActionMappings=mappings))
check("the weapon keys are those of the game's weapon actions, whatever the player set, a malformed name left out",
      draw_keys.keys(mappings) == {"One", "Gamepad_FaceButton_Top", "MouseScrollDown", "MouseScrollUp",
                                   "Gamepad_DPad_Up"})

pressed: list[bool] = []
draw_keys.listen(lambda: pressed.append(True))
check("listening binds each weapon key once, hidden, seeing every event, and enabled",
      sorted(bind.key for bind in made) == sorted(draw_keys.keys(mappings))
      and all(bind.is_hidden and bind.event_filter is None and bind.is_enabled for bind in made)
      and draw_keys.listening())
check("... and the log says which keys", state["misc"][-1] == "[Tidy Weapons] weapon keys listened until the weapons "
      "are back: Gamepad_DPad_Up, Gamepad_FaceButton_Top, MouseScrollDown, MouseScrollUp, One")
one = next(bind for bind in made if bind.key == "One")
check("a press is told, and the key is left to the game",
      one.callback(types.SimpleNamespace(name="IE_Pressed")) is None and pressed == [True])
one.callback(types.SimpleNamespace(name="IE_Released"))
one.callback(types.SimpleNamespace(name="IE_Repeat"))
check("a release or a repeat is not a press", pressed == [True])

draw_keys.stop()
check("stop lets every key go", not draw_keys.listening() and not any(bind.is_enabled for bind in made))
draw_keys.stop()
check("stopping again is harmless", not draw_keys.listening())


def broken() -> None:
    raise RuntimeError("boom")


made.clear()
draw_keys.listen(broken)
first = list(made)
draw_keys.listen(broken)
check("listening again lets the old keys go first", not any(bind.is_enabled for bind in first)
      and sum(bind.is_enabled for bind in made) == len(first))
press = made[-1].callback
check("a press that fails still leaves the key to the game, and is written once",
      press(types.SimpleNamespace(name="IE_Pressed")) is None and press(types.SimpleNamespace(name="IE_Pressed")) is None
      and len(state["errors"]) == 1 and "weapon key press not followed" in state["errors"][0])
draw_keys.stop()

draw_keys.listen(broken)
stuck, free = made[-2:]
stuck.disable = broken
state["errors"].clear()
draw_keys.stop()
check("a key the SDK will not let go is written, and the others still go",
      not draw_keys.listening() and not free.is_enabled and len(state["errors"]) == 1
      and "could not be let go" in state["errors"][0])

state["pc"] = None
made.clear()
draw_keys.listen(broken)
check("no player: nothing to listen to", not made and not draw_keys.listening())

state["pc"] = types.SimpleNamespace(PlayerInput=types.SimpleNamespace(
    EnhancedActionMappings=[mapping("Action_Weapon1", "One")] * (draw_keys.MAX_MAPPINGS + 5)
    + [mapping("Action_Weapon2", "Two")]))
check("a key list is read up to MAX_MAPPINGS entries only",
      draw_keys.keys(state["pc"].PlayerInput.EnhancedActionMappings) == {"One"})


def refusing(*_args, **_kwargs):
    bind = make("refused", "Two", None)
    bind.enable = broken
    made.append(bind)
    return bind


state["pc"] = types.SimpleNamespace(PlayerInput=types.SimpleNamespace(
    EnhancedActionMappings=[mapping("Action_Weapon1", "One"), mapping("Action_Weapon2", "Two")]))
made.clear()
draw_keys.keybind = lambda *args, **kwargs: (
    refusing() if args[1] == "Two" else made.append(make(*args, **kwargs)) or made[-1])
try:
    draw_keys.listen(broken)
    raised = False
except RuntimeError:
    raised = True
check("a key the SDK refuses: raised, and no key stays bound", raised and not draw_keys.listening()
      and not any(bind.is_enabled for bind in made))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
