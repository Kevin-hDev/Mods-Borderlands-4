"""The normal mode's settings as the window's NORMAL MODE page shows them (menu.py): the level, Bandit at first, and
the allied enemies, off at first (Kevin, 15 October 2026: the mode is there to play normally). Whether the mode is on
is kept in the settings file too, hidden: on, it stays on from one game launch to the next until STOP (decision 80).
A value the file holds that is no choice reads as the default.

The Hardcore's two switches (decision 89, spec-hardcore.md) sit on the same page, in a card of their own that the mode
on never locks: Kevin wants it switched off « a tous moment si le joueur trouve que ca devient trop difficile ». Off
at first, its progress on at first; normal/hardcore.py reads them.

The faster dodges can be switched off, on at first (Kevin, 15 October 2026: « pour l'accélération des esquives, je
penses qu'on va l'ajouter dans les options du mode normal pour que le joueur puisse le désactiver, il reste activer
par défaut »): off, the enemies dodge at the game's own speed, their chance and rest still the level's.

The shields (decisions 111 and 112) can be switched off at Bandit only, on at first (Kevin: « bandit affiche l'option
quand on clic dessus mais senior et predator n'ont pas l'option, les shield sont obligatoire pour jouer a ces deux
modes la »): the page shows the row at Bandit only, and the other levels give the shields whatever it holds.

The enemies' speed (decision 121), INCREASED at first, the level's own; REDUCED, its run and faster dodges slower
(levels.reduced), for those who find them too fast. The page shows the row at Senior and Predator only, and Bandit
keeps its speed whatever it holds."""

from dataclasses import dataclass

from mods_base import BoolOption, SpinnerOption

from . import levels

level = SpinnerOption("normal_level", levels.DEFAULT, list(levels.LEVELS), display_name="Level",
                      description="How hard the game's enemies are made.")
allies = BoolOption("normal_allies", False, display_name="Allied enemies",
                    description="All the enemies in one team: they no longer fight each other.")
hardcore = BoolOption("normal_hardcore", False, display_name="Hardcore",
                      description="The enemies grow stronger as you kill, slowly, all game long.")
progress = BoolOption("normal_hardcore_progress", True, display_name="Progress",
                      description="Off: the difficulty reached stays as it is, without rising.")
fast_dodges = BoolOption("normal_fast_dodges", True, display_name="Faster dodges",
                         description="The enemies dodge faster than in the game. Off: the game's own dodge speed.")
shields = BoolOption("normal_shields", True, display_name="Shields",
                     description="The enemies without a shield get one, 40% of their health. It never comes back "
                                 "once broken.")
INCREASED, REDUCED = "Increased", "Reduced"
speed = SpinnerOption("normal_speed", INCREASED, [INCREASED, REDUCED], display_name="Enemy speed",
                      description="Reduced: the enemies run 15% slower, and so do their faster dodges. For those who "
                                  "find them too fast.")
on = BoolOption("normal_on", False, is_hidden=True)

# The NORMAL MODE page's rows: those the mode on locks, then the Hardcore's, never locked; then the hidden one.
LOCKED = [level, allies, fast_dodges, speed, shields]
HARDCORE = [hardcore, progress]
PAGE = [*LOCKED, *HARDCORE]
ALL = [*PAGE, on]


@dataclass(frozen=True)
class Settings:
    level: levels.Level
    allies: bool
    fast_dodges: bool = True
    shields: bool = True
    reduced: bool = False


def read() -> Settings:
    chosen = levels.level(level.value)
    reduced = chosen.reducible and speed.value == REDUCED
    return Settings(level=levels.reduced(chosen) if reduced else chosen, allies=allies.value is True,
                    fast_dodges=fast_dodges.value is not False,
                    shields=chosen.shields == levels.ALWAYS or shields.value is not False, reduced=reduced)
