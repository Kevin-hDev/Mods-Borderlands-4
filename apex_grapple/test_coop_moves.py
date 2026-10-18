"""Tests coop_moves.py: on a guest, the engine's move combining off from its own rope to its first frame on the ground
after it, at most LONGEST_NS after the rope; the value found put back as found, once; put back at switch-off, through
the game's world when no character is left; on the host, never touched; through the frame loop."""

import types

from grapple_fixture import SECOND, check, fails, fresh, sdk_stubs, state
from apex_grapple import coop_moves, frame

import sys

MS = 1_000_000
commands: list[tuple] = []
found = {"value": 1}
kismet = state["kismet"]
kismet.GetConsoleVariableIntValue = lambda name: found["value"] if name == coop_moves.VARIABLE else -1
kismet.ExecuteConsoleCommand = lambda context, command, player: commands.append((context, command, player))


def notes(text: str) -> int:
    return sum(text in line for line in state["misc"])


player, rope = fresh(on_ground=False)
movement = player.CharacterMovement

coop_moves.step(player, False, 0)
check("no rope yet: nothing run", commands == [])
coop_moves.step(player, True, 10 * MS)
check("a rope: combining off, through the player's character and controller",
      commands == [(player, "p.NetEnableMoveCombining 0", state["pc"])])
check("and said with the value found", notes("co-op: moves sent one by one during the rope (p.NetEnableMoveCombining 1 -> 0)") == 1)
coop_moves.step(player, True, 20 * MS)
check("run once per window", len(commands) == 1)
coop_moves.step(player, False, 30 * MS)
check("the rope over, in the air: still off", len(commands) == 1)
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
coop_moves.step(player, False, 40 * MS)
check("landed: put back as found, said", commands[-1] == (player, "p.NetEnableMoveCombining 1", state["pc"])
      and notes("co-op: moves combined again (p.NetEnableMoveCombining 1)") == 1)
coop_moves.step(player, False, 50 * MS)
check("put back once", len(commands) == 2)

found["value"] = 0
coop_moves.step(player, True, 60 * MS)
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
coop_moves.step(player, False, 70 * MS)
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
coop_moves.step(player, False, 80 * MS)
check("found off by the player, left off", commands[-1][1] == "p.NetEnableMoveCombining 0")
found["value"] = 1

movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
coop_moves.step(player, True, 100 * MS)
coop_moves.step(player, False, 100 * MS + coop_moves.LONGEST_NS)
check("never landing, off up to the longest", commands[-1][1] == "p.NetEnableMoveCombining 0")
coop_moves.step(player, False, 101 * MS + coop_moves.LONGEST_NS)
check("past it, put back", commands[-1][1] == "p.NetEnableMoveCombining 1")

coop_moves.step(player, True, 200 * MS)
coop_moves.reset()
check("switched off: put back through the character", commands[-1][:2] == (player, "p.NetEnableMoveCombining 1"))
coop_moves.reset()
check("and not again", commands[-1][:2] == (player, "p.NetEnableMoveCombining 1") and len(commands) == 8)

coop_moves.step(player, True, 300 * MS)
coop_moves.release(None)
check("with no character, through the game's world", commands[-1][0] is sys.modules["mods_base"].ENGINE.GameViewport.World)

kismet.ExecuteConsoleCommand = lambda context, command, player: (_ for _ in ()).throw(RuntimeError("refused"))
try:
    coop_moves.step(player, True, 400 * MS)
    raised = False
except RuntimeError:
    raised = True
check("a refused command is raised to the frame loop, and leaves the window closed to try again",
      raised and coop_moves._kept is None)
kismet.ExecuteConsoleCommand = lambda context, command, player: commands.append((context, command, player))

# Through the frame loop: only on a guest, with the player's own rope.
commands.clear()
player, _rope = fresh(on_ground=False)
frame.on_frame(player.anim, 1 * SECOND)
frame.rope.fire(player, 1 * SECOND)
frame.on_frame(player.anim, 1 * SECOND + 10 * MS)
check("on the host, the frame loop never touches it", frame.rope.busy and commands == [])
frame.rope.reset()
player, _rope = fresh(on_ground=False)
player.role = "ROLE_AutonomousProxy"
frame.on_frame(player.anim, 2 * SECOND)
frame.rope.fire(player, 2 * SECOND)
frame.on_frame(player.anim, 2 * SECOND + 10 * MS)
check("on a guest with its rope, the frame loop turns combining off",
      frame.rope.busy and commands and commands[-1][1] == "p.NetEnableMoveCombining 0")
frame.stop()
check("and the mod switched off puts it back", commands and commands[-1][1] == "p.NetEnableMoveCombining 1")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
