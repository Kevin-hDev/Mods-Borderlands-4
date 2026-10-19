"""A Horde run's settings, as the window's HORDE MODE and OPTIONS pages show them (menu.py), and as a run reads them at
its start.

The choices are Kevin's (decisions 47, 48, 50, 52, 70 and 79): five levels, named Level 1 to Level 5 in the window and
never by their number (decision 53, panel_en.py); the enemies' speed from Normal to +50 % by 10 %, Normal at first;
Normal, Buff or Buff+, Normal at first, its help naming no figure (Kevin, 15 October 2026: « conserve uniquement les
noms BUFF(+) »); a time limit of 10 to 60 minutes or none, none at first; the bar shown, on at first, in three sizes.
The killed always come back: decision 80 took away decision 44's row, the Horde doing one thing and the normal mode
the other. The bar speaks the window's language (decision 62). A value the settings file holds that is no choice reads
as the default: a file edited by hand never keeps a run from starting.

The first row, Starting point (decision 138, spec-points-de-depart.md), off at first: on, the run starts from the place
chosen in the page's tabs. The place chosen has no row: kept while the row is off, shown again when it is on (Kevin:
« le mod mémorise le dernier choix »), the first of Kevin's places at first.

Two rows for the player's computer, as games offer (Kevin, 15 October 2026: « proposer des reglages
activable/desactivable »), each at first as the Horde was: the most enemies hunting at once, 30 to 120 by 10, 120 at
first (decision 96), and the far enemies managed, on at first (decision 97). The second is greyed and always on
(decision 99, Kevin after trial 33: « on va le griser temporairement ») until it is reworked.
"""

from dataclasses import dataclass

from mods_base import BoolOption, HiddenOption, SpinnerOption

from . import horde, levels, start_places, texts

SPEEDS = {"Normal": 1.0, "+10%": 1.1, "+20%": 1.2, "+30%": 1.3, "+40%": 1.4, "+50%": 1.5}
DURATIONS = {"10 min": 600.0, "20 min": 1200.0, "30 min": 1800.0, "45 min": 2700.0, "60 min": 3600.0,
             "Unlimited": None}
DEFAULT_SPEED, DEFAULT_DURATION = "Normal", "Unlimited"
# Decision 79, Kevin, 15 October 2026: Buff gives every enemy 20 % more health and the hunter 10 % more damage
# taken, Buff+ 40 % and 20 %. Each as (the enemies' health, the damage the hunter takes).
BUFFS = {"Normal": (1.0, 1.0), "Buff": (1.2, 1.1), "Buff+": (1.4, 1.2)}
DEFAULT_BUFF = "Normal"
# The bar's words in points (decision 52). Medium is trial 10's 19, already a little bigger than trial 9's 15; Small
# and Large are Claude's, until step 4 sets the three with the bar under Kevin's eyes.
BAR_SIZES = {"Small": 15.0, "Medium": 19.0, "Large": 24.0}
DEFAULT_BAR_SIZE = "Medium"
# Decision 96, Kevin, 15 October 2026: « une plage qui irait de 30 a 120 et par tranche de 10 ».
CROWDS = [str(most) for most in range(30, horde.CROWD_MAX + 1, 10)]

start_point = BoolOption("start_point", False, display_name="Starting point",
                         description="Start the run from a place of the map chosen in the tabs above, instead of where "
                                     "you stand.")
start_place = HiddenOption("start_place", start_places.DEFAULT)
level = SpinnerOption("level", str(levels.DEFAULT), [str(key) for key in levels.LEVELS], display_name="Level",
                      description="The higher the level, the more enemies around you.")
speed = SpinnerOption("speed", DEFAULT_SPEED, list(SPEEDS), display_name="Enemy speed",
                      description="How fast the enemies hunting you run.")
buff = SpinnerOption("buff", DEFAULT_BUFF, list(BUFFS), display_name="Buff",
                     description="Buff: the enemies have more health and you take more damage. Buff+: even more.")
duration = SpinnerOption("duration", DEFAULT_DURATION, list(DURATIONS), display_name="Time limit",
                         description="The run stops by itself at the end. Unlimited: until STOP.")
crowd = SpinnerOption("max_enemies", str(horde.CROWD_MAX), CROWDS, display_name="Max enemies",
                      description="The most enemies hunting you at once. Fewer: a lighter load for your computer.")
far = BoolOption("manage_far", True, display_name="Manage far enemies",
                 description="An enemy left far behind is brought back behind you. Always on for now: this "
                             "setting will be reworked in a later version.")
bar = BoolOption("bar", True, display_name="In-game bar",
                 description="Your kills, deaths and time, at the top left of the screen during a run.")
