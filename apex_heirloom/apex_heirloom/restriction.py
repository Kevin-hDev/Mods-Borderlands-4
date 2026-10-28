"""Keeps the weapon away when the game lifts a weapon restriction that began with no weapon in hand.

Why, Kevin, 2026-09-25: "si j'entre dans le véhicule arme rangée, quand je ressors je ressors avec l'arme sortie".
Verified in game the same day (docs/investigations/tidy_weapons/2026-09-25-arme-rendue-a-la-descente-de-vehicule.md):
getting in, the game calls the character's WeaponRestrictionChanged with True; getting out, with False, 70 ms after the
exit and 3 ms before it gives the weapon back, with no other weapon function between. So the False call is kept from
running when the restriction began with the hand empty, the weapon then stays away. With a weapon in hand at the start,
the game gives it back as it always did. With the holster off (parts.py), the game always gives it back.

Skipping it takes nothing else away, seen by Kevin in game the same day: "la sortie du véhicule rend bien tout à la
sortie, grenade, grappin, attaque de mêlée fonctionne toujours et ne rend pas l'arme". But the call also clears the
character's bWeaponsRestricted, and nothing else does short of a fast travel: Kevin could no longer draw his weapon
after such a ride (2026-09-26, cosmetics/heirloom/docs/enquetes/2026-09-26-arme-bloquee-apres-vehicule.md). Cleared
with the skipped call, the game gave the weapon back by itself 1.2 s later (four rides, within 0.03 s); cleared 3 s
later by a probe, it stayed away until Kevin drew it (verified in game). That moment is when the camera, flying back
from behind the character after the exit, reaches the eyes (sondes/apex_exit_camera_watch.py, same day). So the flag is
cleared once the camera has been in the eyes EYES_FOR_S, and at once when the holster stops, so that no weapon stays
out of reach. A fixed wait of 2 s came first; Kevin: "c'est trop visible, ça ressemble juste à un bug". A press of a
weapon key before that clears it at once (draw_keys.py): the game then draws the weapon the player asks for.
"""

import time
from dataclasses import dataclass
from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Block, Type

from . import apex_camera_view as camera_view
from . import draw_keys, keys, report

RESTRICTION = "/Script/OakGame.OakCharacter:WeaponRestrictionChanged"
NO_WEAPON, GOING_AWAY, WEAPON = "no weapon in hand", "the weapon being put away", "a weapon in hand"
# The camera reaches the eyes 1.17 s after the lift, and the game gives the weapon back 1.18 to 1.21 s after it (two
# sessions, déduction): past it, a draw is the player's own. The game draws a weapon with no call a mod sees, so the
# player's own draw cannot be told apart from it sooner.
EYES_FOR_S = 0.15
# In third person the camera never comes to the eyes: past the game's own return, as measured in first person.
THIRD_PERSON_AFTER_S = 1.4
# Whatever the camera does, the weapons are never left out of reach longer.
AT_MOST_S = 5.0
clock = time.perf_counter


@dataclass
class _Held:
    """The player's character whose restriction flag a skipped lift left set, by name; when; and since when the camera
    looks through its eyes, None while it does not."""
    name: str
    lifted_at: float
    eyes_since: float | None = None
    # Whether the player's weapon keys were bound for it: tried once, even when the SDK refused them.
    keys_tried: bool = False


# The player's character under a weapon restriction, by name, and whether it began with the hand empty; None outside
# one. No game object is held.
_restriction: tuple[str, bool] | None = None
# None when no flag waits.
_held: _Held | None = None


def _is_player(character: Any) -> bool:
    pc = get_pc(possibly_loading=True)
    return pc is not None and character is not None and (
        character == getattr(pc, "Pawn", None) or character == getattr(pc, "OakCharacter", None))


def _hand(character: Any) -> str:
    weapon = character.ActiveWeapons.Slots[0].Weapon
    if weapon is None:
        return NO_WEAPON
    # Put away by a key just before getting in, the weapon is still going down (0.46 to 0.6 s, holster.GOING_DOWN_S):
    # the hand is as good as empty.
    return GOING_AWAY if keys.going_down(weapon) else WEAPON


