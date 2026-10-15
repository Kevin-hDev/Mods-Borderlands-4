"""Tests the reads of the game: a text cleaned and cut; a path, or why not; a place, refused when it is not finite or
cannot be read; a distance in metres; a place for the log; a death said only by a bool; a definition read from the
actor's own data, among its first fields only; a zone's radius, or ValueError."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402
from sdk_stubs import FakeStruct, vector  # noqa: E402

state = sdk_stubs.install()

from it_follows import reads  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def raises(error: type) -> object:
    def act(*_args: object) -> object:
        raise error("unreadable")
    return act


def with_definition(name: object, before: int = 0) -> object:
    fields = {f"Field{index}": index for index in range(before)}
    fields["GbxActorDef"] = types.SimpleNamespace(_name=name)
    return types.SimpleNamespace(GbxActorData=FakeStruct(fields))


try:
    check("a text loses its line breaks and is cut", reads.clean("a\r\nb" + "c" * 300) == "ab" + "c" * 198)
    check("a path is read",
          reads.path_of(types.SimpleNamespace(_path_name=lambda: "/Game/Maps/A.B")) == "/Game/Maps/A.B")
    check("an unreadable path says why", reads.path_of(object()) == "? (AttributeError)")

    actor = types.SimpleNamespace(K2_GetActorLocation=lambda: vector(100.0, -200.0, 300.0),
                                  K2_GetComponentLocation=lambda: vector(1.0, 2.0, 3.0))
    check("an actor's place, in cm", reads.point(actor) == (100.0, -200.0, 300.0))
    check("a zone's place, by its own getter", reads.point(actor, "K2_GetComponentLocation") == (1.0, 2.0, 3.0))
    check("a place that is not finite is none",
          reads.point(types.SimpleNamespace(K2_GetActorLocation=lambda: vector(math.nan, 0.0, 0.0))) is None)
    check("a place that cannot be read is none",
          reads.point(types.SimpleNamespace(K2_GetActorLocation=raises(RuntimeError))) is None and
          reads.point(None) is None)
    check("a distance in metres, to 0.1 m", reads.metres((0.0, 0.0, 0.0), (3000.0, 4000.0, 0.0)) == 50.0
          and reads.metres((0.0, 0.0, 0.0), (1234.0, 0.0, 0.0)) == 12.3)
    check("no distance without both places", reads.metres(None, (0.0, 0.0, 0.0)) is None)
    check("a place for the log, in metres", reads.spot((1234.0, -5.0, 100.0)) == [12.3, -0.1, 1.0]
          and reads.spot(None) is None)

    def health(value: object) -> object:
        return types.SimpleNamespace(HealthState=types.SimpleNamespace(bCurrentlyDead=value))

    check("dead and alive, as the game says", reads.dead(health(True)) is True and reads.dead(health(False)) is False)
    check("a death the game does not say with a bool is unknown", reads.dead(health(1)) is None
          and reads.dead(object()) is None)

    def moving(value: object) -> object:
        return types.SimpleNamespace(CharacterMovement=types.SimpleNamespace(MovementMode=value))

    check("a movement mode by its short name", reads.mode(moving("<EMovementMode.MOVE_Swimming: 4>")) == "MOVE_Swimming"
          and reads.mode(moving("<EMovementMode.MOVE_None: 0>")) == "MOVE_None")
    check("no movement mode when none is named or it cannot be read", reads.mode(moving("<odd>")) is None
          and reads.mode(object()) is None)
    check("a definition is read from the actor's own data", reads.definition(with_definition("Char_CatYoung")) ==
          "Char_CatYoung")
    check("a definition past the first fields is not looked for", reads.definition(with_definition("Char_X", 8)) is None
          and reads.definition(with_definition("Char_Y", 7)) == "Char_Y")
    check("an empty definition is none", reads.definition(with_definition("")) is None)
    broken = types.SimpleNamespace(GbxActorData=FakeStruct({"GbxActorDef": RuntimeError("no")}))
    check("a definition that raises is none", reads.definition(broken) is None
          and reads.definition(object()) is None)

    def zone(radius: object) -> object:
        return types.SimpleNamespace(settings=types.SimpleNamespace(
            CombatTerritory=types.SimpleNamespace(Radius=radius)))

    check("a zone's radius, in cm", reads.zone_radius_cm(zone(1500)) == 1500.0)
    for label, target in (("not finite", zone(math.inf)), ("unreadable", object()), ("not a number", zone("x"))):
        try:
            reads.zone_radius_cm(target)
            refused = False
        except ValueError:
            refused = True
        check(f"a radius {label} raises ValueError", refused)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