bar_size = SpinnerOption("bar_size", DEFAULT_BAR_SIZE, list(BAR_SIZES), display_name="Bar size",
                         description="Its size on the screen.")
# Decision 146: off at first, for the whole game, not only during a run (lost_loot.py does the work).
lost_loot = BoolOption("lost_loot", False, display_name="Lost Loot: 400 items",
                       description="The Lost Loot machine keeps up to 400 items instead of the game's limit. Off: the "
                                   "items it holds stay in it.")
# Decision 148: a switch, the 16:10 of the screen's own height (resolution.py). Its identifier is not trial 113's
# "resolution_1610", whose saved "Off" a switch would read as on (mods_base's BoolOption takes bool("Off")).
resolution = BoolOption("stretch_1610", False, display_name="16:10 resolution",
                        description="Plays in Fullscreen at the 16:10 resolution of your screen's height, 2304×1440 "
                                    "on a 1440p screen; on a 16:9 screen the image is stretched. Off: your own "
                                    "resolution and display mode come back.")
# The player's own resolution and display mode, "<width>x<height>:<mode>", kept while a 16:10 one is applied.
resolution_own = HiddenOption("resolution_own", "")
# Decision 149, Kevin, 19 October 2026: three profiles, the photo mode's Saturation at 140, 170 and 200 (trial 116:
# its 170 is the engine's 1.7), « le profil par défaut à l'activation ce sera 1,7 ». colours.py does the work.
COLOUR_PROFILES = {"Profile 1": 1.4, "Profile 2": 1.7, "Profile 3": 2.0}
DEFAULT_COLOUR_PROFILE = "Profile 2"
# One line, Kevin after trial 119: « Profil de couleurs », « juste "Des couleurs plus vives dans tout le jeu." »; the
# profile's buttons sit on the switch's line (panel_colours.py), so its own label and help are never shown.
colours = BoolOption("saturated_colours", False, display_name="Color profile",
                     description="Brighter colors over the whole game.")
colour_profile = SpinnerOption("colour_profile", DEFAULT_COLOUR_PROFILE, list(COLOUR_PROFILES), display_name="Profile",
                               description="")

# The RUN page's rows, which a run in progress locks, then the OPTIONS page's.
RUN = [start_point, level, speed, buff, duration, crowd, far]
DISPLAY = [bar, bar_size, lost_loot, resolution, colours, colour_profile]
# Decision 99: rows shown greyed and held at their default. Off, the horde stayed at 0 to 22 enemies at levels 2 and 5,
# and rose to 51 within 30 s once on again (trial 33).
SHELVED = (far,)
ALL = [*RUN, start_place, *DISPLAY, resolution_own]


@dataclass(frozen=True)
class Settings:
    level: int
    speed: float
    duration_s: float | None
    respawn: bool
    language: str
    bar: bool
    bar_points: float
    health: float = 1.0
    taken: float = 1.0
    crowd_max: int = horde.CROWD_MAX
    manage_far: bool = True
    # The starting place's number, None to start where the player stands.
    start_place: int | None = None


def _number(value: object) -> int:
    try:
        return int(str(value))
    except ValueError:
        return levels.DEFAULT


def read(language: str = texts.ENGLISH) -> Settings:
    """The settings as they stand now, the bar in the window's language; a value that is no choice reads as its
    default."""
    target = _number(level.value)
    health, taken = BUFFS.get(buff.value, BUFFS[DEFAULT_BUFF])
    return Settings(level=target if target in levels.LEVELS else levels.DEFAULT,
                    speed=SPEEDS.get(speed.value, SPEEDS[DEFAULT_SPEED]),
                    duration_s=DURATIONS.get(duration.value, DURATIONS[DEFAULT_DURATION]),
                    respawn=True,
                    language=language if language in texts.LANGUAGES else texts.ENGLISH,
                    bar=bar.value is not False,
                    bar_points=BAR_SIZES.get(bar_size.value, BAR_SIZES[DEFAULT_BAR_SIZE]),
                    health=health, taken=taken,
                    crowd_max=int(crowd.value) if crowd.value in CROWDS else horde.CROWD_MAX,
                    manage_far=True,
                    start_place=start_places.find(start_place.value).number if start_point.value is True else None)


def shelve() -> None:
    """Each shelved row back at its default, whatever the settings file holds (decision 99)."""
    for option in SHELVED:
        option.value = option.default_value


def duration_name(seconds: float | None) -> str:
    """The time limit's choice for a number of seconds, as the history keeps it; Unlimited for one it has not."""
    return next((name for name, limit in DURATIONS.items() if limit == seconds), DEFAULT_DURATION)
