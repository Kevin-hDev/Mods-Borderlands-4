"""Which mod leads the companions' team when several installed mods carry this package (decision 69 of
docs/renforts): one team at a time, never two. Each mod switched on joins; one switched off leaves. The one that
leads joined with first=True (the mod spec-compagnons.md puts first when both are installed); between two of the
same kind, the first by name, whatever the order they joined in, which the game's loading of the mods does not fix.
A team starts only when no other mod leads (team.py), and a team running stops when another mod comes to lead: at
once when that mod's team starts (claim), at its own next beat otherwise.

The state lives in sys.modules under a name of its own, as the camera's runtime (apex_camera_runtime/shared.py):
every copy of this module, one per mod, reads and writes the same one. Reading never creates it. Its name, its
protocol field and its clash flag never change, whatever a later version changes besides (review of 23 October
2026: a name carrying the protocol let a copy of another protocol make a state of its own, and both teams ran).
A copy that finds a state of another protocol raises the clash flag on it: from then on no copy, of either
protocol, says who leads, and no team starts until the game restarts with both mods at the same version.
"""

import re
import sys
from types import ModuleType
from typing import Any, Callable

from .. import report

PROTOCOL = 1
STATE = "_characters_team_owners"
# A mod's package name, as team.OWNER gives it.
_OWNER = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
# Our mods carrying the team are two; a few more leave room without letting the state grow without end.
MOST = 8
# What leads() says beside a state of another protocol, or once two protocols met: no mod may start a team.
UNKNOWN = "unknown"


class Refused(RuntimeError):
    """A state of another protocol is loaded, or the state is full, or the owner's name is no package name."""


def _clash(state: Any) -> None:
    """The flag every copy reads, raised on a state another copy made."""
    try:
        state.clash = True
    except (AttributeError, TypeError):
        pass  # An object that takes no attribute: the Refused raised after says the clash to this copy anyway.


def _state(create: bool) -> ModuleType | None:
    state = sys.modules.get(STATE)
    if state is not None:
        found = getattr(state, "protocol", None)
        if found != PROTOCOL:
            _clash(state)
            raise Refused(f"team owners state of protocol {str(found)[:16]}, this copy's is {PROTOCOL}")
        if type(getattr(state, "owners", None)) is not dict or type(getattr(state, "running", None)) is not dict:
            _clash(state)
            raise Refused("team owners state of a shape this protocol never makes")
        if getattr(state, "clash", False) is True:
            raise Refused("copies of two protocols are loaded")
        return state
    if not create:
        return None
    state = ModuleType(STATE)
    state.protocol = PROTOCOL
    state.clash = False
    # owner -> first, in the order they joined.
    state.owners = {}
    # owner -> what stops its team, while one runs (claim, release): one at most once claims stopped the others.
    state.running = {}
    sys.modules[STATE] = state
    return state


def _checked(owner: object) -> str:
    if type(owner) is not str or not _OWNER.fullmatch(owner):
        raise Refused("invalid team owner")
    return owner


def join(owner: str, first: bool = False) -> None:
    """That mod switched on, leading before those without first."""
    owners = _state(create=True).owners
    if _checked(owner) not in owners and len(owners) >= MOST:
        raise Refused("team owners full")
    owners[owner] = first is True


def leave(owner: str) -> None:
    """That mod switched off."""
    state = _state(create=False)
    if state is not None:
        state.owners.pop(_checked(owner), None)


def leads() -> str | None:
    """The mod that leads the team now, None when no mod joined, UNKNOWN beside a state of another protocol."""
    try:
        state = _state(create=False)
    except Refused:
        return UNKNOWN
    if state is None or not state.owners:
        return None
    return min(state.owners, key=lambda owner: (not state.owners[owner], owner))


def elsewhere(owner: str) -> bool:
    """Whether another mod leads the team, or none can be known to: that mod's team must not run."""
    leader = leads()
    return leader is not None and leader != owner


def _refused(owner: object, error: Refused) -> None:
    """A refusal said, the name given cut to a package name's length: it may be anything."""
    report.note("team_owner_refused", owner=owner[:64] if type(owner) is str else "", why=str(error),
                protocol=PROTOCOL)


def claim(owner: str, stop: Callable[[], Any]) -> list[str]:
    """That mod's team starting, once no other mod leads it (team.py): every other mod's team still running stopped
    first, by the stop it gave, so that two teams never follow the hunter, not even until that team's next beat,
    which a window pausing the game holds back (review of 23 October 2026: the bars' port stayed the other team's);
    then this one's stop kept. The mods stopped; none when the state refuses, said."""
    try:
        running = _state(create=True).running
        _checked(owner)
    except Refused as error:
        _refused(owner, error)
        return []
    stopped = [other for other in running if other != owner]
    for other in stopped:
        stop_other = running.pop(other)
        try:
            stop_other()
        except Exception as error:
            report.note("team_owner_stop_failed", owner=other, error=type(error).__name__)
    running[owner] = stop
    return stopped


def release(owner: str, stop: Callable[[], Any]) -> None:
    """That mod's team stopped: its stop forgotten, if it is still the one kept (a later team of the same mod keeps
    its own)."""
    try:
        state = _state(create=False)
    except Refused:
        return
    if state is not None and state.running.get(owner) is stop:
        del state.running[owner]


def switched_on(owner: str, first: bool = False) -> bool:
    """join for a mod switching on, said with who leads then; whether it joined. A refusal is said, never raised: the
    mod still switches on; beside a state of another protocol, or a full one, its team then does not start."""
    try:
        join(owner, first)
    except Refused as error:
        _refused(owner, error)
        return False
    report.note("team_owner_joined", owner=owner, first=first is True, leads=leads())
    return True


def switched_off(owner: str) -> bool:
    """leave for a mod switching off, said with who leads then; whether it left."""
    try:
        leave(owner)
    except Refused as error:
        _refused(owner, error)
        return False
    report.note("team_owner_left", owner=owner, leads=leads())
    return True


def reset_for_tests() -> None:
    sys.modules.pop(STATE, None)
