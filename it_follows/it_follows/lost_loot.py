"""The OPTIONS page's Lost Loot row (decision 146): the Lost Loot machine keeps up to TARGET items, off at first.

Kevin, 19 October 2026: « le mode horde laisse énormément de butin perdu »; 400 (« ce sera 400 »). On, a bonus of
TARGET minus the game's limit is added to the machine's limit (lost_loot_game.py); off, its opposite. Items past the
game's limit stay in the machine when the bonus goes, is taken back, or is gone with a reloaded save (trial 110,
vérifié en jeu): nothing is lost, so turning it off warns of nothing.

A loaded save brings a new player state with no bonus (trial 108): when the game says the character is ready
(READY, the hook Player Movement reapplies its settings on, source unique), a short watch tries once a second, WATCH_S
at most, until the limit can be read, then adds the bonus again. A limit above MOST_GAME is no limit of the game's
(6 plus eight SDU upgrades of 1): another change made it, and it is left alone. Each add stays in the game until it is
relaunched, so they are counted, MAX_ADDS at most a launch. Disabling the mod takes the bonus back.
Not checked in coop: the bonus is added to the local player's own limit only.
"""

from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Type

from . import frame, lost_loot_game as game, options, report

TARGET = 400.0
MOST_GAME = 100.0
MAX_ADDS = 40
READY = "/Script/OakGame.OakPlayerController:ServerNotifyCharacterReadyForGameplay"
READY_ID = "it_follows:lost_loot_ready"
WATCH_ID = "it_follows:lost_loot"
WATCH_S = 30.0
# What a watch waits through: the game still loading the player.
WAITING = ("no_character", "no_player_state", "limit_unread")

_held: dict = {"owner": None, "added": 0.0, "adds": 0}
_hooks: dict = {"ready": None, "watch": None, "until": 0.0}


def wanted() -> bool:
    return options.lost_loot.value is True


def apply(on: bool) -> str:
    """The bonus added or taken back to match on, on the player now loaded; what happened, never raising."""
    try:
        return _apply(on)
    except Exception as error:
        report.error_once(f"lost_loot:{type(error).__name__}",
                          f"Lost Loot limit unchanged: {type(error).__name__}: {str(error)[:120]}")
        return "failed"


def _apply(on: bool) -> str:
    pc = get_pc(possibly_loading=True)
    if pc is None or getattr(pc, "OakCharacter", None) is None:
        return "no_character"
    owner = game.owner(pc)
    if owner is None:
        return "no_player_state"
    if owner != _held["owner"]:
        _held.update(owner=owner, added=0.0)
    added = _held["added"]
    if on == (added != 0.0):
        return "held"
    if _held["adds"] >= MAX_ADDS:
        return "too_many_adds"
    before = game.limit(pc)
    if before is None:
        return "limit_unread"
    if on and not 0.0 < before <= MOST_GAME:
        report.note("lost_loot_left", limit=before)
        return "not_the_game_s"
    delta = TARGET - before if on else -added
    _held["adds"] += 1
    report.note("lost_loot_adding", wanted=on, limit=before, delta=delta)
    outcome = game.add(pc, delta)
    after = game.limit(pc)
    if outcome == game.SUCCESS or (after is not None and abs(after - before - delta) < 0.5):
        _held["added"] = round(added + delta, 4)
    report.note("lost_loot_added", outcome=outcome, limit=after, added=_held["added"], adds=_held["adds"])
    return "raised" if on else "lowered"


def changed(_option: Any, value: Any) -> None:
    """The row switched in the window (mods_base calls this while the mod is enabled)."""
    apply(value is True)


def _tick(moment: float) -> None:
    outcome = apply(wanted())
    if outcome in WAITING and moment < _hooks["until"]:
        return
    if outcome in WAITING:
        report.note("lost_loot_gave_up", outcome=outcome)
    _stop_watch()


def _watch_failed(reason: str) -> None:
    report.note("lost_loot_watch_failed", reason=reason)
    _stop_watch()


def watch() -> None:
    """Tries once a second, WATCH_S at most, until the player is loaded enough to read the limit."""
    _stop_watch()
    beat = frame.Beat(_tick, _watch_failed, identifier=WATCH_ID)
    _hooks.update(watch=beat, until=frame.now() + WATCH_S)
    beat.start()


def _stop_watch() -> None:
    beat, _hooks["watch"] = _hooks["watch"], None
    if beat is not None:
        beat.stop()


def _ready(*_args: Any) -> None:
    if wanted():
        watch()


def start() -> None:
    """The mod enabled: watches for loaded saves, and adds the bonus now if the row is on."""
    if _hooks["ready"] is None:
        _hooks["ready"] = hook(READY, Type.POST, hook_identifier=READY_ID)(_ready)
        _hooks["ready"].enable()
    if wanted():
        watch()


def stop() -> None:
    """The mod disabled: no more watching, and the bonus taken back."""
    active, _hooks["ready"] = _hooks["ready"], None
    if active is not None:
        active.disable()
    _stop_watch()
    apply(False)
