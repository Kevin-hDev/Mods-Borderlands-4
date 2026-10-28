"""Tests Kevin's rule (guard.py): nothing while at least FEW enemies follow; fewer, nothing before WAIT_S, then a group
of GROUP enemies of the place, written down; none again before SETTLE_S, then again while still short; enough
followers between start the count again; the place's kinds first, else those met last in the run, else nobody asked,
said."""

import sys

import sdk_stubs

sdk_stubs.install()

from it_follows import guard as guard_module  # noqa: E402

fails: list[str] = []
notes: list[dict] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Kinds:
    """zone_kinds.ZoneKinds as the rule reads it: the kinds of the place, and those met last in the run."""

    def __init__(self, place: list[str], run: list[str]) -> None:
        self.place, self.run = place, run

    def around(self, _here: object, knows: object) -> list[str]:
        return [kind for kind in self.place if knows(kind)]

    def latest(self, knows: object) -> list[str]:
        return [kind for kind in self.run if knows(kind)]


def knows(kind: str) -> bool:
    return kind != "Char_Odd"


def note(event: str, **fields: object) -> None:
    notes.append({"event": event, **fields})


HERE = (0.0, 0.0, 0.0)
FEW, WAIT, GROUP, SETTLE = guard_module.FEW, guard_module.WAIT_S, guard_module.GROUP, guard_module.SETTLE_S

try:
    rule = guard_module.Guard(note)
    place = Kinds(["Char_CatAdult", "Char_BatBasic", "Char_Odd"], ["Char_GruntSMG"])
    check("Kevin's numbers: fewer than 2 for 3 s", FEW == 2 and WAIT == 3.0)
    check("enough followers: nothing", rule.group(FEW, 0.0, place, HERE, knows) == []
          and rule.group(FEW, 10.0, place, HERE, knows) == [])
    check("fewer, nothing before WAIT_S", rule.group(1, 20.0, place, HERE, knows) == []
          and rule.group(0, 20.0 + WAIT - 0.1, place, HERE, knows) == [])
    group = rule.group(0, 20.0 + WAIT, place, HERE, knows)
    check("after WAIT_S, a group of GROUP enemies of the place, its kinds taken in turn, those the camps can make",
          len(group) == GROUP and [kind for _name, kind in group[:3]] == ["Char_CatAdult", "Char_BatBasic",
                                                                          "Char_CatAdult"]
          and all(name == "guard_1" for name, _kind in group))
    check("written down: the group, how many followed, how many asked, of the place, its kinds",
          notes[-1] == {"event": "guard", "group": 1, "following": 0, "asked": GROUP, "of": "place",
                        "kinds": ["Char_BatBasic", "Char_CatAdult"]})
    start = 20.0 + WAIT
    check("none again before SETTLE_S, even while still short",
          rule.group(0, start + WAIT, place, HERE, knows) == []
          and rule.group(0, start + SETTLE - 0.1, place, HERE, knows) == [])
    check("then again while still short", len(rule.group(0, start + SETTLE, place, HERE, knows)) == GROUP)
    start += SETTLE
    rule.group(FEW, start + SETTLE + 1.0, place, HERE, knows)
    check("enough followers between: the count starts again", rule.group(1, start + SETTLE + 2.0, place, HERE, knows)
          == [] and len(rule.group(1, start + SETTLE + 2.0 + WAIT, place, HERE, knows)) == GROUP)

    rule = guard_module.Guard(note)
    rule.group(0, 0.0, place, HERE, knows)
    rule.group(FEW, 2.0, place, HERE, knows)
    rule.group(0, 2.5, place, HERE, knows)
    check("short, then enough, then short again: WAIT_S counted from the new shortage",
          rule.group(0, WAIT + 0.1, place, HERE, knows) == []
          and len(rule.group(0, 2.5 + WAIT, place, HERE, knows)) == GROUP)

    rule = guard_module.Guard(note)
    run_only = Kinds([], ["Char_GruntSMG", "Char_SoldierShotgun"])
    rule.group(0, 0.0, run_only, HERE, knows)
    group = rule.group(0, WAIT, run_only, HERE, knows)
    check("none met at the place: the kinds met last in the run", len(group) == GROUP
          and {kind for _name, kind in group} == {"Char_GruntSMG", "Char_SoldierShotgun"} and notes[-1]["of"] == "run")
    rule = guard_module.Guard(note)
    rule.group(0, 0.0, Kinds([], []), HERE, knows)
    check("none met anywhere: nobody asked, said",
          rule.group(0, WAIT, Kinds([], ["Char_Odd"]), HERE, knows) == []
          and notes[-1] == {"event": "guard", "group": 1, "following": 0, "asked": 0, "why": "no_kind"})
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
