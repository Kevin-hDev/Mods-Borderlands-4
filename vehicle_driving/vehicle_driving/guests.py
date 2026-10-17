"""On a co-op host: every guest's vehicle driven as the guest's own Vehicle Driving drives it, with the host's settings
(Kevin, 2026-10-17: « Ceux de l'hôte », as Apex Movement does for the guests' characters).

The host decides where every vehicle is. Trial 1 of docs/coop/2026-10-17-vehicule-invite.md: the guest's game wrote
Vehicle Driving's values on its vehicle while the host kept the game's own on the same vehicle (verified in game), so
the host drove the guest's path with a slower vehicle, no grip and no push in the air, and pulled the guest back. Here
the host holds each guest's vehicle as frame.py holds the player's own: its values (tuning.py), its grip and its push in
the air, each through the same class, so the two never differ.

A guest's vehicle is one the host has authority on and does not drive itself: on a guest's game, the others' vehicles
are the host's to move, and nothing is found. The guns' damage formula is the game's own, one for every vehicle: the
player's own Tuning alone writes it (levers.targets, with_game).
A failure costs that guest's vehicle alone until its next vehicle, said once.
"""

from typing import Any

import mods_base
import unrealsdk

from . import air_push, grip, report, tuning

# Four players at most in Borderlands 4; the vehicles followed come from other games, so they are bounded anyway.
MAX_GUESTS = 8


class GuestVehicle:
    def __init__(self, vehicle: Any, now_ns: int) -> None:
        self.tuning = tuning.Tuning(with_game=False)
        self.grip = grip.Grip(now_ns)
        self.air = air_push.AirPush(now_ns)
        self.failed = False
        self.name = str(vehicle.Name)
        self.said(self.tuning.take(vehicle))

    def said(self, lines: list[str]) -> None:
        for line in lines:
            report.note(f"co-op guest {self.name}: {line}")


_guests: dict[int, GuestVehicle] = {}


def _authority() -> Any:
    return unrealsdk.find_enum("ENetRole").ROLE_Authority


def guest_vehicles() -> dict[int, Any]:
    """Each guest's vehicle by its PlayerId, on the host only."""
    world = mods_base.ENGINE.GameViewport.World
    game_state = world.GameState if world else None
    if not game_state:
        return {}
    authority = _authority()
    found = {}
    for state in list(game_state.PlayerArray)[:MAX_GUESTS]:
        pawn = state.PawnPrivate
        if (pawn and getattr(pawn, "OakVehicleMovement", None) is not None and not pawn.IsLocallyControlled()
                and pawn.GetLocalRole() == authority):
            found[int(state.PlayerId)] = pawn
    return found


def _drop(player: int) -> None:
    guest = _guests.pop(player)
    for line in guest.tuning.put_back():
        report.error_once(line, f"co-op guest {guest.name}: {line}")
    report.note(f"co-op guest {guest.name}: left the vehicle, game values back")


def tick(now_ns: int, factors: dict[str, float], check: bool, loss: float, push: float, grip_on: bool) -> None:
    """One frame: the values written at each check, as frame.py's, and at once on a vehicle just taken; a guest's
    vehicle changed or left is put back first."""
    found = guest_vehicles()
    for player in [player for player, guest in _guests.items()
                   if found.get(player) is None or found[player] != guest.tuning.vehicle()]:
        _drop(player)
    for player, vehicle in found.items():
        guest = _guests.get(player)
        taken = guest is None
        if taken:
            guest = _guests[player] = GuestVehicle(vehicle, now_ns)
        if guest.failed:
            continue
        try:
            _step(guest, vehicle, now_ns, factors if check or taken else None, loss, push, grip_on)
        except Exception as exc:
            guest.failed = True
            report.error_once(f"guest:{type(exc).__name__}",
                              f"a co-op guest's vehicle stopped being driven until its next vehicle: {exc!r}")


def _step(guest: GuestVehicle, vehicle: Any, now_ns: int, factors: dict[str, float] | None, loss: float, push: float,
          grip_on: bool) -> None:
    if factors is not None:
        guest.said(guest.tuning.update(factors))
    pushed, lines = guest.air.step(now_ns, vehicle, push)
    guest.said(lines)
    # One part sets the vehicle's speed in a frame, as for the player's own (frame.py).
    if not grip_on or pushed:
        guest.grip.rest(now_ns)
    else:
        guest.said(guest.grip.step(now_ns, vehicle, loss))


def stop_all() -> list[str]:
    """Every guest's vehicle given its game values back; one line per value that could not be."""
    lines: list[str] = []
    for guest in _guests.values():
        lines += guest.tuning.put_back()
    _guests.clear()
    return lines
