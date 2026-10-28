"""Co-op: on the host, puts on each guest's character the Apex values the guest's own game moves it with.

The host replays every move of a guest with the values of that guest's character on the host's machine, lands
somewhere else than the guest did and pulls the guest back, several times a second. Written by a probe on the guest's
character, Apex's gravity, acceleration, air control and glide cut the guest's backward snaps by about four
(docs/coop/2026-10-16-essai-recopie.md, verified in the logs). Each guest gets the host's settings: until the host can
send them, both players need the same Apex settings.

This module owns every value written on a guest's character, as ownership does for the player's own: the game's value
is kept at the first write, put back when no movement wants the field any more or when the mod stops, and forgotten
with the character.
"""

from dataclasses import dataclass
from typing import Any, Callable

import mods_base
import unrealsdk
from unrealsdk import unreal

from . import report

REFRESH_NS = 1_000_000_000
# Borderlands 4 takes four players: the host and three guests. Bounds what is read from the game's player list.
MAX_PLAYERS = 4
# The values written are a gravity scale near 1 and speeds or accelerations up to tens of thousands; 32-bit rounding
# stays far under this on all of them.
TOLERANCE = 0.01
# A line per value written on a guest: they only change with the guest's sprint and the menu, so a flood means the
# game takes a value back every frame, which the first lines still show.
MAX_LINES = 200
# Lines per field of each guest, so that a value written every frame, the slide's speed scale, cannot spend the whole
# bound in two slides as it did on 2026-10-16 (releves/coop/2026-10-17-glissade-echelle-coop).
MAX_FIELD_LINES = 10



@dataclass(frozen=True)
class GuestFrame:
    """What a movement is told of one guest at one frame. `memo` is that guest's own, kept until the guest leaves: a
    movement that follows a guest from frame to frame, such as a slide, keeps its state there under its own name."""

    character: Any
    now_ns: int
    game_value: Callable[[str], Any]
    memo: dict[str, Any]


Wanted = Callable[[GuestFrame], dict[str, Any]]


class _Guest:
    def __init__(self, character: Any) -> None:
        self.pointer = unreal.WeakPointer(character)
        self.name = str(getattr(character, "Name", "?"))
        self.present = True
        # Field of the character movement -> the game's value, kept from the first write.
        self.originals: dict[str, Any] = {}
        # One entry per movement that follows the guest, under the movement's own name: bounded by the movements.
        self.memo: dict[str, Any] = {}
        # Lines said per field, and per field given back: bounded by the fields the movements write.
        self.field_lines: dict[str, int] = {}


_guests: list[_Guest] = []
_next_refresh_ns = 0
_lines = 0


def _read(movement: Any, field: str) -> Any:
    if "." in field:
        # One float of a struct, such as MaxGroundSpeedScale.Value: the game computes it from the rest of the struct,
        # which is left to the game.
        struct, member = field.split(".", 1)
        return float(getattr(getattr(movement, struct), member))
    value = getattr(movement, field)
    if isinstance(value, bool):
        # A switch, such as the host's trust in a climbing guest's place: kept and given back as a switch.
        return value
    if hasattr(value, "BaseValue"):
        # Gearbox's attribute pairs: the game reads Value and refills it from BaseValue, so both travel together.
        return float(value.BaseValue), float(value.Value)
    return float(value)


def _put(movement: Any, field: str, value: Any) -> None:
    if "." in field:
        struct_name, member = field.split(".", 1)
        struct = getattr(movement, struct_name)
        setattr(struct, member, value)
        setattr(movement, struct_name, struct)
    elif isinstance(value, tuple):
        pair = getattr(movement, field)
        pair.BaseValue, pair.Value = value
        # Assigned back whole, glide.py's lesson: a field written on the SDK's copy changes nothing in the game.
        setattr(movement, field, pair)
    else:
        setattr(movement, field, value)


def _differs(found: Any, wanted: Any) -> bool:
    if isinstance(wanted, tuple):
        return any(abs(a - b) > TOLERANCE for a, b in zip(found, wanted))
    return abs(found - wanted) > TOLERANCE


