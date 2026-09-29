"""Tests the depth of field kept off while the heirloom shows: off once, the player's value read first; given back as
read when the heirloom is hidden, once; nothing sent without a player controller, the player's value kept to give back
later; an engine call that fails is said and never stops the heirloom's showing."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

fails: list[str] = []
said: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = heirloom_stubs.install()
commands: list[str] = []
player_value = [3]


def execute(_world: object, command: str, _pc: object) -> None:
    commands.append(command)


console = types.SimpleNamespace(GetConsoleVariableIntValue=lambda name: player_value[0], ExecuteConsoleCommand=execute)
state["classes"]["KismetSystemLibrary"] = types.SimpleNamespace(ClassDefaultObject=console)
state["pc"] = types.SimpleNamespace()

from apex_heirloom import apex_depth_of_field as depth  # noqa: E402

depth.follow(True, said.append)
depth.follow(True, said.append)
check("shown, the depth of field goes off once, the player's value read first",
      commands == ["r.DepthOfFieldQuality 0"] and depth.STATE.kept == 3)
depth.follow(False, said.append)
depth.follow(False, said.append)
check("hidden, the player's value comes back as read, once", commands[-1] == "r.DepthOfFieldQuality 3"
      and len(commands) == 2 and depth.STATE.kept is None)
depth.give_back()
check("given back with nothing of ours set, nothing is sent", len(commands) == 2)

state["pc"] = None
depth.follow(True, said.append)
check("no player controller: nothing sent, nothing kept, and it is said",
      len(commands) == 2 and depth.STATE.kept is None and "no player controller" in said[-1])

state["pc"] = types.SimpleNamespace()
depth.follow(True, said.append)
state["pc"] = None
depth.follow(False, said.append)
check("no player controller to give it back: the player's value is kept, to give back later",
      depth.STATE.kept == 3 and commands[-1] == "r.DepthOfFieldQuality 0")
state["pc"] = types.SimpleNamespace()
depth.give_back()
check("... and it comes back at the next chance", commands[-1] == "r.DepthOfFieldQuality 3" and depth.STATE.kept is None)


def broken(*_args: object) -> None:
    raise RuntimeError("engine refused")


console.ExecuteConsoleCommand = broken
try:
    depth.follow(True, said.append)
    raised = False
except Exception:
    raised = True
check("an engine call that fails is said, not raised, and nothing is kept",
      not raised and "could not be changed" in said[-1] and depth.STATE.kept is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
