"""A Horde run's settings, as the window's HORDE MODE and OPTIONS pages show them (menu.py), and as a run reads them at
its start.

The choices are Kevin's (decisions 47, 48, 50, 52, 70 and 79): five levels, named Level 1 to Level 5 in the window and
never by their number (decision 53, panel_en.py); the enemies' speed from Normal to +50 % by 10 %, Normal at first;
Normal, Buff or Buff+, Normal at first, its help naming no figure (Kevin, 15 October 2026: « conserve uniquement les
noms BUFF(+) »); a time limit of 10 to 60 minutes or none, none at first; the bar shown, on at first, in three sizes.
The killed always come back: decision 80 took away decision 44's row, the Horde doing one thing and the normal mode
the other. The bar speaks the window's language (decision 62). A value the settings file holds that is no choice reads
as the default: a file edited by hand never keeps a run from starting.

Two rows for the player's computer, as games offer (Kevin, 15 October 2026: « proposer des reglages
activable/desactivable »), each at first as the Horde was: the most enemies hunting at once, 30 to 120 by 10, 120 at
first (decision 96), and the far enemies managed, on at first (decision 97). The second is greyed and always on
(decision 99, Kevin after trial 33: « on va le griser temporairement ») until it is reworked.
"""

from dataclasses import dataclass

from mods_base import BoolOption, SpinnerOption

from . import horde, levels, texts

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

# The RUN page's rows, which a run in progress locks, then the OPTIONS page's.
RUN = [level, speed, buff, duration, crowd, far]
DISPLAY = [bar, bar_size]
# Decision 99: rows shown greyed and held at their default. Off, the horde stayed at 0 to 22 enemies at levels 2 and 5,
# and rose to 51 within 30 s once on again (trial 33).
SHELVED = (far,)
ALL = [*RUN, *DISPLAY]


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
                    manage_far=True)


def shelve() -> None:
    """Each shelved row back at its default, whatever the settings file holds (decision 99)."""
    for option in SHELVED:
        option.value = option.default_value


def duration_name(seconds: float | None) -> str:
    """The time limit's choice for a number of seconds, as the history keeps it; Unlimited for one it has not."""
    return next((name for name, limit in DURATIONS.items() if limit == seconds), DEFAULT_DURATION)