def _say(text: str) -> None:
    global _lines
    if _lines < MAX_LINES:
        _lines += 1
        report.note(text if _lines < MAX_LINES else f"{text} (last co-op line until the mod is switched off and on)")


def _say_field(guest: _Guest, key: str, text: str) -> None:
    said = guest.field_lines.get(key, 0)
    if said >= MAX_FIELD_LINES:
        return
    guest.field_lines[key] = said + 1
    _say(text if said + 1 < MAX_FIELD_LINES else f"{text} (last line for this field)")


def _is_host(player: Any) -> bool:
    return player.GetLocalRole() == unrealsdk.find_enum("ENetRole").ROLE_Authority


def _look(player: Any) -> list[Any]:
    """The guests' characters on foot; none when this game is not the host. A guest in a vehicle is skipped: the
    vehicle moves by its own rules."""
    if not _is_host(player):
        return []
    world = mods_base.ENGINE.GameViewport.World
    game_state = world.GameState if world else None
    if not game_state:
        return []
    found = []
    for player_state in list(game_state.PlayerArray)[:MAX_PLAYERS]:
        pawn = player_state.PawnPrivate
        if not pawn or pawn.IsLocallyControlled():
            continue
        if getattr(pawn, "CharacterMovement", None) is None:
            continue
        found.append(pawn)
    return found


def _follow(found: list[Any]) -> None:
    for guest in [guest for guest in _guests if guest.pointer() is None]:
        # Its values died with it: nothing to put back.
        _guests.remove(guest)
        _say(f"co-op guest {guest.name} gone")
    for guest in _guests:
        guest.present = False
    for character in found:
        guest = next((guest for guest in _guests if guest.pointer() == character), None)
        if guest is None:
            if len(_guests) >= MAX_PLAYERS:
                continue
            guest = _Guest(character)
            _guests.append(guest)
            _say(f"co-op guest {guest.name}: the host applies Apex's values to them")
        guest.present = True


def _apply(guest: _Guest, movement: Any, wanted: dict[str, Any]) -> None:
    for field, value in wanted.items():
        current = _read(movement, field)
        # A switch goes back off, the engine's own value, never as found: Apex Grapple turns the same trust switches on
        # during a guest's rope, and one found on then would be put back on for good.
        guest.originals.setdefault(field, False if isinstance(value, bool) else current)
        if _differs(current, value):
            _put(movement, field, value)
            _say_field(guest, field, f"co-op guest {guest.name}: {field} {value}")
    for field in [field for field in guest.originals if field not in wanted]:
        _put(movement, field, guest.originals.pop(field))
        _say_field(guest, f"{field}:back", f"co-op guest {guest.name}: {field} back to the game's")


def update(player: Any, now_ns: int, wanted_for: Wanted) -> None:
    """Once a frame on the host; `wanted_for` gives the fields each switched-on movement wants on that guest, from
    what a GuestFrame tells of it."""
    global _next_refresh_ns
    if now_ns >= _next_refresh_ns:
        _next_refresh_ns = now_ns + REFRESH_NS
        _follow(_look(player))
    for guest in _guests:
        character = guest.pointer()
        if character is None or not guest.present:
            continue
        movement = character.CharacterMovement

        def game_value(field: str, guest: _Guest = guest, movement: Any = movement) -> Any:
            return guest.originals[field] if field in guest.originals else _read(movement, field)

        _apply(guest, movement, wanted_for(GuestFrame(character, now_ns, game_value, guest.memo)))


def give_back_all() -> list[str]:
    """Puts every guest's values back, then forgets the guests; one line per value that could not be put back."""
    global _next_refresh_ns, _lines
    failures = []
    for guest in _guests:
        character = guest.pointer()
        if character is None:
            continue
        for field, value in guest.originals.items():
            try:
                _put(character.CharacterMovement, field, value)
            except Exception as exc:
                failures.append(f"could not restore {field} on co-op guest {guest.name}: {exc!r}")
    _guests.clear()
    _next_refresh_ns = 0
    _lines = 0
    return failures
