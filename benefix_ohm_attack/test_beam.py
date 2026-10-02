"""Tests the beam on screen: found or loaded, put at the hand unlit, aimed, lit, followed, and taken away whole."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import beam, report  # noqa: E402

fails: list[str] = []
HAND, WALL = (10.0, -20.0, 40.0), (510.0, -20.0, 40.0)
FIRE = beam.Effect(sdk_stubs.FIRE_BEAM)


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def lit() -> bool:
    return beam.state() != "no effect"


character = object()
check("nothing is lit at first", not lit())
beam.light(character, FIRE, HAND, WALL)
made = state["beams"][0]
check("the beam is put at the hand, neither lit nor self-destroying",
      state["spawns"] == [(character, "the fire beam", HAND, False, False)])
check("it is turned to the anchor and told the anchor's world spot, then lit",
      made.poses == [(HAND, (0.0, 0.0))] and made.targets == [("User.Target", WALL)] and state["events"] == ["LIT"]
      and made.aimed_when_lit)
check("it is lit", lit())
check("its far end is told as a plain vector", made.positions == [])
check("the log's word on a lit effect: whether the game runs it and how big it draws it",
      beam.state() == "effect active True, radius 2500")
made.active, made.radius = False, 0.0
check("an effect the game has switched off reads as such", beam.state() == "effect active False, radius 0")
made.active, made.radius = True, 2500.0
made.IsActive = lambda: 1 / 0
errors = len(state["errors"])
check("a reading the game refuses is said as unread, the other is still given, and it is no error",
      beam.state() == "effect active unread (ZeroDivisionError), radius 2500" and len(state["errors"]) == errors)
del made.IsActive

beam.follow((10.0, -20.0, 40.0), (10.0, 480.0, 40.0))
check("following moves both ends", made.poses[-1] == (HAND, (0.0, 90.0)) and made.targets[-1][1] == (10.0, 480.0, 40.0))

beam.off()
check("switching off hands it back, puts it out and removes it, in that order",
      made.bAutoDestroy is True and state["events"] == ["LIT", "OFF", "REMOVED"] and not lit())
beam.off()
beam.follow(HAND, WALL)
check("switching off or following nothing does nothing", state["events"] == ["LIT", "OFF", "REMOVED"])
check("with nothing lit there is no effect to tell of", beam.state() == "no effect")

missing = "/Game/Gear/Weapons/_Shared/Effects/Systems/GenericLaser/NS_Beam_Energy_Shock.NS_Beam_Energy_Shock"
beam.light(character, beam.Effect(missing), HAND, WALL)
check("an effect the game does not hold is loaded from its archives",
      state["loads"] == [missing] and state["spawns"][-1][1] == "a loaded beam" and lit())

beam.light(character, FIRE, HAND, WALL)
check("lighting again removes the beam already lit", state["events"].count("REMOVED") == 2 and len(state["beams"]) == 3)

state["beams"][-1].refuses_target = True
errors = len(state["errors"])
beam.follow(HAND, WALL)
check("a beam that stops following is switched off, said once",
      not lit() and state["events"].count("REMOVED") == 3 and len(state["errors"]) == errors + 1)

state["objects"]["lightning"] = "a beam aimed by a position"
beam.light(character, beam.Effect("lightning", position=True), HAND, WALL)
made = state["beams"][-1]
check("a beam whose far end is a position is aimed by that setter, when lit",
      made.positions == [("User.Target", WALL)] and made.targets == [] and made.aimed_when_lit and lit())
beam.follow(HAND, (10.0, 480.0, 40.0))
check("and when followed", made.positions[-1] == ("User.Target", (10.0, 480.0, 40.0)) and made.targets == [])
beam.off()
beams = len(state["beams"])

state["objects"].clear()
sdk_stubs_get =sys.modules["unrealsdk"].find_class("AssetRegistryHelpers").ClassDefaultObject
sdk_stubs_get.GetAsset = lambda data: None
errors = len(state["errors"])
beam.light(character, FIRE, HAND, WALL)
check("an effect that cannot be loaded lights nothing, said once",
      not lit() and len(state["beams"]) == beams and len(state["errors"]) == errors + 1)

state["objects"][sdk_stubs.FIRE_BEAM] = "the fire beam"
state["spawn_gives"] = "tuple"
beam.light(character, FIRE, HAND, WALL)
check("a beam the game hands back in a tuple is taken out of it and lit", lit() and state["events"][-1] == "LIT")
beam.off()
for gives in ("empty", "nothing"):
    report.reset()
    state["spawn_gives"] = gives
    errors = len(state["errors"])
    beam.light(character, FIRE, HAND, WALL)
    check(f"the game handing back {gives}: no beam, said once", not lit() and len(state["errors"]) == errors + 1)
state["spawn_gives"] = "beam"

report.reset()
beam.light(character, FIRE, HAND, WALL)
made = state["beams"][-1]
made.Deactivate = lambda: made.no_such_step
errors, removed = len(state["errors"]), state["events"].count("REMOVED")
beam.off()
check("a step of the switching off that fails is said once and does not stop the next: the beam is still removed",
      made.bAutoDestroy is True and state["events"].count("REMOVED") == removed + 1
      and len(state["errors"]) == errors + 1 and not lit())

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
