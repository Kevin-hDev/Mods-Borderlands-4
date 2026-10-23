"""Tests the key that launches Companions' team or stops it (team_key.py, It Follows' own under Companions' names):
F8 at first, under a name of its own; a value that is no key read as F8; the SDK's keybind given the chosen key, once;
pressed with a team kept, the team started with Companions' owner, said; pressed while it is on, stopped; pressed with
no team kept, nothing started, said; pressed while the window is open, nothing done, the window's page doing it;
pressed while It Follows leads the team, nothing started, the refusal said."""

import json
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import companion_fixture as fake  # noqa: E402
import companions  # noqa: E402
from companions import control_window, session, settings, team_key  # noqa: E402
from companions.characters.companions import owners, team as team_module  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    found = [json.loads(text.removeprefix("[Companions] ")) for text in state["info"]
             if text.startswith("[Companions] {")]
    return [line for line in found if line["event"] == event]


game = fake.Game(state)
check("F8 at first, under a name of its own", team_key.DEFAULT == "F8" and team_key.option.identifier ==
      "companions_key" and team_key.key() == "F8")
team_key.option.value = "../F9"
check("a value that is no key: F8", team_key.key() == "F8")
team_key.option.value = "F11"
check("the SDK's keybind given the chosen key, once", team_key.align() is True and team_key.bind.key == "F11"
      and team_key.align() is False)
team_key.option.value = "F8"
team_key.align()

team_key._pressed()
check("no team kept: nothing started, said", not session.team_on()
      and notes("team_key_pressed")[-1]["outcome"] == "empty")
settings.team.value = ["Crankus", "Vex"]
team_key._pressed()
check("a team kept: started by Companions' owner, said", session.team_on()
      and notes("team_key_pressed")[-1]["outcome"] == "started")
team_key._pressed()
check("pressed again: stopped, said", not session.team_on() and notes("team_key_pressed")[-1]["outcome"] == "stopped")
real_active = control_window.active
control_window.active = lambda: True
team_key._pressed()
check("the window open: nothing done, said", not session.team_on()
      and notes("team_key_pressed")[-1]["outcome"] == "window_open")
control_window.active = real_active
owners.reset_for_tests()
owners.switched_on(team_module.OWNER)
owners.switched_on("it_follows", first=True)
team_key._pressed()
check("It Follows leading the team: nothing started, the refusal said", not session.team_on()
      and notes("team_key_pressed")[-1]["outcome"] == "elsewhere")
owners.reset_for_tests()
check("Companions' module, not It Follows'", isinstance(companions, types.ModuleType)
      and not any(name.startswith("it_follows") for name in sys.modules))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
