"""Tests Companions' owner of the team (session.py), the companions' code being the characters' package's (decision 69
of docs/renforts), the game faked (companion_fixture.py): nothing on at first; none chosen, nothing; a team started
with the settings read at its start, said; one at a time; stopped, the hook removed; one set of camps for every team
of the game session; no team at the main menu; a team asking at the main menu stopped by its owner, an old one asking
leaving the new one on; It Follows 1.0.10 in the game: no team, said; It Follows leading the team: none, and one
running stopped when It Follows comes to lead. And the bars' service started with the team, which reads the bars'
setting through what session.py hands in."""

import json
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import companion_fixture as fake  # noqa: E402
from companions import report, session, settings  # noqa: E402
from companions.characters import animation_hook  # noqa: E402
from companions.characters.companions import owners, team as team_module  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    found = [json.loads(text.removeprefix(report.PREFIX + " ")) for text in state["info"]
             if text.startswith(report.PREFIX + " {")]
    return [line for line in found if line["event"] == event]


game = fake.Game(state)
check("Companions' lines behind its own name; its hooks named after its package", report.PREFIX == "[Companions]"
      and team_module.IDENTIFIER == "companions:companions")
check("nothing on, nothing in the way", not session.team_on() and session.stop_team() == "not_on"
      and session.blocked() is None)
check("none chosen, nothing on", session.start_team([]) == "empty" and not session.team_on()
      and session.start_team(["Nobody"]) == "empty")
settings.health.value, settings.refill.value = 9, 30
check("the team started, on, with the settings read at its start, said",
      session.start_team(["Crankus"]) == "started" and session.team_on()
      and len(session._state["team"].respawns.waiting) == 1
      and notes("team_start")[-1]["tuning"] == {"Crankus": [9.0, 0.3, 30.0, 1.2, 45.0, "own", "settings",
                                                            "companions"]})
settings.health.value = 2
check("a setting changed while it is on: the team keeps the one it started with",
      session._state["team"].tuning_of("Crankus").times == 9.0)
settings.health.value, settings.refill.value = 4, settings.NEVER
check("one team at a time, its beat on the animation update", session.start_team(["Abomination"]) == "already_on"
      and team_module.IDENTIFIER in animation_hook.beats())
check("stopped, off, the hook removed", session.stop_team() == "stopped" and not session.team_on()
      and team_module.IDENTIFIER not in animation_hook.beats() and notes("team_stop")[-1]["why"] == "stopped")
first_births = session._state["births"]
session.start_team(["Crankus"])
check("one set of camps for every team of the game session (decision 59)",
      first_births is not None and session._state["team"].births is first_births)
session.stop_team()

real_showing = session.main_menu.showing
session.main_menu.showing = lambda _pc: True
check("no team launched at the main menu (it would stop at once)",
      session.start_team(["Crankus"]) == "main_menu" and not session.team_on())
session.main_menu.showing = lambda _pc: None
check("the menu unread: the team launched", session.start_team(["Crankus"]) == "started")
owned = session._state["team"]
owned.end("main_menu")
check("the team asking at the main menu, stopped by its owner, said",
      not session.team_on() and notes("team_stop")[-1]["why"] == "main_menu")
session.start_team(["Crankus"])
stops = len(notes("team_stop"))
owned.end("main_menu")
check("an old team asking leaves the new one on", session.team_on() and len(notes("team_stop")) == stops)
session.stop_team()
session.main_menu.showing = real_showing

sys.modules["it_follows.companions.team"] = types.ModuleType("it_follows.companions.team")
check("It Follows 1.0.10 in the game: no team, said", session.start_team(["Crankus"]) == "it_follows_outdated"
      and not session.team_on() and notes("team_refused")[-1]["why"] == "it_follows_outdated"
      and session.blocked() == "team_outdated")
del sys.modules["it_follows.companions.team"]
sys.modules["it_follows.characters.companions.team"] = types.ModuleType("it_follows.characters.companions.team")
check("the It Follows that carries the characters' package: never taken for 1.0.10, the team starts",
      session.blocked() is None and session.start_team(["Crankus"]) == "started")
session.stop_team()
del sys.modules["it_follows.characters.companions.team"]

owners.reset_for_tests()
owners.switched_on(team_module.OWNER)
owners.switched_on("it_follows", first=True)
check("It Follows leading the team: none started, said why", session.start_team(["Crankus"]) == "elsewhere"
      and not session.team_on() and session.blocked() == "team_elsewhere")
owners.switched_off("it_follows")
check("It Follows switched off: Companions leads, the team starts", session.start_team(["Crankus"]) == "started")
led = session._state["team"]
owners.switched_on("it_follows", first=True)
led.end("elsewhere")
check("It Follows coming to lead: the team asking is stopped by its owner, said", not session.team_on()
      and notes("team_stop")[-1]["why"] == "elsewhere")
owners.reset_for_tests()
foreign = types.ModuleType(owners.STATE)
foreign.protocol, foreign.owners = owners.PROTOCOL + 1, {}
sys.modules[owners.STATE] = foreign
check("copies of the companions' code of two versions: no team, said as such, never as It Follows leading",
      session.blocked() == "team_mismatch" and session.start_team(["Crankus"]) == "elsewhere")
owners.reset_for_tests()


class Published:
    def __init__(self) -> None:
        self.stopped = None

    def beat(self, team: object) -> None:
        pass

    def stop(self, why: str) -> None:
        self.stopped = why


made: list = []
real_bars = session.bars
session.bars = types.SimpleNamespace(start=lambda clock, shown: made.append((clock, shown)) or Published())
session.start_team(["Crankus"])
check("the bars' service started with the team, on its clock", [clock for clock, _shown in made] == [
      session._state["team"].clock] and isinstance(session._state["team"].bars, Published))
settings.bars.value = True
check("the bars' setting read through what Companions hands in, at each read", made[0][1]() is True)
settings.bars.value = False
check("off at first", settings.bars.default_value is False and made[0][1]() is False)
started_bars = session._state["team"].bars
session.stop_team()
check("stopped with the team", started_bars.stopped == "stopped")
session.bars = real_bars

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
