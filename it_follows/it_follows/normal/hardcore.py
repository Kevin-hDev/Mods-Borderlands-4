"""The Hardcore (decision 89, docs/RUN/spec-hardcore.md): the normal mode's enemies 1 % tougher, and the player taking
1 % more damage, every 100 kills, on top of the level. Kevin, 15 October 2026: « une monter en puissance progressive
et très lente », since the game sets its enemies to the hunter's level and never grows harder.

The one owner of the kills counted, kept from one game launch to the next in a hidden option of the mod's settings
file, which the SDK writes whole (settings_persistence.py). Three states from the page's two switches
(normal/options.py): off, nothing applied and nothing counted, the kills kept; on, the percent applied and the kills
counted; paused, the percent applied and nothing counted (Kevin: « continuer a jouer avec le mod et la difficulté
qu'il aura ajouter sans qu'il ne continue de progresser »). One count for the whole game in this version; one by game
saved in the next.

Written at each step reached, with each status line of the normal mode (every 30 s) and when a game played ends
(normal/play.py), not at each kill: each write rewrites the whole file. A game quit to the desktop never ends its play
(trial 31): it loses only the kills of its last 30 s.

A record of a later version (the next one keeps a count by game saved) is never written over: a player who comes back
to this version counts nothing and keeps it whole for the later one (audit of 15 October 2026).
"""

from mods_base import HiddenOption

from .. import hardcore_steps as steps, report
from . import options

VERSION = 1
# The rule's, shared with the Horde (hardcore_steps.py). Trial 31 used 10 for a while, so that a step showed within
# minutes.
KILLS_PER_STEP = steps.KILLS_PER_STEP
# Ten thousand percent: never reached, the count stops there rather than grow without end.
MOST_KILLS = 1_000_000

# Never written yet: {} reads as no kill.
option = HiddenOption("normal_hardcore_kills", {})
# newer: the file holds a later version's record, left as it is.
_count = {"kills": 0, "saved": 0, "newer": False}


def _read(value: object) -> tuple[int, str | None]:
    """The kills a value of the file holds, and what was wrong with it; 0 for a value that is not one."""
    if value == {}:
        return 0, None
    if not isinstance(value, dict):
        return 0, "not_a_record"
    version = value.get("version")
    if type(version) is int and version > VERSION:
        return 0, "newer_version"
    if version != VERSION:
        return 0, "unknown_version"
    kills = value.get("kills")
    if type(kills) is not int or not 0 <= kills <= MOST_KILLS:
        return 0, "bad_kills"
    return kills, None


def load() -> None:
    """The kills the settings file kept; a value it cannot read counts 0, and the log says why."""
    kills, wrong = _read(option.value)
    _count["kills"] = _count["saved"] = kills
    _count["newer"] = wrong == "newer_version"
    report.note("hardcore_read", kills=kills, percent=percent(), state=state(), **({"wrong": wrong} if wrong else {}))


def kills() -> int:
    return _count["kills"]


def percent() -> int:
    return steps.percent(_count["kills"])


def state() -> str:
    """off, on (applied and counting), or paused (applied, not counting)."""
    if options.hardcore.value is not True:
        return "off"
    return "on" if options.progress.value is not False else "paused"


def factor() -> float:
    """What the enemies' health and the damage the player takes are multiplied by, on top of the level."""
    return 1.0 if state() == "off" else steps.factor(percent())


def count(dead: int) -> int | None:
    """Kills read by the normal mode, counted only while on, and never over a later version's record; the new percent
    when a step is reached, written at once, else None."""
    if dead <= 0 or state() != "on" or _count["newer"]:
        return None
    before = percent()
    _count["kills"] = min(MOST_KILLS, _count["kills"] + dead)
    if percent() == before:
        return None
    save("step")
    return percent()


def save(why: str) -> bool:
    """The kills written in the settings file when they changed since the last write; whether the file has them. A
    write that fails keeps them counted until the game closes, and says so."""
    from .. import mod

    if _count["kills"] == _count["saved"]:
        return True
    option.value = {"version": VERSION, "kills": _count["kills"]}
    try:
        mod.save_settings()
    except Exception as error:
        report.note("hardcore_not_saved", why=why, error=type(error).__name__)
        return False
    _count["saved"] = _count["kills"]
    report.note("hardcore_saved", why=why, kills=_count["kills"], percent=percent())
    return True
