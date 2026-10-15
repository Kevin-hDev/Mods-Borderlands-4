"""Tests the game's limit of enemies lifted for It Follows: switched off once, on the world in play's settings, each
call written by report.py before it is made, and given back at the stop where It Follows switched it, once a run;
settings the game had already switched off are left alone and not given back; settings that cannot be read, or a
switch that raises, are said and never retried; lifted settings the game no longer holds are lifted again, and are not
given back."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import budget, report  # noqa: E402
import wave_fixture as fake  # noqa: E402
from wave_fixture import events  # noqa: E402

fake.record_log()
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def line(call: str, **fields: object) -> tuple:
    return "log", {"event": "call", "run": 0, "call": call, **fields}


try:
    settings = fake.Settings()
    fake.play(settings)
    limit = budget.Budget(report.announce)
    check("nothing lifted, nothing to give back", limit.restore() == "nothing_lifted" and events == [])
    check("the limit is lifted on the world in play's settings, each call written to the log before it is made",
          limit.lift() == "lifted" and settings.bDisableSpawnBudget is True
          and events == [line("WorldSettings", switch=budget.SWITCH),
                         line("bDisableSpawnBudget", value=True, on="OakWorldSettings_0"),
                         ("bDisableSpawnBudget", True)])
    events.clear()
    check("lifted once: asked again, nothing is read nor called", limit.lift() == "lifted" and events == [])
    check("given back at the stop, written to the log first",
          limit.restore() == "given_back" and settings.bDisableSpawnBudget is False
          and events == [line("bDisableSpawnBudget", value=False, on="OakWorldSettings_0"),
                         ("bDisableSpawnBudget", False)])
    events.clear()
    check("one run's lift: not lifted again after the stop, nor given back twice",
          limit.lift() == "given_back" and limit.restore() == "nothing_lifted" and events == [])

    off = fake.Settings(off=True)
    fake.play(off)
    limit = budget.Budget(report.announce)
    events.clear()
    check("settings the game already switched off are left alone, never retried, never given back",
          limit.lift() == "already_off" and limit.lift() == "already_off" and limit.restore() == "nothing_lifted"
          and off.bDisableSpawnBudget is True and events == [line("WorldSettings", switch=budget.SWITCH)])
    fake.play(None)
    limit = budget.Budget(report.announce)
    first_said = limit.lift()
    events.clear()
    check("no settings in play: said, never retried", first_said == "no_settings" and limit.lift() == "no_settings"
          and events == [])
    del sys.modules["mods_base"].ENGINE
    limit = budget.Budget(report.announce)
    check("settings that cannot be read: said with the error", limit.lift() == "call_failed:AttributeError")
    fake.play(fake.Settings(refuses=True))
    limit = budget.Budget(report.announce)
    check("a switch that raises: said, nothing to give back",
          limit.lift() == "call_failed:RuntimeError" and limit.restore() == "nothing_lifted")

    first = fake.Settings()
    fake.play(first)
    limit = budget.Budget(report.announce)
    limit.lift()
    fake.free(first)
    second = fake.Settings()
    fake.play(second)
    check("lifted settings the game no longer holds: lifted again on the new ones",
          limit.lift() == "lifted" and second.bDisableSpawnBudget is True)
    fake.free(second)
    events.clear()
    check("and settings gone at the stop are not given back", limit.restore() == "settings_gone" and events == [])
    refusing = fake.Settings()
    fake.play(refusing)
    limit = budget.Budget(report.announce)
    limit.lift()
    object.__setattr__(refusing, "refuses", True)
    check("a give back that raises is said", limit.restore() == "call_failed:RuntimeError")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
