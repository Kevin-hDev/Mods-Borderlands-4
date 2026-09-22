"""Own only three one-shot sounds; audio faults must never cancel the rope."""

from typing import Any

import unrealsdk

from . import game, report, rope_audio_config as cfg

_handles: list[Any] = []
_owner: Any = None
_phase = "idle"
_broken = False


def _library() -> Any:
    # Never cache engine objects across possession or level changes.
    return unrealsdk.find_class(cfg.LIBRARY).ClassDefaultObject


def _fault() -> None:
    global _broken
    _broken = True
    report.error_once("audio", cfg.ERROR_TEXT)


def stop() -> None:
    global _owner, _phase
    _owner, _phase = None, "idle"
    owned = tuple(_handles)
    _handles.clear()
    for handle in owned:
        try:
            _library().Stop(PlaybackInstance=handle, FadeTime=cfg.FADE_SECONDS)
        except Exception:
            # These events are finite one-shots. Drop expired handles and prevent
            # additional audio until reset; never keep stale references to retry.
            _fault()


def reset() -> None:
    global _broken
    stop()
    _broken = False


def _character() -> Any:
    actor = _owner() if _owner is not None else None
    return actor if actor is not None and actor == game.character() else None


def _play(actor: Any, name: str) -> bool:
    if _broken:
        return False
    try:
        if len(_handles) >= cfg.MAX_HANDLES:
            raise RuntimeError("audio handle budget")
        # Native PostWwiseEventOnActor resolves the symbolic definition. Python
        # construction alone does not resolve it: do not access its fields here.
        definition = unrealsdk.unreal.FGbxDefPtr(name, cfg.EVENT_TYPE)
        event = unrealsdk.make_struct("GbxAudioEvent", bUseSoundTag=False, WwiseEvent=definition)
        optional_switch = unrealsdk.unreal.FGbxDefPtr(cfg.EMPTY_NAME, cfg.SWITCH_TYPE)
        handle = _library().PostWwiseEventOnActor(
            Actor=actor, EmitterTag=cfg.EMPTY_NAME, Event=event, OptionalSwitch=optional_switch)
        if handle is None:
            raise RuntimeError("missing audio handle")
        _handles.append(handle)
        return True
    except Exception:
        _fault()
        stop()
        return False


def start(actor: Any) -> None:
    global _owner, _phase
    stop()
    if _broken:
        return
    try:
        if actor is None or actor != game.character():
            return
        _owner = unrealsdk.unreal.WeakPointer(actor)
        if _play(actor, cfg.SHOT):
            _phase = "flying"
    except Exception:
        _fault()
        stop()


def attach() -> None:
    global _phase
    if _phase != "flying":
        return
    try:
        actor = _character()
        if actor is None:
            stop()
        elif _play(actor, cfg.CONNECT):
            _phase = "connected"
    except Exception:
        _fault()
        stop()


def pull(actor: Any) -> None:
    global _phase
    if _phase != "connected":
        return
    try:
        if actor is None or actor != _character():
            stop()
        elif _play(actor, cfg.PULL):
            _phase = "pulling"
    except Exception:
        _fault()
        stop()
