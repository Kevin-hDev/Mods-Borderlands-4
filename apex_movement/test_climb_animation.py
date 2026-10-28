"""Tests the arms' climbing animation: the game's climb up played in FullBody with session G's blend and enough loops for
the longest climb, stopped by slot name, never twice; missing arms or a failure reported once without stopping the
climb, and a reset that tries again."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import climb_animation, climb_body, game  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def errors(text: str) -> int:
    return sum(text in line for line in state["errors"])


player = sdk_stubs.FakeCharacter()
sdk_stubs.use_character(state, player)
game.refresh(0)

climb_animation.start(1.0)
check("without arms nothing plays and it is reported once", errors("climb animation unavailable") == 1)
climb_animation.stop()
climb_animation.start(1.0)
check("the report is not repeated", errors("climb animation unavailable") == 1)

game.forget()
game.refresh(0)
arms = sdk_stubs.add_arms(state, player)
sequence = state["objects"][("AnimSequence", sdk_stubs.CLIMB_ANIMATION_PATH)]
climb_animation.start(372 / 370)
check("a climb plays the game's climb up on the arms, in FullBody, with session G's blend", arms.plays == [{
    "Asset": sequence, "SlotNodeName": "FullBody", "BlendInTime": 0.2, "BlendOutTime": 0.2, "InPlayRate": 1.0,
    "LoopCount": 3, "BlendOutTriggerTime": -1.0, "InTimeToStartMontageAt": 0.0}])
check("the log says it played, once", sum("climb animation playing on the arms, 3 loops at most" in line
                                           for line in state["misc"]) == 1)
climb_animation.stop()
check("its end stops the slot by name with the same blend", arms.stops == [(0.2, "FullBody")])
climb_animation.stop()
check("a second stop does nothing", len(arms.stops) == 1)
climb_animation.start(744 / 100)
check("the loops cover the longest climb they are given, 7.44 s in loops of 0.6 s, plus one",
      arms.plays[-1]["LoopCount"] == 14)
check("a second climb does not log it again", sum("climb animation playing" in line for line in state["misc"]) == 1)
climb_animation.reset()
climb_animation.stop()
check("after a reset, the old arms are not stopped", len(arms.stops) == 1)


def refuse(**kwargs: object) -> object:
    raise RuntimeError("unknown slot")


arms.PlaySlotAnimationAsDynamicMontage = refuse
climb_animation.start(1.0)
check("a failure is reported once", errors("climb animation switched off after an error: RuntimeError('unknown slot')") == 1)
climb_animation.start(1.0)
climb_animation.stop()
check("then the animation stays off, and nothing is stopped", errors("switched off after an error") == 1 and len(arms.stops) == 1)
del arms.PlaySlotAnimationAsDynamicMontage
climb_animation.start(1.0)
check("still off until a reset", len(arms.plays) == 2)
climb_animation.reset()
climb_animation.start(1.0)
check("a reset tries again, and logs it again", len(arms.plays) == 3
      and sum("climb animation playing" in line for line in state["misc"]) == 2)

# The coordinator always sends the same climb lifetime and current wall to the independent third-person layer.
body_calls = []
climb_body.start = lambda character, wall, duration: body_calls.append(("start", character, wall, duration))
climb_body.update_wall = lambda wall: body_calls.append(("wall", wall))
climb_body.stop = lambda: body_calls.append(("stop",))
climb_body.reset = lambda: body_calls.append(("reset",))
wall = object()
climb_animation.start(2.5, wall)
climb_animation.update_wall(wall)
climb_animation.stop()
climb_animation.reset()
check("the arms coordinator starts, updates, stops and resets the third-person layer",
      body_calls == [("start", player, wall, 2.5), ("wall", wall), ("stop",), ("reset",)])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
