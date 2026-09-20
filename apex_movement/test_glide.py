"""Tests the faster glide: the ceiling and its acceleration raised together from the game's own values, written
once, given back on stop, and a field the game would have renamed reported without taking the movement down."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import glide, ownership, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(text: str) -> int:
    return sum(text in line for line in state["misc"])


character = sdk_stubs.FakeCharacter()
movement = character.CharacterMovement
speed, acceleration = movement.GlidingSpeed, movement.GlidingAcceleration

check("the game's own glide is 1200, climbed to at 400 a second",
      (speed.BaseValue, acceleration.BaseValue) == (1200.0, 400.0))

glide.update(character, 0)
check("the default raises the ceiling by 30 %", (speed.BaseValue, speed.Value) == (1560.0, 1560.0))
check("and its acceleration by the same 30 %, so a short glide gains as much",
      (acceleration.BaseValue, acceleration.Value) == (520.0, 520.0))
check("what was written is said once, with the game's own value beside it", notes("glide GlidingSpeed 1560 (game 1200)") == 1)

state["misc"].clear()
glide.update(character, 1)
check("an unchanged setting writes nothing more", notes("glide") == 0 and speed.BaseValue == 1560.0)

settings.glide_speed.value = 200
glide.update(character, 2)
check("a new setting is applied from the game's value, never from the mod's",
      (speed.BaseValue, acceleration.BaseValue) == (2400.0, 800.0))

settings.glide_speed.value = 100
glide.update(character, 3)
check("back at 100 %, the game's own values are in place again",
      (speed.BaseValue, speed.Value, acceleration.BaseValue) == (1200.0, 1200.0, 400.0))

settings.glide_speed.value = 130
glide.update(character, 4)
glide.stop(character)
check("stopping puts the game's values back",
      (speed.BaseValue, speed.Value, acceleration.BaseValue, acceleration.Value) == (1200.0, 1200.0, 400.0, 400.0))
check("and nothing is owned any more", not ownership.is_owned("movement.GlidingSpeed"))

# A level change destroys the character: its values die with it, and the next one is written from its own.
glide.update(character, 5)
glide.stop(character)
ownership.forget_character()
other = sdk_stubs.FakeCharacter()
other.CharacterMovement.GlidingSpeed.BaseValue = other.CharacterMovement.GlidingSpeed.Value = 1000.0
glide.update(other, 6)
check("a new character is raised from its own value", other.CharacterMovement.GlidingSpeed.BaseValue == 1300.0)
glide.stop(other)
ownership.restore_all()

state["errors"].clear()
del movement.GlidingAcceleration
glide.update(character, 7)
glide.update(character, 8)
check("a field the game no longer has is reported once", len([e for e in state["errors"] if "GlidingAcceleration" in e]) == 1)
check("and the other value is still written", movement.GlidingSpeed.BaseValue == 1560.0)
glide.stop(character)
ownership.restore_all()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
