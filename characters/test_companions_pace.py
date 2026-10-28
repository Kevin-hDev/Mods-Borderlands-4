"""Tests trials 138 to 141's pace (pace.py): the bonus raised by FACTOR once, or by the factor chosen on the card,
written again if the game changes it; off, nothing written; the combat run locked while the character walks, with
the game's own stance for the tag and the parameters read in game (trial 137); the combat sprint beyond SPRINT_M
until back within RUN_M, the old lock freed first; a tag the game names no stance for: nothing locked, said; its
combat walk locked while it fights without walking, the run when it is walked back; once it neither walks nor
fights, its passive walk locked then freed; each call said first; everything given back once at the end, a failure
said."""

import pathlib
import sys
import types
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
sys.modules["unrealsdk"].make_struct = lambda name, **fields: types.SimpleNamespace(struct=name, **fields)
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("follow_pace_under_test", HERE / "characters" / "companions" / "pace.py")
pace_module = util.module_from_spec(spec)
spec.loader.exec_module(pace_module)

events: list[str] = []
refuse = {"unlock": False}
unknown: set[str] = set()
walking = types.SimpleNamespace(stance=types.SimpleNamespace(_name="Stance_GunToter_Passive_Walk"))
lemmy = types.SimpleNamespace(CharacterMovement=types.SimpleNamespace(MaxGroundSpeedScale=types.SimpleNamespace(
    Value=1.1)), ReplicatedStance=walking)