def restricted(character: Any, restricted_now: bool) -> bool:
    """Follows one restriction change of `character`; True when the game must not run it, the weapon staying away."""
    global _restriction, _held
    name = str(character.Name)
    if restricted_now:
        if not _is_player(character):
            return False
        hand = _hand(character)
        # Each change decides from the hand, as in the version seen in game. A second change within one restriction was
        # never seen (one True and one False per trip in every log of 2026-09-25): if it comes, the log says "again".
        # Keeping the first decision instead would let a lift gone unseen give the weapon back on a later trip (review
        # of the audit's fixes, 2026-09-25).
        again = _restriction is not None and _restriction[0] == name
        _restriction, _held = (name, hand != WEAPON), None
        report.note(f"weapons restricted{' again' if again else ''} with {hand}")
        return False
    if _restriction is None or _restriction[0] != name:
        return False
    empty = _restriction[1]
    _restriction = None
    if empty:
        # Written to the value it holds: a flag that cannot be written raises here, and the game then runs its lift.
        character.bWeaponsRestricted = True
        _held = _Held(name, clock())
        report.note("weapons back: the game's draw skipped, the weapon stays away")
    return empty


def _player() -> Any:
    pc = get_pc(possibly_loading=True)
    return pc, getattr(pc, "OakCharacter", None) if pc is not None else None


def _release(character: Any, why: str) -> None:
    global _held
    _held = None
    character.bWeaponsRestricted = False
    report.note(f"weapons usable again, {why}")


def _why_now(held: _Held, pc: Any, character: Any, arms_animation: Any, now: float) -> str:
    """Why the flag can be cleared now, "" while it stays."""
    where = camera_view.outside(pc.PlayerCameraManager, character, arms_animation, report.note)
    if where:
        held.eyes_since = None
    elif held.eyes_since is None:
        held.eyes_since = now
    if held.eyes_since is not None and now - held.eyes_since >= EYES_FOR_S:
        return "the camera in the eyes"
    waited = now - held.lifted_at
    if camera_view.third_person(where) and waited >= THIRD_PERSON_AFTER_S:
        return "in third person"
    return "the camera still away" if waited >= AT_MOST_S else ""


def asked() -> None:
    """A weapon key pressed while the flag waits: cleared at once, before the game reads the press."""
    if _held is None:
        return
    _, character = _player()
    if character is not None and str(character.Name) == _held.name:
        _release(character, "the player asking for a weapon")


def _listen() -> None:
    try:
        draw_keys.listen(asked)
    except Exception as exc:
        report.error_once("restriction:keys",
                          f"weapon keys not listened after an error, the camera alone gives the weapons back: {exc!r}")


def tick(arms_animation: Any) -> None:
    """At each frame of first-person arms: the flag a skipped lift left set cleared once the player stands in his
    character again and his camera is back in his eyes, the player's weapon keys listened to meanwhile; forgotten for
    another character, whose flag is its own."""
    global _held
    if _held is None:
        # Let go at a frame, not from the press that cleared the flag: the SDK may still be running it.
        draw_keys.stop()
        return
    try:
        pc, character = _player()
        # No character yet is still getting out (the controller has none while riding): forgotten then, the flag
        # would stay set until a fast travel.
        if character is None:
            return
        if str(character.Name) != _held.name:
            _held = None
        elif getattr(pc, "Pawn", None) == character and getattr(arms_animation, "OakCharacter", None) == character:
            if not _held.keys_tried:
                _held.keys_tried = True
                _listen()
            why = _why_now(_held, pc, character, arms_animation, clock())
            if why:
                _release(character, why)
    except Exception as exc:
        _held = None
        report.error_once("restriction:clear", f"weapons left restricted after an error: {exc!r}")


def forget() -> None:
    """The restriction followed forgotten (the holster stops or starts); a flag left set is cleared now."""
    global _restriction, _held
    _restriction = None
    draw_keys.stop()
    if _held is None:
        return
    try:
        _, character = _player()
        if character is not None and str(character.Name) == _held.name:
            _release(character, "the holster stopping")
    except Exception as exc:
        report.error_once("restriction:clear", f"weapons left restricted after an error: {exc!r}")
    _held = None


@hook(RESTRICTION, Type.PRE)
def on_restriction(obj: Any, args: Any, _ret: Any, _func: Any) -> Any:
    if not keys.running():
        return None
    try:
        return Block if restricted(obj, bool(args.bRestricted)) else None
    except Exception as exc:
        # Letting the game run its own change is what it would do without the mod: the weapon comes back, nothing breaks.
        report.error_once("restriction", f"weapon restriction left to the game after an error: {exc!r}")
        return None
