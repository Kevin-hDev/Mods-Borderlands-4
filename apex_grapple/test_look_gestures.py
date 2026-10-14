"""Tests look_gestures.py with the real look_moves, on Vex's arms and body as the game plays montages: a whole shot,
from the press to the arm out of sight, each gesture played in its slot, moved image by image, swapped from standing to
flying and back with the flight, and stopped; a pistol's stows; no weapon; the arms not found; a montage refused and an
animation missing."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import arms as arms_finder, look_gestures, look_load, look_moves  # noqa: E402
import vex_fixture  # noqa: E402

fails: list[str] = []
S = look_moves.NS_PER_S


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


character = sdk_stubs.FakeCharacter()
vex_fixture.install(state)
vex_fixture.remember(state)
arms, body = vex_fixture.dress(state, character)
G = look_gestures
moves = look_moves.Moves(0.4, 0.3, 0, 4.0)


def moved_to(record: list, wanted: list) -> bool:
    return len(record) == len(wanted) and all(slot == want_slot and abs(at - want_at) < 1e-9
                                              for (slot, at), (want_slot, want_at) in zip(record, wanted))


def frame(t: float, pull=None, holding: bool = True, kind: str | None = "RH") -> look_moves.Pose:
    pose = moves.frame(int(t * S), pull)
    G.frame(character, pose, kind, holding)
    return pose


frame(0.0)
check("at the shot, through the eyes: our arm in Offhand at its first image, the rifles' stow in Mainhand",
      vex_fixture.slots(arms) == [("Offhand", "AS_AG_Arms_Left"), ("Mainhand", "AS_RH_UnEquip_Offhand")]
      and arms.played[0]["InTimeToStartMontageAt"] == 0.0 and arms.played[0]["InPlayRate"] == G.FROZEN_RATE
      and abs(arms.played[1]["InTimeToStartMontageAt"] - (0.6666667 - 1.0 / 30.0)) < 1e-6
      and all(played["BlendInTime"] == 0.25 for played in arms.played))
check("and from behind: her left arm and her right one standing, no flight yet",
      vex_fixture.slots(body) == [("Offhand", "AS_AG_Body_Left_Stand"), ("Mainhand", "AS_AG_Body_RH_Stand")])
frame(0.2)
check("the arm moved through its entry, image by image", arms.moved[-1] == ("Offhand", 0.2))
frame(0.4)
frame(0.5, look_moves.Pull((1500.0, 0.0, 0.0), (2500.0, 0.0, 0.0)))
check("not yet caught: still standing", len(body.played) == 2)
moves.catch(int(0.5 * S), 1800.0, 600.0, 2500.0)
pose = frame(0.55, look_moves.Pull((1700.0, 0.0, 0.0), (2500.0, 0.0, 0.0)))
check("caught: the flight in UpperBody from its image 24 on, and both arms swapped to their flying gestures, "
      "crossfaded",
      vex_fixture.slots(body)[2:] == [("UpperBody", "AS_RH_Grapple"), ("Offhand", "AS_AG_Body_Left_Fly"),
                                      ("Mainhand", "AS_AG_Body_RH_Fly")]
      and abs(body.played[2]["InTimeToStartMontageAt"] - (24.0 + 6.0 * pose.fold) / 30.0) < 1e-9 and pose.fold < 0.2
      and (0.25, "Offhand") in body.stopped and (0.25, "Mainhand") in body.stopped)
pose = frame(0.8, look_moves.Pull((1500.0, 0.0, 0.0), (2500.0, 0.0, 0.0)))
check("the fold moves the arms and the flight on together",
      0.0 < pose.fold < 1.0 and moved_to(body.moved[-3:], [("UpperBody", (24.0 + 6.0 * pose.fold) / 30.0),
                                                           ("Offhand", pose.fold), ("Mainhand", pose.fold)])
      and moved_to(arms.moved[-1:], [("Offhand", 0.4 + pose.fold)]))
moves.end(int(1.0 * S))
before = len(body.played)
frame(1.0)
check("the end: the flight fades out, the left arm back standing, the right one goes back to the game",
      (0.25, "UpperBody") in body.stopped and vex_fixture.slots(body)[before:] == [("Offhand", "AS_AG_Body_Left_Stand")]
      and (look_moves.RETURN_S, "Mainhand") in body.stopped and (look_moves.RETURN_S, "Mainhand") in arms.stopped)
t = 1.0
while moves.frame(int(t * S))[0][0] != look_moves.GONE and t < 3.0:
    t += 1.0 / 60.0
    frame(t)
check("the arm folds all the way, goes out, and its gesture fades", (0.25, "Offhand") in arms.stopped
      and any(at > 1.4 for slot, at in arms.moved if slot == "Offhand"))
check("the body's left hand keeps the pistol until the hook is back", G.busy())
frame(t + 0.1, holding=False)
check("then it lets go, and nothing plays any more", not G.busy() and (0.25, "Offhand") in body.stopped)

moves = look_moves.Moves(0.4, 0.3, 0, 4.0)
arms.played.clear()
body.played.clear()
frame(0.0, kind="PS")
check("a pistol in hand: the pistols' stows",
      vex_fixture.slots(arms)[1] == ("Mainhand", "AS_PS_UnEquip_Offhand")
      and vex_fixture.slots(body)[1] == ("Mainhand", "AS_AG_Body_PS_Stand")
      and abs(arms.played[1]["InTimeToStartMontageAt"] - (0.33333334 - 1.0 / 30.0)) < 1e-6)
G.stop()
moves = look_moves.Moves(0.4, 0.3, 0, 4.0)
arms.played.clear()
body.played.clear()
frame(0.0, kind=None)
check("no weapon in hand: no right arm's gesture",
      [slot for slot, _ in vex_fixture.slots(arms) + vex_fixture.slots(body)]
      == ["Offhand", "Offhand"])
G.stop()
state["anim_instances"] = []
arms_finder.forget()
body.played.clear()
frame(0.1)
check("the arms not found: said once, the body's gestures still played",
      sum("first-person arms were not found" in line for line in state["errors"]) == 1 and len(body.played) == 2)
G.stop()
state["anim_instances"] = [arms]
arms.PlaySlotAnimationAsDynamicMontage = lambda **kwargs: None
try:
    frame(0.2)
    refused = False
except RuntimeError as error:
    refused = "played none of AS_AG_Arms_Left" in str(error)
check("a montage the game refuses is a failure", refused)
del arms.PlaySlotAnimationAsDynamicMontage
G.stop()
vex_fixture.install(state, missing=(G.FLIGHT_PATH,))
moves = look_moves.Moves(0.4, 0.3, 0, 4.0)
moves.catch(0, 1800.0, 600.0, 2500.0)
try:
    frame(0.5)
    missing = False
except look_load.Missing as error:
    missing = error.paths == [G.FLIGHT_PATH]
check("an animation the game does not have is named", missing)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
