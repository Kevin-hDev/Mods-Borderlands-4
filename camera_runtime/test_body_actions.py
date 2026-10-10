"""Tests the actions that send the body back to the crosshair: the game's own action keys read by their state, the key
list followed every second, the weapon firing, a second after the last one, and a signal the game will not give left
out once while the others go on."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import body_actions  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def mapping(action: str | None, key: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(Action=None if action is None else types.SimpleNamespace(Name=action),
                                 Key=types.SimpleNamespace(KeyName=key))


down: set[str] = set()
mappings = [mapping("Action_Fire", "LeftMouseButton"), mapping("Action_Gadget", "G"),
            mapping("Action_Skill", "Gamepad_LeftShoulder"), mapping("Action_Jump_HoldToGlide", "SpaceBar"),
            mapping(None, "Z"), mapping("Action_GadgetDoubleTap", "ComboKey")]
pc = types.SimpleNamespace(PlayerInput=types.SimpleNamespace(EnhancedActionMappings=mappings),
                           IsInputKeyDown=lambda key: key.KeyName in down)
anim = types.SimpleNamespace(bIsFiring=False)
lines: list[str] = []
actions = body_actions.Actions(lambda name: types.SimpleNamespace(KeyName=name), lines.append)
SECOND = 1_000_000_000

check("only the shot, grenade and skill keys are read",
      body_actions.action_keys(mappings) == ("G", "Gamepad_LeftShoulder", "LeftMouseButton"))
check("nothing pressed, nothing to face", actions.acting(pc, anim, 0) is False)
check("the keys read are said once", lines == ["action keys G Gamepad_LeftShoulder LeftMouseButton"])
down.add("G")
check("a grenade key held faces the crosshair", actions.acting(pc, anim, 10) is True)
down.clear()
check("a second after its release, still", actions.acting(pc, anim, SECOND) is True)
check("past the second, the run again", actions.acting(pc, anim, SECOND + 11) is False)
anim.bIsFiring = True
check("the weapon firing faces the crosshair, key or not", actions.acting(pc, anim, 2 * SECOND) is True)
anim.bIsFiring = False
mappings.append(mapping("Action_Melee", "V"))
check("the list is not read again within the second",
      actions.acting(pc, anim, 2 * SECOND + 1) is True and "V" not in actions.keys)
actions.acting(pc, anim, 4 * SECOND)
check("read again after it, a new key is followed and said", "V" in actions.keys and lines[-1].endswith("V"))
actions.acting(pc, anim, 6 * SECOND)
check("an unchanged list is not said again", len(lines) == 2)
pc.IsInputKeyDown = lambda key: 1 / 0
check("key states the game will not give are left out, said once, and the weapon still counts",
      actions.acting(pc, anim, 7 * SECOND) is False and lines[-1] == "key states signal unreadable, left out: "
                                                                      "ZeroDivisionError")
anim.bIsFiring = True
check("the weapon still turns the body", actions.acting(pc, anim, 8 * SECOND) is True and len(lines) == 3)
del anim.bIsFiring
actions.reset()
check("an unreadable weapon is left out too", actions.acting(pc, anim, 9 * SECOND) is False
      and lines[-1].startswith("firing signal unreadable"))
empty = body_actions.Actions(lambda name: name, lines.append)
pc_without = types.SimpleNamespace(PlayerInput=types.SimpleNamespace(EnhancedActionMappings=[]),
                                   IsInputKeyDown=lambda key: False)
empty.acting(pc_without, types.SimpleNamespace(bIsFiring=False), 0)
check("a list without action keys is said once", lines[-1] == "action keys none: only shots turn the body")
check("the keys are bounded", len(body_actions.action_keys(
    [mapping("Action_Fire", f"Key{index}") for index in range(100)])) == body_actions.MAX_KEYS)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
