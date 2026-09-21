"""Tests the arms' grapple animation: the game's own, played as a montage, and never costing a pull."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import animation, arms, game  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
hands = sdk_stubs.FakeArms(player)
state["anim_instances"] = [hands]
state["pc"] = sdk_stubs.player(player, state["mappings"])
game.refresh(0, at_once=True)

check("the arms are found by their mesh, there being no field for them", arms.find(player) is hands)

animation.start()
check("the game's own animation is played on the arms", len(hands.played) == 1)
check("on the slot that covers the whole rig", hands.played[0]["SlotNodeName"] == animation.SLOT)
check("it is AS_Grapple, the animation the game's settings name",
      hands.played[0]["Asset"] is game.grapple_animation())
check("the throw plays once and does not loop", hands.played[0]["LoopCount"] == 1)
check("at the game's own speed", hands.played[0]["InPlayRate"] == 1.0)
check("and it is written once", sum("grapple animation playing" in line for line in state["misc"]) == 1)

animation.start()
check("a second start while it plays changes nothing", len(hands.played) == 1)

# The hand holds the rope from the moment the hook sets, instead of replaying the throw in a loop.
animation.hold()
check("holding replays the same animation", len(hands.played) == 2)
check("frozen, so the hand does not move", hands.played[1]["InPlayRate"] == animation.FROZEN_RATE)
check("on the pose that holds the rope, not on the throw",
      hands.played[1]["InTimeToStartMontageAt"] > 0.0)
check("and it is written with the moment it froze at", any("hand held at" in line for line in state["misc"]))
animation.hold()
check("a second hold changes nothing", len(hands.played) == 2)

animation.stop()
check("stopping ends the slot this file played on", hands.stopped == [(animation.BLEND_S, animation.SLOT)])
animation.stop()
check("a second stop does nothing", len(hands.stopped) == 1)

animation.start()
check("it can be played again after a stop", len(hands.played) == 3)
animation.stop()

# A failure must cost the animation alone: a pull without hands beats no pull at all.
hands.raises = True
animation.reset()
state["anim_instances"] = [hands]
animation.start()
check("an animation that fails is written once", any("switched off after an error" in line for line in state["errors"]))
hands.raises = False
animation.start()
check("and it stays off until the next character or switch-on", len(hands.played) == 3)

animation.reset()
state["anim_instances"] = []
animation.start()
check("no arms found says so rather than going quiet",
      any("the arms or AS_Grapple were not found" in line for line in state["errors"]))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