class Handle:
    """The game's FGameDataHandle, as trial 138 read it written."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"FGameDataHandle(12, '{self.name}', None)"


def stance_for(tag: object, owner: object) -> tuple:
    events.append(f"for {tag.struct} {tag.TagName} {owner is lemmy}")
    if tag.TagName in unknown:
        return Handle("None"), tag
    return Handle(tag.TagName.replace("stance.", "Stance_").replace(".", "_")), tag


def lock(actor: object, reason: str, block: bool, stance: Handle) -> None:
    events.append(f"lock {actor is lemmy} {reason} {block} {stance.name}")


def unlock(reason: str, owner: object) -> None:
    events.append(f"unlock {reason} {owner is lemmy}")
    if refuse["unlock"]:
        raise RuntimeError("refused")


state["classes"].update({
    "GbxStanceBlueprintLibrary": types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
        GetStanceForTag=stance_for, UnlockStance=unlock)),
    "GbxNavBlueprintLibrary": types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(LockStance=lock))})


def pace(actor: object = lemmy) -> object:
    events.clear()
    return pace_module.Pace(lambda: actor, "Lemmy_1", lambda text: events.append(f"note {text}"))


def calls() -> list[str]:
    return [event for event in events if not event.startswith("note")]


walker = pace()
check("the bonus raised by FACTOR, said first", walker.boost() == "1.1->1.32"
      and abs(lemmy.CharacterMovement.MaxGroundSpeedScale.Value - 1.32) < 1e-9
      and events == ["note about to write MaxGroundSpeedScale 1.32 on Lemmy_1"])
events.clear()
check("not walking, nothing locked: nothing called", walker.keep(False, 40.0, False) == "held" and events == [])
check("walking: his combat run locked, the game's stance for the tag, said first",
      walker.keep(True, 15.0, False) == "locked:Run" and events == [
          "note about to call GetStanceForTag stance.Combat.Run on Lemmy_1", "for GameplayTag stance.Combat.Run True",
          "note about to call LockStance FGameDataHandle(12, 'Stance_Combat_Run', None) on Lemmy_1",
          "lock True Renforts True Stance_Combat_Run"] and walker.locks == 1)
events.clear()
check("between RUN_M and SPRINT_M the run kept", walker.keep(True, 30.0, False) == "held" and events == [])
check("beyond SPRINT_M the combat sprint, the run freed first", walker.keep(True, 30.1, False) == "locked:Sprint"
      and calls() == ["for GameplayTag stance.Combat.Sprint True", "unlock Renforts True",
                      "lock True Renforts True Stance_Combat_Sprint"]
      and events[2] == "note about to call UnlockStance on Lemmy_1")
events.clear()
check("the sprint kept down to RUN_M", walker.keep(True, 20.0, False) == "held" and events == [])
check("within RUN_M the run again", walker.keep(True, 19.9, False) == "locked:Run" and walker.locks == 3)
events.clear()
check("no distance: nothing changed", walker.keep(True, None, False) == "held" and events == [])
lemmy.CharacterMovement.MaxGroundSpeedScale.Value = 1.0
check("the game changed the bonus: written again, said", walker.keep(True, 15.0, False) == "held,boost_again"
      and abs(lemmy.CharacterMovement.MaxGroundSpeedScale.Value - 1.32) < 1e-9
      and events == ["note about to write MaxGroundSpeedScale again on Lemmy_1"])
events.clear()
check("no longer walking: his passive walk locked, then freed", walker.keep(False, 3.0, False) == "rested"
      and calls() == [
      "for GameplayTag stance.Passive.Walk True", "unlock Renforts True",
      "lock True Renforts True Stance_Passive_Walk", "unlock Renforts True"] and walker.locked is None)
events.clear()
check("rested: nothing more", walker.keep(False, 3.0, False) == "held" and events == [])
check("fighting, not walking: his combat walk locked, said first", walker.keep(False, 3.0, True) == "locked:Walk"
      and events == ["note about to call GetStanceForTag stance.Combat.Walk on Lemmy_1",
                     "for GameplayTag stance.Combat.Walk True",
                     "note about to call LockStance FGameDataHandle(12, 'Stance_Combat_Walk', None) on Lemmy_1",
                     "lock True Renforts True Stance_Combat_Walk"])
events.clear()
check("still fighting: kept, nothing called", walker.keep(False, 3.0, True) == "held" and events == [])
check("walked back while fighting: the run, not the combat walk, the walk freed first",
      walker.keep(True, 25.0, True) == "locked:Run" and calls() == [
          "for GameplayTag stance.Combat.Run True", "unlock Renforts True",
          "lock True Renforts True Stance_Combat_Run"])
events.clear()
check("back in the fight: the combat walk again, the run freed first", walker.keep(False, 3.0, True) == "locked:Walk"
      and calls() == ["for GameplayTag stance.Combat.Walk True", "unlock Renforts True",
                      "lock True Renforts True Stance_Combat_Walk"])
events.clear()
check("the fight over: his passive walk locked, then freed", walker.keep(False, 3.0, False) == "rested"
      and calls()[-2:] == ["lock True Renforts True Stance_Passive_Walk", "unlock Renforts True"]
      and walker.locked is None)

unknown.add("stance.Combat.Sprint")
walker.keep(True, 15.0, False)
events.clear()
check("a tag naming no stance: nothing locked, said", walker.keep(True, 40.0, False).startswith(
      "no_stance:Sprint:FGameDataHandle(12, 'None'") and calls() == ["for GameplayTag stance.Combat.Sprint True"]
      and walker.locked == "stance.Combat.Run")
unknown.add("stance.Passive.Walk")
events.clear()
check("no walk to rest in: freed all the same, said",
      walker.keep(False, 3.0, False).startswith("unlocked:no_stance:Walk")
      and calls()[-1] == "unlock Renforts True" and walker.locked is None)
unknown.clear()

walker.keep(True, 15.0, False)
events.clear()
check("given back: rested, the game's bonus written back", walker.put_back() == {
      "stance": "rested", "boost": "restored"} and abs(lemmy.CharacterMovement.MaxGroundSpeedScale.Value - 1.1) < 1e-9
      and events[-1] == "note about to write MaxGroundSpeedScale 1.1 back on Lemmy_1")
events.clear()
check("given back once", walker.put_back() == {"stance": "not_locked", "boost": "not_boosted"} and events == [])

held = [lemmy]
walker = pace_module.Pace(lambda: held[0], "Lemmy_1", lambda text: events.append(f"note {text}"))
walker.keep(True, 15.0, False)
held[0] = None
events.clear()
check("gone with its stance locked: no stance call on no character, said (review of 22 October 2026)",
      walker.put_back()["stance"] == "gone" and calls() == [] and walker.locked is None)

walker = pace()
walker.boost()
walker.keep(True, 15.0, False)
refuse["unlock"] = True
check("a failing unlock said, the bonus still written back", walker.put_back() == {
      "stance": "failed:RuntimeError", "boost": "restored"})
walker.keep(True, 15.0, False)
try:
    walker.keep(False, 3.0, False)
    raised = False
except RuntimeError:
    raised = True
check("a failing unlock in a sample raises, so that the follow ends on it", raised)
refuse["unlock"] = False

lemmy.CharacterMovement.MaxGroundSpeedScale.Value = 1.1
events.clear()
faster = pace_module.Pace(lambda: lemmy, "Lemmy_1", lambda text: events.append(f"note {text}"), 1.3)
check("a factor chosen on the card (+30 %): the bonus raised by it, held by it", faster.boost() == "1.1->1.43"
      and abs(lemmy.CharacterMovement.MaxGroundSpeedScale.Value - 1.43) < 1e-9)
lemmy.CharacterMovement.MaxGroundSpeedScale.Value = 1.0
check("held at its own factor", faster.keep(True, 15.0, False).endswith("boost_again")
      and abs(lemmy.CharacterMovement.MaxGroundSpeedScale.Value - 1.43) < 1e-9)
faster.put_back()
lemmy.CharacterMovement.MaxGroundSpeedScale.Value = 1.1
events.clear()
still = pace_module.Pace(lambda: lemmy, "Lemmy_1", lambda text: events.append(f"note {text}"), 1.0)
check("the bonus off: nothing written, nothing held, nothing given back", still.boost() == "off" and events == []
      and still.keep(False, 3.0, False) == "held" and still.put_back() == {"stance": "not_locked",
                                                                         "boost": "not_boosted"}
      and lemmy.CharacterMovement.MaxGroundSpeedScale.Value == 1.1)

walker = pace(types.SimpleNamespace())
check("no movement to boost: said", walker.boost() == "failed:AttributeError" and walker.base is None)
check("never boosted: nothing written in a sample", walker.keep(False, 3.0, False) == "held")
check("the return value of a call with outputs", pace_module.first(("handle", "tag")) == "handle"
      and pace_module.first("handle") == "handle")
check("the stance a handle names", pace_module.named("FGameDataHandle(12, 'Stance_GunToter_Combat_Run', None)")
      == "Stance_GunToter_Combat_Run" and pace_module.named("FGameDataHandle(0, 'None', None)") is None
      and pace_module.named("FGameDataHandle(0, '', None)") is None and pace_module.named("nothing") is None)
check("the stance read, or None", pace_module.stance_of(lemmy) == "Stance_GunToter_Passive_Walk"
      and pace_module.stance_of(object()) is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
