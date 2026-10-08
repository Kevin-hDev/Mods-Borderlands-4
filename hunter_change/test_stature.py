"""The size of the look worn: given whole, the character lifted by the half height gained, the crouched half height
set before the eye heights; kept: given again in the same frame when the game stands the character up with its own,
at most once a frame, never while crouched nor on another character nor once forgotten; given up, said once, when the
game puts its own back more than three times within a second, and taken again by the next wear; a refused step said
once and told; the own size given back, the character lowered to the ground."""

import sys

import sdk_stubs

state = sdk_stubs.install()

import fake_game  # noqa: E402
from fake_game import rule  # noqa: E402
from hunter_change import hunters, report, stature  # noqa: E402

fails: list[str] = []
harlowe, amon = hunters.by_code("Gravitar"), hunters.by_code("Paladin")


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


character = fake_game.load(state, "Gravitar", "8107146506D5906AD9BCCD4479661B4D")
movement = character.CharacterMovement


def recalculated(half: float) -> None:
    """As Unreal does: the crouched eye height worked out again from the class's defaults (2026-10-08)."""
    movement.CrouchedHalfHeight, character.CrouchedEyeHeight = half, 48.4


movement.SetCrouchedHalfHeight = recalculated
check("given whole, lifted by the half height gained, the crouched half height set before the eye heights",
      stature.wear(character, amon) and fake_game.size(character) == fake_game.own_size("Paladin")
      and character.CapsuleComponent.CapsuleRadius == 40.0 and movement.CrouchedHalfHeight == 60.5
      and character.location.Z == 1029.0)

stature.keep(character, 10.0)
check("nothing while the size holds", character.location.Z == 1029.0)
fake_game.stand_up(character)
stature.keep(character, 10.1)
check("given again in the same frame when the game stands the character up, lifted again",
      fake_game.size(character) == fake_game.own_size("Paladin") and character.location.Z == 1058.0)
fake_game.stand_up(character)
stature.keep(character, 10.1 + stature.STEP_S / 2)
check("at most once a frame", character.CapsuleComponent.CapsuleHalfHeight == 86.0)
stature.keep(character, 10.2)
character.bIsCrouched, character.CapsuleComponent.CapsuleHalfHeight = True, 60.5
stature.keep(character, 10.3)
check("never while crouched", character.CapsuleComponent.CapsuleHalfHeight == 60.5)
character.bIsCrouched = False

other = fake_game.load(state, "Gravitar", "8107146506D5906AD9BCCD4479661B4D")
fake_game.stand_up(other)
stature.keep(other, 10.4)
check("never on another character", other.CapsuleComponent.CapsuleHalfHeight == 86.0)

errors = len(state["errors"])
for step in range(5):
    fake_game.stand_up(character)
    stature.keep(character, 20.0 + step * 0.1)
check("given up, said once, past three gives within a second",
      character.CapsuleComponent.CapsuleHalfHeight == 86.0 and len(state["errors"]) == errors + 1
      and "keeps putting the character's own size back" in state["errors"][-1])
fake_game.stand_up(character)
stature.keep(character, 30.0)
check("still given up afterwards", character.CapsuleComponent.CapsuleHalfHeight == 86.0)
stature.wear(character, amon)
fake_game.stand_up(character)
stature.keep(character, 31.0)
check("taken again by the next wear", character.CapsuleComponent.CapsuleHalfHeight == 115.0)

stature.forget()
fake_game.stand_up(character)
stature.keep(character, 32.0)
check("never once forgotten", character.CapsuleComponent.CapsuleHalfHeight == 86.0)

report.reset()
rule["size_refused"] = True
errors = len(state["errors"])
check("a refused step said once and told", not stature.wear(character, amon) and not stature.wear(character, amon)
      and len(state["errors"]) == errors + 1 and "Amon's size was refused at the capsule step" in state["errors"][-1])
rule["size_refused"] = False

stature.wear(character, amon)
lifted = character.location.Z
check("the own size given back, the character lowered to the ground", stature.wear(character, harlowe)
      and fake_game.size(character) == fake_game.own_size("Gravitar") and character.location.Z == lifted - 29.0)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
