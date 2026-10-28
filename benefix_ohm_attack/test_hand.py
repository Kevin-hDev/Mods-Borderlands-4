"""Tests where the left hand is: the arms' socket, and a spot beside the camera when it cannot be read."""

import math
import pathlib
import types
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import hand, report  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(found, wanted):
    return all(abs(a - b) < 1e-6 for a, b in zip(found, wanted))


pc, character = sdk_stubs.player(state)
hand.forget()
check("the hand is the middle of the palm, where the arms carry that socket", hand.spot(pc, character) == (10.0, -20.0, 40.0))
palm = state["sockets"].pop("FX_L_Hand_Weave")
check("on arms without it, the back of the wrist", hand.spot(pc, character) == (2.0, -22.0, 38.0))
state["sockets"]["FX_L_Hand_Weave"] = palm
check("the arms found are handed to whoever animates them", hand.arms(character) is state["arms_animation"].Outer)
scans = state["scans"]
hand.spot(pc, character)
check("the arms are looked for once, not at every frame", state["scans"] == scans)
state["anim_instances"] = []
hand.forget()
errors = len(state["errors"])
beside = hand.spot(pc, character)
check("without arms the beam leaves from low and left of the camera, said once",
      near(beside, (40.0, -25.0, 30.0)) and len(state["errors"]) == errors + 1)
scans = state["scans"]
hand.spot(pc, character)
check("after a failure the arms are not looked for again until the next shot", state["scans"] == scans)
hand.forget()
hand.spot(pc, character)
check("the next shot looks again", state["scans"] == scans + 1)
state["anim_instances"] = [state["arms_animation"]]
state["sockets"].clear()
hand.forget()
report.reset()
errors = len(state["errors"])
check("arms without any hand socket: beside the camera, said once",
      near(hand.spot(pc, character), (40.0, -25.0, 30.0)) and len(state["errors"]) == errors + 1)

state["anim_instances"] = [state["arms_animation"]]
state["sockets"]["FX_L_Hand_Weave"] = palm
hand.forget()
report.reset()
# The game's own numbers: the arms drawn at 77 degrees, Kevin's world at 110.
state["fov"], state["arms_fov"] = 110.0, 77.0
spread = math.tan(math.radians(110.0) / 2) / math.tan(math.radians(77.0) / 2)
check("with the world drawn wider than the arms, the hand is where the world shows what the arms show",
      near(hand.spot(pc, character), (10.0, -20.0 * spread, 50.0 - 10.0 * spread)))
state["sockets"].clear()
hand.forget()
check("the spot beside the camera, which is no spot of the arms, is not moved",
      near(hand.spot(pc, character), (40.0, -25.0, 30.0)))
report.reset()

check("the body seen from outside is the character's own mesh", hand.body(character) is character.Mesh)
state["camera_mode"] = "ThirdPerson"
hand.forget()
scans = state["scans"]
check("in third person the hand is the body's, at its hand socket, not moved: the body is drawn as the world is",
      hand.spot(pc, character) == (30.0, -15.0, 120.0))
check("and the first-person arms are not looked for", state["scans"] == scans)
del state["body_sockets"]["FX_L_Hand"]
check("on a body without that socket, the hand's bone", hand.spot(pc, character) == (28.0, -14.0, 118.0))
state["body_sockets"].clear()
report.reset()
errors = len(state["errors"])
check("a body with neither: beside the camera, said once, naming the body",
      near(hand.spot(pc, character), (40.0, -25.0, 30.0)) and len(state["errors"]) == errors + 1
      and "on the body" in state["errors"][-1])
state["camera_mode"] = "Default"
state["sockets"]["FX_L_Hand_Weave"] = palm
state["fov"] = state["arms_fov"] = 90.0
hand.forget()
check("back in first person the hand is the arms' again", hand.spot(pc, character) == (10.0, -20.0, 40.0))

state["scanned"].clear()
hand.forget()
hand.spot(pc, character)
check("the arms are looked for among the animation instances, whatever their own class",
      state["scanned"] == [("/Script/Engine.AnimInstance", False)])

# Another player's character, in a game with several: its arms carry the same name.
other = types.SimpleNamespace(Name="Char_Player_1")
theirs = types.SimpleNamespace(Name="FirstPersonArms", Outer=other, DoesSocketExist=lambda name: True,
                               GetSocketLocation=lambda name: types.SimpleNamespace(X=900.0, Y=900.0, Z=900.0))
their_animation = types.SimpleNamespace(Outer=theirs)
theirs.GetAnimInstance = lambda: their_animation
state["anim_instances"] = [their_animation, state["arms_animation"]]
hand.forget()
check("the arms taken are the character's own, not another character's found first",
      hand.arms(character) is state["arms_animation"].Outer and hand.spot(pc, character) == (10.0, -20.0, 40.0))
check("and the arms kept are not handed to another character", hand.arms(other) is theirs)
state["anim_instances"] = [state["arms_animation"]]

for label, far in (("not a number", float("nan")), ("endless", float("inf")), ("beyond any level", 1e12)):
    hand.forget()
    report.reset()
    state["sockets"]["FX_L_Hand_Weave"] = (10.0, far, 40.0)
    errors = len(state["errors"])
    check(f"a hand whose place is {label}: beside the camera, said once",
          near(hand.spot(pc, character), (40.0, -25.0, 30.0)) and len(state["errors"]) == errors + 1)
state["sockets"]["FX_L_Hand_Weave"] = palm

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
