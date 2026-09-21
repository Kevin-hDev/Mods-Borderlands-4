"""Binds the grapple key and the jump key through the SDK, so the mod sees each press before the game.

The grapple key is the one the mod must answer for: a press that ends in a grapple is kept from the
game, and a press that does not is handed straight to it, which is how the punch survives.

Jump releases an attached rope. By default that press is consumed so it spends no extra jump;
the next press jumps normally. JumpCurrentCount and JumpMaxCount remain owned by Apex Movement.
During hook flight the jump still belongs to the game.

A blocked press has its release and its repeats blocked too, so the game never sees half a press.
An error in a callback hands the key to the game: a press wrongly passed does what the game does, a
press wrongly blocked makes the game unplayable.
"""

import time
from typing import Any

from mods_base import keybind
from unrealsdk.hooks import Block

from . import control_window, control_config, game, game_grapple, game_target, input_list, report, session, settings
from .control_chords import Chords

PRESSED = "IE_Pressed"
RELEASED = "IE_Released"

_binds: list[Any] = []
_keys: tuple[frozenset[str], frozenset[str]] = (frozenset(), frozenset())
# The keys whose press this mod kept from the game, so its release is kept too. One entry per key held.
_blocked: set[str] = set()
_rope: Any = None
_epoch: Any = None
_active = False
_groups: tuple = ()
_chords = Chords(())
_input_frame_ns = 0


def _event_name(event: Any) -> str:
    return getattr(event, "name", str(event))


def _after_press(key: str, event_name: str) -> Any:
    """What a release or a repeat does: it follows the press it belongs to, blocked or not."""
    blocked = key in _blocked
    if event_name == RELEASED:
        _blocked.discard(key)
    return Block if blocked else None


def _on_grapple(key: str) -> Any:
    epoch = _epoch
    def callback(event: Any) -> Any:
        if not _active or epoch is not _epoch:
            return None
        try:
            if control_window.active():
                return None  # Let the native window receive it without triggering gameplay.
            name = _event_name(event)
            if name != PRESSED:
                _, released = _chords.feed(key, name)
                if released:
                    _rope.key_up(time.perf_counter_ns())
                return _after_press(key, name)
            now_ns = time.perf_counter_ns()
            character = session.refresh(now_ns, _rope, at_once=True)
            if character is None or not _active or epoch is not _epoch:
                _blocked.discard(key)
                return None
            trigger, _ = _chords.feed(key, name)
            if not trigger:
                return _after_press(key, name)
            if game_grapple.ON and game_target.ready():
                # The prototype: the press goes to the game, which grapples to the mod's point. Only
                # when that point is really there — otherwise the mod's own grapple runs as before.
                _blocked.discard(key)
                return None
            if not _rope.fire(character, now_ns):
                _blocked.discard(key)
                return None
            _blocked.add(key)
            if key in control_config.PULSE_KEYS:
                _chords.feed(key, RELEASED)
                _rope.key_up(now_ns)
                _blocked.discard(key)
            return Block
        except Exception:
            _blocked.discard(key)
            session.reset(_rope)
            report.error_once("keys:grapple", "grapple key passed to the game after an error")
            return None

    return callback


def _on_jump(key: str) -> Any:
    epoch = _epoch
    def callback(event: Any) -> Any:
        if not _active or epoch is not _epoch:
            return None
        try:
            if control_window.active():
                return None  # Let the native window receive it without triggering gameplay.
            name = _event_name(event)
            if name != PRESSED:
                return _after_press(key, name)
            now_ns = time.perf_counter_ns()
            character = session.refresh(now_ns, _rope, at_once=True)
            if character is None or not _active or epoch is not _epoch:
                _blocked.discard(key)
                return None
            if _rope.holds:
                # Use the normal release path to preserve momentum and clean up both visuals.
                _rope.let_go("jump pressed", now_ns)
                if bool(settings.block_jump.value):
                    _blocked.add(key)
                    return Block
            return None
        except Exception:
            _blocked.discard(key)
            session.reset(_rope)
            report.error_once("keys:jump", "jump key passed to the game after an error")
            return None

    return callback


def is_bound() -> bool:
    return _active


def matches(mappings: list[Any]) -> bool:
    """The keys bound are still the ones the game lists."""
    return _wanted(mappings) == _keys and control_config.groups(mappings) == _groups


def _wanted(mappings: list[Any]) -> tuple[frozenset[str], frozenset[str]]:
    grapple = frozenset(key for group in control_config.groups(mappings) for key in group)
    # A key that does both is the grapple's: blocking a jump on it would swallow the grapple press.
    return grapple, frozenset(input_list.jump_keys(mappings)) - grapple


def bind(mappings: list[Any], rope: Any) -> bool:
    """Binds every grapple and jump key; False when the game lists no grapple key."""
    global _keys, _rope, _epoch, _active, _groups, _chords
    grapple_keys, jump_keys = _wanted(mappings)
    if _binds:
        unbind()
        if _binds:
            return False
    if not grapple_keys:
        return False
    _rope = rope
    _groups = control_config.groups(mappings)
    _chords = Chords(_groups)
    _epoch = object()
    epoch = _epoch
    # Named after the package, like the frame hook: the SDK binds by key, and the name says which
    # file bound it when two mods hold the same one.
    try:
        for key in sorted(grapple_keys):
            _binds.append(keybind(f"{__package__}:grapple:{key}", key, _on_grapple(key),
                                  is_hidden=True, event_filter=None))
        for key in sorted(jump_keys):
            _binds.append(keybind(f"{__package__}:jump:{key}", key, _on_jump(key), is_hidden=True, event_filter=None))
        for bound in _binds:
            bound.enable()
            if epoch is not _epoch:
                return False
    except Exception:
        unbind()
        raise
    _keys = (grapple_keys, jump_keys)
    _active = True
    report.note(f"keys bound grapple={sorted(grapple_keys)} jump={sorted(jump_keys)}")
    return True


def unbind() -> None:
    global _keys, _rope, _epoch, _active
    # Invalidate callbacks before touching the SDK, including callbacks re-entering during disable.
    _active = False
    _epoch = _rope = None
    _keys = (frozenset(), frozenset())
    _blocked.clear()
    _chords.clear()
    count = len(_binds)
    for bound in tuple(_binds):
        try:
            bound.disable()
        except Exception:
            report.error_once("keys:unbind", "some grapple keys could not be released; release will be retried")
        else:
            _binds.remove(bound)
    if count > len(_binds):
        report.note(f"keys released ({count - len(_binds)})")


def forget_input() -> None:
    """No held chord may survive a possession change or a stopped session."""
    _chords.clear()
    _blocked.clear()


def observe(now_ns: int) -> None:
    """Menus suppress SDK releases; discard incomplete chords after menus or suspended frames."""
    global _input_frame_ns
    gap = _input_frame_ns and now_ns - _input_frame_ns > control_config.INPUT_GAP_NS
    _input_frame_ns = now_ns
    if _chords.down and any(len(group) == 2 for group in _groups):
        if gap or bool(getattr(game.controller(), "bShowMouseCursor", False)):
            # Preserve release ownership for an existing pull, but require a fresh combination.
            _chords.down.clear()
