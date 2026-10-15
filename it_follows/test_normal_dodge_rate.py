"""Tests the level's dodges (normal/dodge_rate.py) on a real block of memory (param_fixture.py): a family's file opened
once, its conditions, tickets and distances opened, its chance set, its rests divided by 20, IsMovingSpeed raised for
Predator only; the copy of an enemy born before brought to the file, that of one born after left as it holds them
already; both given back to the game's values; the file given back, its own tickets too; a file the game dropped owes
nothing; a value refused leaves the others written; past MAX_FAMILIES and without dodges, nothing."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

import param_fixture as fx  # noqa: E402
from it_follows import gbx_param  # noqa: E402
from it_follows.normal import dodge_rate, levels  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def value(holder: object, key: str) -> object:
    return gbx_param.read(*dodge_rate._part(holder, key))[1]


def hidden(holder: object) -> dict:
    keys = [f"{entry}.Chance" for entry in dodge_rate.ENTRIES]
    keys += [f"{entry}.cooldown" for entry in dodge_rate.ALL_ENTRIES] + ["CombatStartedWarmup", "IsMovingSpeed"]
    return {key: value(holder, key) for key in keys}


def conditions(holder: object) -> dict:
    return {(entry, field): getattr(getattr(holder, entry), field) for entry in dodge_rate.ALL_ENTRIES
            for field, _ in dodge_rate._changes(entry)}


GAME = {**{f"{entry}.Chance": 0.15 for entry in dodge_rate.ENTRIES},
        **{f"{entry}.cooldown": [8.0, 2.0] for entry in dodge_rate.ENTRIES},
        "DodgeRandom.cooldown": 4.0, "CombatStartedWarmup": 2.0, "IsMovingSpeed": 10.0}
BANDIT = {**{f"{entry}.Chance": 0.35 for entry in dodge_rate.ENTRIES},
          **{f"{entry}.cooldown": [0.4, 0.1] for entry in dodge_rate.ENTRIES},
          "DodgeRandom.cooldown": 0.2, "CombatStartedWarmup": 0.1, "IsMovingSpeed": 10.0}
OPEN = {(entry, field): opened for entry in dodge_rate.ALL_ENTRIES for field, opened in dodge_rate._changes(entry)}

try:
    lines: list[tuple[str, dict]] = []
    calls: list[tuple[str, dict]] = []
    memory = fx.Memory()
    human = fx.dodge_file(memory, "DodgeData_Human")
    game_conditions = conditions(human)
    before = fx.enemy(memory, "Char_GunToterSMG_Male", 12.0, human)
    dodges = dodge_rate.Dodges(levels.LEVELS["Bandit"], lambda event, **f: lines.append((event, f)),
                               lambda call, log=True, **f: calls.append((call, f)))
    check("the family named", dodges.meet(before) == "DodgeData_Human")
    check("its file written: chance 0.35, rests divided by 20, IsMovingSpeed kept", hidden(human) == BANDIT)
    check("its conditions opened, the tickets off, the file's own too",
          conditions(human) == OPEN and human.bUseTicketSettings is False)
    check("the file announced, then said opened: 27 conditions of the three dodges, 2 tickets more, 8 values",
          calls == [("AIDodgeData", {"family": "DodgeData_Human"})]
          and lines == [("normal_dodges_opened", {"family": "DodgeData_Human", "opened": 29, "written": 8,
                                                  "refused": {}})])
    check("the copy of the enemy born before brought to the file",
          hidden(before.AIDodgeState) == BANDIT and conditions(before.AIDodgeState) == OPEN)
    after = fx.enemy(memory, "Char_GunToterSMG_Female", 20.0, human)
    tally = dodge_rate._bring(dodges.files["DodgeData_Human"], after.AIDodgeState, back=False)
    check("the copy of one born after holds the file already: nothing written", tally == {"already": 8})
    dodges.meet(after)
    check("met, the file is not opened again", len(calls) == 1 and len(lines) == 1)
    check("given back: the copy written before, and the one born after",
          dodges.give_back(before) == {"written": 8} and dodges.give_back(after) == {"written": 8}
          and hidden(before.AIDodgeState) == GAME and hidden(after.AIDodgeState) == GAME
          and conditions(after.AIDodgeState) == game_conditions)
    check("given back twice: already", dodges.give_back(before) == {"already": 8})
    own = fx.enemy(memory, "Char_GunToterPistol_Female", 25.0, human)
    own.AIDodgeState.DodgeBullet.MaxDistance = 500.0
    dodges.meet(own)
    kept = own.AIDodgeState.DodgeBullet.MaxDistance
    dodges.give_back(own)
    check("a condition the game set otherwise in a copy is left, brought and given back",
          kept == 500.0 and own.AIDodgeState.DodgeBullet.MaxDistance == 500.0
          and own.AIDodgeState.DodgeBullet.bLimitAngle is True)
    stopped = dodges.stop()
    check("the file given back, its own tickets too", stopped == {"families": 1, "gone": 0, "written": 8}
          and hidden(human) == GAME and conditions(human) == game_conditions and human.bUseTicketSettings is True
          and dodges.files == {})

    predator = dodge_rate.Dodges(levels.LEVELS["Predator"], lambda event, **f: None, lambda call, log=True, **f: None)
    cat = fx.dodge_file(memory, "DodgeData_Cat", chance=1.0)
    predator.meet(fx.enemy(memory, "Char_CatAdult", 30.0, cat))
    check("Predator: chance 0.55, IsMovingSpeed x100", value(cat, "DodgeBullet.Chance") == 0.55
          and value(cat, "IsMovingSpeed") == 1000.0)
    cat._values["freed"] = True
    check("a file the game dropped owes nothing", predator.stop() == {"families": 1, "gone": 1})

    lines.clear()
    odd = fx.build(memory, "AIDodgeData", {**fx.dodge_fields(0.15), "bUseTicketSettings": True}, name="DodgeData_Odd")
    memory.put(odd.DodgeZone.Chance._get_address(), fx.param(single=0.15, pointer=0x2000))
    bandit = dodge_rate.Dodges(levels.LEVELS["Bandit"], lambda event, **f: lines.append((event, f)),
                               lambda call, log=True, **f: None)
    bandit.meet(fx.enemy(memory, "Char_Odd", 5.0, odd))
    check("a value not in place refused, the others written", lines[0][1]["refused"] == {"DodgeZone.Chance": "kind:3"}
          and lines[0][1]["written"] == 7 and value(odd, "DodgeBullet.Chance") == 0.35)
    bandit.stop()

    check("room for the game's some 60 families", dodge_rate.MAX_FAMILIES >= 60)
    kept_most, dodge_rate.MAX_FAMILIES = dodge_rate.MAX_FAMILIES, 4
    many = dodge_rate.Dodges(levels.LEVELS["Bandit"], lambda event, **f: None, lambda call, log=True, **f: None)
    for number in range(dodge_rate.MAX_FAMILIES):
        family = fx.dodge_file(memory, f"DodgeData_{number}")
        many.meet(fx.enemy(memory, f"Char_{number}", 5.0, family))
    last = fx.dodge_file(memory, "DodgeData_Last")
    check("past MAX_FAMILIES, a new family is left to the game",
          many.meet(fx.enemy(memory, "Char_Last", 5.0, last)) is None and value(last, "DodgeBullet.Chance") == 0.15)
    dodge_rate.MAX_FAMILIES = kept_most
    check("an enemy without dodges: nothing", many.meet(type("Pawn", (), {"AIDodgeState": type(
        "State", (), {"CurrentDodgeData": None})()})()) is None)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
