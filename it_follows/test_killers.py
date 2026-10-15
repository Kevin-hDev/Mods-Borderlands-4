"""Tests who killed an enemy (killers.py): what KillerActor and LastHitBy hold, said as the player (his character, or
his controller), the vehicle he drives, none, unreadable, or the class of what they hold; a kill is the player's when
KillerActor says the player or his vehicle, or says none while LastHitBy says the player; never a spectre's, another
vehicle's, nor one nothing says."""

import pathlib
import sys
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import killers  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def thing(kind: str) -> SimpleNamespace:
    return SimpleNamespace(Class=SimpleNamespace(Name=kind))


class Refusing:
    """A dead body whose fields cannot be read."""

    def __getattr__(self, name: str) -> object:
        raise RuntimeError("no")


try:
    hunter, car = thing("OakCharacter_Player"), thing("OakVehicle_Runner")
    other_car, spectre = thing("OakVehicle_Bandit"), thing("OakCharacter_Spectre")
    pc = SimpleNamespace(Pawn=car)

    def body(killer: object, last_hit: object) -> SimpleNamespace:
        return SimpleNamespace(KillerActor=killer, LastHitBy=last_hit)

    check("killed by his character", killers.killed_by(body(hunter, None), hunter, pc) == ("player", "none"))
    check("last hit by his controller", killers.killed_by(body(None, pc), hunter, pc) == ("none", "player"))
    check("killed by the vehicle he drives", killers.killed_by(body(car, None), hunter, pc) == ("vehicle", "none"))
    check("another vehicle, a spectre: their class", killers.killed_by(body(other_car, spectre), hunter, pc)
          == ("other:OakVehicle_Bandit", "other:OakCharacter_Spectre"))
    check("something without a class", killers.killed_by(body(object(), None), hunter, pc) == ("other:?", "none"))
    check("a body that cannot be read", killers.killed_by(Refusing(), hunter, pc) == ("unreadable", "unreadable"))
    check("no controller: only his character is his", killers.killed_by(body(car, None), hunter, None)
          == ("other:OakVehicle_Runner", "none"))
    check("the class cut short", killers.killed_by(body(thing("X" * 90), None), hunter, pc)[0] == "other:" + "X" * 40)
    check("the player's kills", all(killers.by_player(said) for said in (("player", "none"), ("vehicle", "none"),
                                                                       ("none", "player"), ("player", "other:X"))))
    check("never the rest's", not any(killers.by_player(said) for said in (
        ("other:OakCharacter_Spectre", "player"), ("none", "none"), ("unreadable", "player"),
        ("none", "other:AIController"), ("other:OakVehicle_Bandit", "none"))))
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
