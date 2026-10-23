"""Tests trial 140's fight (fight.py): the world's characters read without a line, bounded; the hunter's living
enemy nearest the character, within COMBAT_M of the hunter or of it, by the game's attitude; imposed, said first; kept
while near and alive, imposed again once the game cleared it; a refusal said and tried again; released once it is
dead or far, the next one imposed; calm when none; released at the end, once, a failing clear said."""

import pathlib
import sys
import types
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("follow_fight_under_test", HERE / "it_follows" / "companions" / "fight.py")
fight_module = util.module_from_spec(spec)
spec.loader.exec_module(fight_module)

events: list[str] = []


class Foe:
    def __init__(self, name: str, x: float, hostile: bool = True) -> None:
        self.Name, self.x, self.hostile, self.dead = name, x, hostile, False


read = types.SimpleNamespace(
    dead=lambda foe: foe.dead, place=lambda foe: (foe.x, 0.0, 0.0),
    metres=lambda a, b: None if a is None or b is None else abs(a[0] - b[0]) / 100.0,
    attitude=lambda player, foe: "hostile" if foe.hostile else "friendly")


class Patch:
    def __init__(self, actor: object, foe: object) -> None:
        self.foe, self.applied = foe, False
        self.refuse = targets.refuse
        self.broken = targets.broken

    def read(self) -> str:
        return "player" if self.applied and not targets.cleared else "none"

    def apply(self) -> None:
        events.append(f"apply {self.foe().Name}")
        if self.refuse:
            raise ValueError("Target baseline unavailable")
        self.applied = True
        targets.cleared = False

    def restore(self) -> str:
        events.append("restore")
        if self.broken:
            raise ValueError("Target cleanup not confirmed")
        self.applied = False
        return "restored"


targets = types.SimpleNamespace(imposed=Patch, refuse=False, broken=False, cleared=False)


def fight() -> object:
    events.clear()
    return fight_module.Fight(lambda: "lemmy", "Lemmy_1", lambda text: events.append(f"note {text}"), read, targets,
                              lambda foe: (lambda: None if foe.dead == "gone" else foe))


here, mine = (0.0, 0.0, 0.0), (1000.0, 0.0, 0.0)
near, nearer, friend, far = Foe("Bandit_1", 3000.0), Foe("Bandit_2", 1500.0), Foe("Rush", 1100.0, False), Foe(
    "Bandit_3", 9000.0)
fighter = fight()
check("calm: no enemy near", fighter.keep([friend, far], "player", here, mine) == "calm" and not fighter.fighting
      and events == [])
check("nothing without places", fighter.keep([near], "player", None, mine) == "unknown")
check("the nearest enemy to him imposed, said first", fighter.keep([near, nearer, friend, far], "player", here, mine)
      == "target:Bandit_2" and events == ["note about to call AISetScriptedTarget Bandit_2 on Lemmy_1",
                                          "apply Bandit_2"] and fighter.fighting and fighter.imposed == 1)
events.clear()
check("kept while near and alive", fighter.keep([near, nearer], "player", here, mine) == "fighting:Bandit_2"
      and events == [])
targets.cleared = True
check("cleared by the game: its own cleared first, imposed again", fighter.keep([near, nearer], "player", here, mine)
      == "target:Bandit_2" and events[-3:] == ["restore", "note about to call AISetScriptedTarget Bandit_2 on Lemmy_1",
                                               "apply Bandit_2"] and fighter.imposed == 2)
nearer.dead = True
events.clear()
check("dead: released, the next one imposed", fighter.keep([near, nearer], "player", here, mine) == "target:Bandit_1"
      and events[:2] == ["note about to call AIClearScriptedTarget on Lemmy_1", "restore"])
near.x = 9000.0
events.clear()
check("far: released, calm", fighter.keep([near], "player", here, mine) == "calm:restored" and not fighter.fighting)
check("an enemy COMBAT_M from the hunter, farther from him, counts",
      fighter.keep([Foe("Bandit_4", -3500.0)], "player", here, mine) == "target:Bandit_4")
fighter.release()
check("an enemy beyond COMBAT_M of both: calm",
      fighter.keep([Foe("Bandit_5", -3510.0)], "player", here, mine) == "calm")
check("the nearest to him, not to the hunter", fighter.keep([Foe("Near_hunter", -800.0), Foe("Near_him", 2600.0)],
                                                             "player", here, mine) == "target:Near_him")
fighter.release()

fighter = fight()
targets.refuse = True
foe = Foe("Bandit_6", 2000.0)
check("refused: said, cleared, the enemy kept", fighter.keep([foe], "player", here, mine).startswith(
      "refused:Bandit_6:ValueError") and fighter.fighting and fighter.imposed == 0 and events[-1] == "restore"
      and fighter.patch is None)
targets.refuse = False
check("tried again at the next sample", fighter.keep([foe], "player", here, mine) == "target:Bandit_6"
      and fighter.imposed == 1)
check("released at the end", fighter.release() == "restored" and not fighter.fighting)
check("released once", fighter.release() == "inactive")
targets.broken = True
fighter.keep([foe], "player", here, mine)
check("a failing clear said", fighter.release() == "restore_error:ValueError")
targets.broken = False
fighter = fight()
gone = Foe("Bandit_7", 2000.0)
fighter.keep([gone], "player", here, mine)
gone.dead = "gone"
check("an enemy the game took away: released", fighter.keep([], "player", here, mine) == "calm:restored")

listed = [Foe(f"Bandit_{number}", 0.0) for number in range(1200)]


def all_of(WorldContextObject: object, ActorClass: object, OutActors: list) -> tuple:
    asked = WorldContextObject == "pc" and ActorClass == "OakCharacterClass"
    return None, iter(listed) if asked else iter([])


state["classes"].update({"OakCharacter": "OakCharacterClass", "GameplayStatics": types.SimpleNamespace(
    ClassDefaultObject=types.SimpleNamespace(GetAllActorsOfClass=all_of))})
found = fight_module.characters("pc")
check("the world's characters, bounded, without a line", len(found) == 1000 and found[0] is listed[0]
      and state["info"] == [])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
