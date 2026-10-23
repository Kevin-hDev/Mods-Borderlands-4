"""The companions' health bars at the bottom left of the screen (decision 36 of docs/renforts/README.md, Kevin, 21
October 2026: « afficher leur barres de vies en jeu par dessus l'HUD a gauche de l'ecran [...] comme en coop pour le
coequipier , que ce soit desactiver par defaut »), drawn by the game's own co-op teammates' block, in green
(trials 178 and 179, validated by Kevin), the names in the game's language (trial 182, bars_names.py). A dead one
on its way back shows a full red bar (decision 51, Kevin, trial 191: an empty one « on pense qu'il est toujours la »).

Shown or not by an option of the mod's window, off at first, offered only while the bars' package lies in the game's
Paks folder (decision 48: delivered apart, detected; without it the option would show and do nothing): the mod owns
the option and hands in how to read it (start). Python never touches the
game's screen (docs/candidats/HUD/ERREURS.md, 9: both tries crashed the game): the package's script asks a loopback
service for the team (bars_service.py), about four times a second.

The same service tells the aimed bar's page which Vault Hunter is aimed at (aimed.py, decisions 49 and 53), so it
runs with the team whenever either package lies in Paks; the option only shows the bars or hides them.

While the team is on: every EVERY_S of the team's beat, each companion it follows, rank by rank, its health and its
shield; then each one dead and on its way back, marked dead, so that the player sees who died (Kevin, trial 189:
« sans les barres de vies a gauche c'est compiquer de surveiller qui meurt »); whether the bars are shown; the hunter
aimed at. A publish that fails stops the service, said; the team goes on.
"""

import json
import re
from pathlib import Path
from typing import Any, Callable

from mods_base import get_pc

from .. import report
from . import aimed, bars_names, bars_service, bars_wire, kinds

CONSTANTS = "companion_bars.json"
# A package's name as the game finds it in Paks, never a path: it is read from a file.
PACKAGE_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,80}_P\.pak$")
EVERY_S = 0.25
MAX_TEXT = 120


def paks(here: Path = Path(__file__)) -> Path | None:
    """The game's Paks folder, found from where the mod lies (<game>/sdk_mods/...); None when it is not there."""
    for folder in here.parents:
        if folder.name.lower() == "sdk_mods":
            return folder.parent / "OakGame" / "Content" / "Paks"
    return None


def packages(read: Callable[[str], str] = bars_names.read_asset) -> dict[str, str]:
    """The two packages' names, the bars' and the aimed bar's, from assets/companion_bars.json: their one authority,
    which the tools that build them read too (docs/renforts/sondes/companion_bars and nameplate_trial). Empty when
    unread, or when one is no package's name."""
    try:
        constants = json.loads(read(CONSTANTS))
        found = {"bars": constants["barsPak"], "names": constants["namesPak"]}
    except (OSError, ValueError, KeyError, TypeError):
        return {}
    return found if all(isinstance(name, str) and PACKAGE_NAME.match(name) for name in found.values()) else {}


def installed(here: Path = Path(__file__), which: str = "bars",
              read: Callable[[str], str] = bars_names.read_asset) -> bool:
    """Whether that package, the bars' unless said, lies in the game's Paks folder."""
    pak, folder = packages(read).get(which), paks(here)
    try:
        return pak is not None and folder is not None and (folder / pak).is_file()
    except OSError:
        return False


def rows(follows: list, waiting: list, names: dict) -> list[tuple]:
    """(name shown, health, shield, dead) of each companion followed, rank by rank, then of each dead one on its way
    back, its health empty; kinds.MOST at most."""
    living = [(names.get(one.companion, one.companion), one.tough.health(), one.tough.shield_share(), False)
              for one in sorted(follows, key=lambda one: one.rank)]
    dead = [(names.get(one["companion"], one["companion"]), 0.0, None, True) for one in waiting
            if one["after_s"] > 0.0]
    return (living + dead)[:kinds.MOST]


class Bars:
    """The service and what it publishes for one team: service bars_service.CompanionBars, started; names the names
    shown (bars_names.shown); clock() the team's time; shown() whether the mod's option shows the bars; pc() the
    player's controller."""

    def __init__(self, service: Any, names: dict, clock: Callable[[], float], shown: Callable[[], bool],
                 pc: Callable[[], Any] = get_pc) -> None:
        self.service, self.names, self.clock, self.shown, self.pc = service, names, clock, shown, pc
        self.aimed = aimed.Aimed(clock)
        self.next_at = clock()
        self.published = 0
        self.done: str | None = None

    def beat(self, team: Any) -> None:
        if self.done is not None or self.clock() < self.next_at:
            return
        self.next_at = self.clock() + EVERY_S
        try:
            follows = team.active()
            self.service.publish(rows(follows, team.respawns.waiting, self.names), self.shown() is True,
                                 self.aimed.look(self.pc(), follows, self.names))
        except Exception as error:
            self.stop(f"failed:{type(error).__name__}:{str(error)[:MAX_TEXT]}")
            return
        self.published += 1

    def stop(self, why: str) -> None:
        if self.done is not None:
            return
        self.done = why
        stopped = self.service.stop()
        report.note("companion_bars_stop", why=why, published=self.published, asked=self.service.asked,
                    stopped=stopped)


def _said(sentence: str) -> None:
    report.note("companion_bars_said", said=sentence)


def start(clock: Callable[[], float], shown: Callable[[], bool], read: Callable[[str], str] = bars_names.read_asset,
          here: Path = Path(__file__)) -> Bars | None:
    """The service for a team, when either package is installed: started, the names read in the game's language,
    the bars shown while shown() says so; None, and why said, otherwise."""
    try:
        constants = json.loads(read(CONSTANTS))
    except (OSError, ValueError, TypeError) as error:
        report.note("companion_bars_off", why=f"failed:{type(error).__name__}")
        return None
    bars_pak, names_pak = installed(here, "bars", read), installed(here, "names", read)
    if not bars_pak and not names_pak:
        report.note("companion_bars_off", why="no_package")
        return None
    try:
        service = bars_service.CompanionBars(bars_wire, constants, _said)
        if not service.start():
            report.note("companion_bars_off", why="no_port")
            return None
    except (OSError, ValueError, KeyError, TypeError) as error:
        report.note("companion_bars_off", why=f"failed:{type(error).__name__}")
        return None
    language, how = bars_names.culture()
    names, source = bars_names.shown(language, read)
    report.note("companion_bars_start", port=service.port(), every_s=EVERY_S, culture=language, culture_read=how,
                names=source, bars=bars_pak, names_pak=names_pak)
    return Bars(service, names, clock, shown)
