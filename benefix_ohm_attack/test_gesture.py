"""Tests the raised hand: a pose played on the arms and on the body in the left hand's slot, faded out when the
shot ends, and never in the way of a shot when it cannot be played."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import gesture, hand, report  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


pc, character = sdk_stubs.player(state)
arms, body = state["arms_animation"], state["body_animation"]
hand.forget()

gesture.lower()
check("lowering a hand that is not raised does nothing", arms.stopped == [] and body.stopped == [])

check("raising the hand names what took the pose: the arms and the body", gesture.raise_hand(character) == ("arms", "body"))
asked, asked_body = arms.played[0], body.played[0]
check("the arms play our own animation, found in the game's memory", asked["Asset"] == "the hand pose" and state["loads"] == [])
check("the body plays its own pose", asked_body["Asset"] == "the body pose")
check("both in the Offhand slot", asked["SlotNodeName"] == "Offhand" and asked_body["SlotNodeName"] == "Offhand")
check("faded in, held for an hour's worth of turns, from its start, at its own pace",
      all(one["BlendInTime"] == 0.2 and one["BlendOutTime"] == 0.25 and one["LoopCount"] == 3600
          and one["InPlayRate"] == 1.0 and one["InTimeToStartMontageAt"] == 0.0 and one["BlendOutTriggerTime"] == -1.0
          for one in (asked, asked_body)))

gesture.lower()
check("lowering fades out each montage on the instance that plays it, and only it",
      arms.stopped == [(0.25, "a montage")] and body.stopped == [(0.25, "a body montage")])
gesture.lower()
check("lowering twice stops them once", len(arms.stopped) == 1 and len(body.stopped) == 1)

gesture.raise_hand(character)
gesture.raise_hand(character)
check("raising again first lowers the pose already playing",
      len(arms.played) == 3 and len(arms.stopped) == 2 and len(body.played) == 3 and len(body.stopped) == 2)
gesture.lower()

arms.gives = ("a montage", "an output parameter")
gesture.raise_hand(character)
gesture.lower()
check("a montage handed back with output parameters is the one stopped", arms.stopped[-1] == (0.25, "a montage"))
arms.gives = "a montage"

played = len(arms.played)
del state["objects"][sdk_stubs.HAND_POSE]
gesture.raise_hand(character)
check("a pose the game dropped from memory is loaded from its container, as an animation",
      state["loads"] == [sdk_stubs.HAND_POSE] and state["load_classes"] == ["/Script/Engine.AnimSequence"]
      and len(arms.played) == played + 1)
gesture.lower()

del state["objects"][sdk_stubs.HAND_POSE]
state["in_archives"] = False
errors, played, stopped = len(state["errors"]), len(arms.played), len(arms.stopped)
check("without its container the arms stay down, the body still takes its pose, and the log names the container, once",
      gesture.raise_hand(character) == ("body",) and len(arms.played) == played and len(state["errors"]) == errors + 1
      and "000_BenefixOhmAttack_999_P" in state["errors"][-1] and "on the arms" in state["errors"][-1])
gesture.raise_hand(character)
check("said once only", len(state["errors"]) == errors + 1)
gesture.lower()
check("and nothing is stopped on the arms afterwards", len(arms.stopped) == stopped)
state["in_archives"] = True
state["objects"][sdk_stubs.HAND_POSE] = "the hand pose"

arms.gives = None
report.reset()
errors = len(state["errors"])
check("a pose the game plays nothing of is said, and leaves nothing to stop on the arms",
      gesture.raise_hand(character) == ("body",) and len(state["errors"]) == errors + 1
      and "played nothing" in state["errors"][-1])
gesture.lower()
check("the arms had nothing to stop", len(arms.stopped) == stopped)
arms.gives = "a montage"

state["anim_instances"] = []
hand.forget()
played = len(arms.played)
check("without first-person arms only the body takes the pose",
      gesture.raise_hand(character) == ("body",) and len(arms.played) == played)
gesture.lower()
state["anim_instances"] = [arms]
hand.forget()

body.refuses = True
report.reset()
errors = len(state["errors"])
check("a body that refuses the pose: the arms take theirs, said once for the body",
      gesture.raise_hand(character) == ("arms",) and len(state["errors"]) == errors + 1
      and "on the body" in state["errors"][-1])
gesture.lower()
arms.refuses = True
check("the arms refusing after the body did: nothing raised, and the arms' failure is said too",
      gesture.raise_hand(character) == () and len(state["errors"]) == errors + 2
      and "on the arms" in state["errors"][-1])
gesture.lower()
arms.refuses = body.refuses = False
mesh = character.Mesh
del character.Mesh
check("a character without a body mesh: the arms take theirs", gesture.raise_hand(character) == ("arms",))
gesture.lower()
character.Mesh = mesh

stopped, stopped_body = len(arms.stopped), len(body.stopped)
gesture.raise_hand(character)
state["gone"].add(id("a montage"))
gesture.lower()
check("a montage the game already removed is not stopped, the other one is",
      len(arms.stopped) == stopped and len(body.stopped) == stopped_body + 1)
state["gone"].clear()

gesture.raise_hand(character)
arms.Montage_Stop = lambda blend_out, montage: (_ for _ in ()).throw(RuntimeError("the arms refuse"))
report.reset()
errors, stopped_body = len(state["errors"]), len(body.stopped)
gesture.lower()
check("arms that refuse to stop the pose: said, not raised, and the body's pose is still stopped",
      len(state["errors"]) == errors + 1 and len(body.stopped) == stopped_body + 1)

check("the fake game holds the two poses under the names the mod asks for, each its own",
      gesture.ANIMATION == sdk_stubs.HAND_POSE and gesture.BODY_ANIMATION == sdk_stubs.BODY_POSE
      and gesture.BODY_ANIMATION != gesture.ANIMATION)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
