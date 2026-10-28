"""Tests the jump press: Croix injected for the jump action on the player's own subsystem, looked up once per controller,
nothing pressed without a controller, a jump action or a subsystem, and a forget that looks up again."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import jump_press  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("without a controller nothing is pressed or looked up", not jump_press.press() and state["subsystem_scans"] == 0)

state["subsystems"].append(types.SimpleNamespace(Outer=types.SimpleNamespace(Name="OtherPlayer")))
sdk_stubs.use_character(state, sdk_stubs.FakeCharacter())
mine = state["subsystems"][-1]
check("with a controller Croix is pressed", jump_press.press())
function, target, kwargs = state["injections"][0]
check("through the interface's injection function, on the player's own subsystem",
      function is state["inject_function"] and target is mine)
check("for the jump action, fully pressed, without modifiers or triggers",
      str(kwargs["Action"].Name) == "Action_Jump_HoldToGlide" and kwargs["Value"].X == 1.0
      and kwargs["Modifiers"] == [] and kwargs["Triggers"] == [])
jump_press.press()
check("looked up once per controller", len(state["injections"]) == 2 and state["subsystem_scans"] == 1)

sdk_stubs.use_character(state, sdk_stubs.FakeCharacter())
jump_press.press()
check("a new controller is looked up again, on its own subsystem", state["subsystem_scans"] == 2
      and state["injections"][-1][1] is state["subsystems"][-1])

state["mappings"] = [sdk_stubs.mapping("Action_Move", "Gamepad_Left2D")]
sdk_stubs.use_character(state, sdk_stubs.FakeCharacter())
check("without the jump action nothing is pressed", not jump_press.press() and len(state["injections"]) == 3)
jump_press.press()
check("and it is not looked up again every frame", state["subsystem_scans"] == 3)
jump_press.forget()
jump_press.press()
check("forget looks up again", state["subsystem_scans"] == 4)

state["mappings"] = [sdk_stubs.mapping("Action_Jump_HoldToGlide", "Gamepad_FaceButton_Bottom")]
state["subsystems"].clear()
jump_press.forget()
check("without the player's subsystem nothing is pressed", not jump_press.press())

sdk_stubs.use_character(state, sdk_stubs.FakeCharacter())
state["inject_function"] = None
jump_press.forget()
try:
    jump_press.press()
    raised = False
except ValueError:
    raised = True
check("a game without the interface raises, for the climb to report", raised)
check("then nothing is pressed, without looking up again", not jump_press.press() and state["subsystem_scans"] == 6)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
