"""What one shot did, in one line of the log at its end.

Kevin's first trial of the lock (2026-10-02): "je ressens rien de différent", then "entre le réglage minimum et
maximum je vois pas de différence". The log of that trial showed locks and bounces, and could not say whether an
enemy had been caught beside the aim, how far the aim had strayed from a locked enemy, nor what the settings were.
This line says all three for every shot.
"""

from . import aim, foes, lock, settings
from .slider_values import bounded

_seconds = _under_s = _caught_s = _locked_s = _hidden_s = 0.0
_strayed = 0.0


def begin() -> None:
    global _seconds, _under_s, _caught_s, _locked_s, _hidden_s, _strayed
    _seconds = _under_s = _caught_s = _locked_s = _hidden_s = 0.0
    _strayed = 0.0


def frame(aimed: aim.Aim, first: lock.Target | None, passed: float) -> None:
    global _seconds, _under_s, _caught_s, _locked_s, _hidden_s, _strayed
    _seconds += passed
    if aimed.enemy is not None:
        if aimed.caught:
            _caught_s += passed
        else:
            _under_s += passed
    if aimed.hidden:
        _hidden_s += passed
    if first is not None and first.locked:
        _locked_s += passed
        _strayed = max(_strayed, first.strayed)


def _settings() -> str:
    """The settings the shot was fired with: the window cannot be open during a shot."""
    width = bounded(settings.width)
    locked = (f"lock after {bounded(settings.lock_delay):.2f} s broken at {bounded(settings.lock_angle):.0f} degrees"
              if settings.lock.value is True else "lock off")
    return (f"{f'catch {width:.0f} cm' if width > 0 else 'catch off'}, {locked}, "
            f"bounce {'on' if settings.bounce.value is True else 'off'}")


def line() -> str:
    parts = ["on no enemy"]
    if _under_s or _caught_s:
        parts = [f"on an enemy {_under_s:.2f} s under the aim and {_caught_s:.2f} s caught beside it"]
    if _locked_s:
        parts.append(f"locked {_locked_s:.2f} s, the aim up to {_strayed:.0f} degrees away")
    if _hidden_s:
        parts.append(f"a foe beside the aim hidden {_hidden_s:.2f} s")
    parts.append(f"{foes.known()} foes known")
    parts.append(_settings())
    return f"shot {_seconds:.2f} s: " + "; ".join(parts)
