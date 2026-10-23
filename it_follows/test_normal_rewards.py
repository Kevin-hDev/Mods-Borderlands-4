"""Tests the normal mode's rewards (normal/rewards.py, decision 119): each level's shares, experience +10, +15 and +20
%, ammo +10, +20 and +25 %, money +15 %; at the start each share added once on the player, each call written before it
is made, what each multiplier reads after said; taken back by its opposite, read back as the game had it; one add that
fails said, the others kept, and never taken back; a read that fails said, the share kept; the player gone, nothing
called; nothing added, nothing taken back; taken back once only; no definition type or no library, nothing called."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows.normal import levels, rewards  # noqa: E402

XP, AMMO, CASH = (name for name, _field in rewards.ATTRIBUTES)
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class DefPtr:
    def __init__(self, name: str, kind: object) -> None:
        self.name, self.kind = name, kind


class Attributes:
    """The game's library: the multipliers read their gear's value plus the modifiers added on the character."""

    def __init__(self) -> None:
        self.added: list[tuple[str, float]] = []
        self.calls: list[str] = []
        self.refused: set[str] = set()
        self.unread = False
        self.gear = {XP: 1.0, AMMO: 1.0, CASH: 1.1}

    def AddModifierToGbxAttribute(self, attribute: DefPtr, context: object, kind: str, value: float, refresh: bool,
                                  outcome: str) -> tuple:
        self.calls.append(f"add {attribute.name}")
        assert context is hunter and attribute.kind == "GbxAttributeDef" and kind == "PostAdd" and refresh
        if attribute.name in self.refused:
            raise RuntimeError("refused")
        self.added.append((attribute.name, value))
        return 1, attribute, outcome

    def GetValueOfAttribute(self, name: str, context: object, default: float) -> float:
        if self.unread:
            raise RuntimeError("unread")
        return self.gear[name] + sum(value for kind, value in self.added if kind == name)


hunter = object()
typed = [True]
said: list[tuple[str, dict]] = []
adder = types.SimpleNamespace(_find=lambda name: types.SimpleNamespace(Struct="GbxAttributeDef" if typed[0] else None))
state["enums"].update({rewards.KINDS: types.SimpleNamespace(PostAdd="PostAdd"), rewards.OUTCOMES: ["failure"]})
rewards.FGbxDefPtr = DefPtr


def fresh(level: str = "Senior") -> tuple[rewards.Rewards, Attributes]:
    library = Attributes()
    state["classes"][rewards.LIBRARY] = types.SimpleNamespace(ClassDefaultObject=library, _find=lambda name: adder)
    said.clear()
    return rewards.Rewards(levels.LEVELS[level], lambda call, **fields: said.append((call, fields))), library


def column(field: str) -> list:
    return [getattr(levels.LEVELS[name], field) for name in ("Bandit", "Senior", "Predator", "God")]


try:
    check("experience +10, +15, +20 %, God +25 %; ammo +10, +20, +25 %, God +50 %; money +15 %, God +40 % "
          "(decisions 119 and 155)", column("xp") == [0.1, 0.15, 0.2, 0.25]
          and column("ammo") == [0.1, 0.2, 0.25, 0.5] and column("cash") == [0.15, 0.15, 0.15, 0.4])

    given, library = fresh("God")
    check("at God, each share added as the others", given.start(hunter)["shares"] == {XP: 0.25, AMMO: 0.5, CASH: 0.4}
          and library.added == [(XP, 0.25), (AMMO, 0.5), (CASH, 0.4)])

    given, library = fresh()
    started = given.start(hunter)
    check("each share added once, what each reads after said, the gear's money kept under it",
          started == {"shares": {XP: 0.15, AMMO: 0.2, CASH: 0.15},
                      "reads": {XP: 1.15, AMMO: 1.2, CASH: 1.25}} and library.added == [(XP, 0.15), (AMMO, 0.2),
                                                                                        (CASH, 0.15)])
    check("each call written before it is made", [(call, fields["attribute"]) for call, fields in said]
          == [(rewards.ADDER, XP), (rewards.ADDER, AMMO), (rewards.ADDER, CASH)])
    back = given.put_back(hunter)
    check("taken back by its opposite, read back as the game had it", back == {XP: 1.0, AMMO: 1.0, CASH: 1.1}
          and library.added[3:] == [(XP, -0.15), (AMMO, -0.2), (CASH, -0.15)])
    calls = len(library.calls)
    check("taken back once only", given.put_back(hunter) == "none" and len(library.calls) == calls)

    given, library = fresh("Predator")
    library.refused.add(AMMO)
    started = given.start(hunter)
    check("an add that fails said, the others kept", started["reads"] == {XP: 1.2, AMMO: "failed:RuntimeError",
                                                                          CASH: 1.25})
    check("the one that failed never taken back", list(given.put_back(hunter)) == [XP, CASH]
          and library.added[-2:] == [(XP, -0.2), (CASH, -0.15)])

    given, library = fresh("Bandit")
    library.unread = True
    check("a read that fails said, the share kept", given.start(hunter)["reads"] == dict.fromkeys((XP, AMMO, CASH),
                                                                                                  "unread")
          and given.added == {XP: 0.1, AMMO: 0.1, CASH: 0.15})
    library.calls.clear()
    check("the player gone: nothing called, said", given.put_back(None) == "gone" and library.calls == []
          and given.put_back(hunter) == "none")

    given, library = fresh()
    check("nothing added, nothing taken back", given.put_back(hunter) == "none" and library.calls == [])

    typed[0] = False
    given, library = fresh()
    check("no definition type: refused, nothing called", given.start(hunter) == {"refused": "untyped"}
          and library.calls == [] and said == [] and given.put_back(hunter) == "none")
    typed[0] = True

    given, library = fresh()
    del state["classes"][rewards.LIBRARY]
    check("no library: refused, nothing called", given.start(hunter) == {"refused": "no_library:KeyError"}
          and library.calls == [])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
