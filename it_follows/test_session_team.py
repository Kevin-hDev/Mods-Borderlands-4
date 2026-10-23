"""Tests It Follows' owner of the companions' team (session.py), the companions' code being the characters' package's
(decision 69 of docs/renforts), the game faked (companion_fixture.py): nothing on at first; none chosen, nothing; a
team started with its card given and It Follows' level played, said; one at a time; stopped, the hook removed; one
set of camps for every team of the game session; the mod switched off stops it even when the normal mode's stop
raises; a stop failing midway still removes the hook; no team launched at the main menu, one launched while the menu
is unread; a team asking at the main menu stopped by its owner, an old one asking leaving the new one on. The mod
switched on leads the team before any other mod (owners.py), switched off leaves it. And the
bars' service started with the team whatever It Follows' option, which it reads through what session.py hands in.
Taken from the team's and the bars' tests when the companions' code left It Follows."""

import json
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import companion_fixture as fake  # noqa: E402
import it_follows  # noqa: E402
from it_follows import companion_choices as choices, report, session  # noqa: E402
from it_follows.characters.companions import owners, team as team_module  # noqa: E402

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
check("It Follows' lines behind its own name; its hooks named after its package", report.PREFIX == "[It Follows]"
      and team_module.IDENTIFIER == "it_follows:companions")
check("session: nothing on", session.team_live() is None and session.stop_team() == "not_on")
check("session: none chosen, nothing on", session.start_team([]) == "empty" and session.team_live() is None
      and session.start_team(["Nobody"]) == "empty")
check("session: the team started, on, its card given and It Follows' level played (none: Bandit)",
      session.start_team(["Crankus"], {"Crankus": choices.Choice(True, "Off")}) == "started"
      and session.team_live() == session.TeamLive(0, 1)
      and notes("team_start")[-1]["tuning"] == {"Crankus": [4.0, 0.3, None, 1.0, 45.0, "own", "Bandit", "off"]})
check("session: one team at a time", session.start_team(["Abomination"]) == "already_on")
check("session: stopped, off, the hook removed", session.stop_team() == "stopped" and session.team_live() is None
      and team_module.IDENTIFIER not in state["hooks"] and notes("team_stop")[-1]["why"] == "stopped")
first_births = session._state["companion_births"]
session.start_team(["Crankus"])
check("one set of camps for every team of the game session, as the Horde's (decision 59)",
      first_births is not None and session._state["team"].births is first_births)
real_stop_normal = session.stop_normal
session.stop_normal = lambda _reason: (_ for _ in ()).throw(RuntimeError("normal"))
it_follows._on_disable()
session.stop_normal = real_stop_normal
check("the mod switched off, the normal mode's stop raising: the team stopped all the same, said",
      session.team_live() is None and notes("team_stop")[-1]["why"] == "mod_disabled"
      and notes("disabled")[-1]["failed"] == ["normal:RuntimeError"])
check("the mod switched off: It Follows left the team's owners, said", owners.leads() is None
      and notes("team_owner_left")[-1]["owner"] == "it_follows")
owners.join("companions")
it_follows._on_enable()
check("the mod switched on, another mod joined before: It Follows leads, first, said",
      owners.leads() == "it_follows" and notes("team_owner_joined")[-1]["first"] is True)
check("leading, its team starts", session.start_team(["Crankus"]) == "started")
session.stop_team()
owners.reset_for_tests()

session.start_team(["Crankus"])
broken = session._state["team"]
broken.respawns.clear = lambda: (_ for _ in ()).throw(RuntimeError("clear"))
try:
    session.stop_team()
    stop_raised = False
except RuntimeError:
    stop_raised = True
check("a stop failing midway: the hook removed all the same, no team left running unowned",
      stop_raised and broken.hook is None and team_module.IDENTIFIER not in state["hooks"]
      and session.team_live() is None)

real_showing = session.main_menu.showing
session.main_menu.showing = lambda _pc: True
check("session: no team launched at the main menu (it would stop at once)",
      session.start_team(["Crankus"]) == "main_menu" and session.team_live() is None)
session.main_menu.showing = lambda _pc: None
check("session: the menu unread, the team launched as before", session.start_team(["Crankus"]) == "started")
owned = session._state["team"]
owned.end("main_menu")
check("session: the team asking at the main menu, stopped by its owner, said",
      session.team_live() is None and notes("team_stop")[-1]["why"] == "main_menu"
      and team_module.IDENTIFIER not in state["hooks"])
session.start_team(["Crankus"])
stops = len(notes("team_stop"))
owned.end("main_menu")
check("session: an old team asking leaves the new one on", session.team_on() and len(notes("team_stop")) == stops)
session.stop_team()
session.main_menu.showing = real_showing


class Published:
    def __init__(self) -> None:
        self.stopped = None

    def beat(self, team: object) -> None:
        pass

    def stop(self, why: str) -> None:
        self.stopped = why


made: list = []
real_bars = session.companion_bars
session.companion_bars = types.SimpleNamespace(start=lambda clock, shown: made.append((clock, shown)) or Published())
session.start_team(["Crankus"])
check("the bars' service started with the team, whatever the option, on its clock", [
      clock for clock, _shown in made] == [session._state["team"].clock]
      and isinstance(session._state["team"].bars, Published))
choices.bars.value = True
check("It Follows' option read through what it hands in, at each read", made[0][1]() is True)
choices.bars.value = False
check("It Follows' option, off at first, under its name of 1.0.10; its row starts and stops nothing",
      choices.bars.identifier == "companion_bars" and made[0][1]() is False and not hasattr(session, "switch_bars")
      and getattr(choices.bars, "on_change_while_enabled", None) is None)
started_bars = session._state["team"].bars
session.stop_team()
check("stopped with the team", started_bars.stopped == "stopped")
session.companion_bars = real_bars

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
