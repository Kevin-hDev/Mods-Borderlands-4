"""Tests the shot's own line of the log: what the aim, the catch and the lock did while the key was held, among how
many foes, and with which settings."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import aim, foes, lock, settings, shot_report  # noqa: E402

fails: list[str] = []
FAR = (5000.0, 0.0, 50.0)
DEFAULTS = "0 foes known; catch 200 cm, lock after 0.20 s broken at 30 degrees, bounce on"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def frames(count: int, aimed: aim.Aim, first: lock.Target | None = None) -> None:
    for _ in range(count):
        shot_report.frame(aimed, first, 0.05)


def target(locked: bool = False, strayed: float = 0.0) -> lock.Target:
    return lock.Target(psycho, (960.0, 0.0, 50.0), None, "Char_Psycho", 960.0, locked, strayed)


pc, character = sdk_stubs.player(state)
psycho = sdk_stubs.Actor("Char_Psycho_4", (1000.0, 0.0, 50.0))
nothing = aim.Aim(anchor=FAR)
under = aim.Aim(anchor=(960.0, 0.0, 50.0), enemy=psycho, species="Char_Psycho", distance=960.0)
beside = aim.Aim(anchor=(960.0, 0.0, 50.0), enemy=psycho, species="Char_Psycho", distance=960.0, caught=True)

shot_report.begin()
frames(12, nothing)
check("a shot on nothing says how long it lasted, and that, then how many foes were known and the settings",
      shot_report.line() == f"shot 0.60 s: on no enemy; {DEFAULTS}")

shot_report.begin()
frames(8, under, target())
frames(4, beside, target())
check("a shot on an enemy says for how long he was under the aim, and for how long caught beside it",
      shot_report.line() == f"shot 0.60 s: on an enemy 0.40 s under the aim and 0.20 s caught beside it; {DEFAULTS}")

shot_report.begin()
frames(4, under, target())
for strayed in (3.0, 12.4, 7.0):
    shot_report.frame(nothing, target(locked=True, strayed=strayed), 0.05)
check("a lock says how long it held and how far the aim strayed from the enemy at most",
      shot_report.line() == "shot 0.35 s: on an enemy 0.20 s under the aim and 0.00 s caught beside it; "
                            f"locked 0.15 s, the aim up to 12 degrees away; {DEFAULTS}")
shot_report.frame(nothing, target(locked=False, strayed=50.0), 0.05)
check("a target that is not locked is no lock", "locked 0.15 s, the aim up to 12 degrees" in shot_report.line())

shot_report.begin()
frames(3, aim.Aim(anchor=FAR, hidden=True))
frames(1, nothing)
check("a foe near the aim that something hid is said, with how long",
      shot_report.line() == f"shot 0.20 s: on no enemy; a foe beside the aim hidden 0.15 s; {DEFAULTS}")

shot_report.begin()
check("a new shot starts from nothing", shot_report.line() == f"shot 0.00 s: on no enemy; {DEFAULTS}")

state["all"]["OakCharacter"] = [character, psycho, sdk_stubs.Actor("Char_Brute_9", (400.0, 300.0, 50.0))]
foes.around(character)
settings.width.value, settings.lock_delay.value, settings.lock_angle.value = 350, 1.5, 5
settings.bounce.value = False
check("the line says how many foes the last walk found, and the settings the shot was fired with",
      shot_report.line() == "shot 0.00 s: on no enemy; 2 foes known; catch 350 cm, lock after 1.50 s broken at "
                            "5 degrees, bounce off")
settings.width.value, settings.lock.value = 0, False
check("a catch of nothing and a lock switched off are said off",
      shot_report.line().endswith("2 foes known; catch off, lock off, bounce off"))
settings.width.value = 100000
check("a setting written out of its bounds is said as the attack reads it", "catch 500 cm" in shot_report.line())

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
