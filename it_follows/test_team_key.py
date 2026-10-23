"""Tests the key that launches the companions' team or stops it (team_key.py) and its row on the OPTIONS page
(panel_options.py): F8 at first, under a name of its own; a value that is no key read as F8; the SDK's keybind given
the chosen key, once; pressed with the team kept, the team started with each one's choice, said; pressed while it is
on, stopped; pressed with no team kept, nothing started, said; on the OPTIONS page, its row under the window's key,
a key chosen written and given to the keybind; the window's key refused there, and this one refused for the
window's, said, the field showing its own again; either field waiting for a key, Escape cancels the wait alone."""

import json
import pathlib
import sys
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import panel_fixture  # noqa: E402

panel_fixture.install()

import it_follows  # noqa: E402
from it_follows import game_pause, open_key, panel_assets, panel_fonts, panel_form, panel_model  # noqa: E402
from it_follows import control_window  # noqa: E402
from it_follows import panel_view, session, team_key, updates, welcome  # noqa: E402
from it_follows.companions import choices  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    found = [json.loads(text.removeprefix("[It Follows] ")) for text in state["info"]
             if text.startswith("[It Follows] {")]
    return [line for line in found if line["event"] == event]


started: list = []


def start_team(names: list, picks: dict) -> str:
    started.append((names, picks))
    session._state["team"] = SimpleNamespace()
    return "started"


def stop_team() -> str:
    session._state["team"] = None
    return "stopped"


session.start_team, session.stop_team = start_team, stop_team

try:
    check("F8 at first: F5 opens It Follows, F6 BL4 Arena, F7 Third Person & FOV", team_key.DEFAULT == "F8"
          == team_key.key() and team_key.bind.key == "F8")
    check("its own name: trial 191's F7 under team_key left behind", team_key.option.identifier == "companions_key")
    team_key.option.value = "Escape"
    check("a value that is no key reads as F8", team_key.key() == "F8" and team_key.align() is False)
    team_key.option.value = "F9"
    check("the SDK's keybind given the chosen key, once", team_key.align() is True and team_key.bind.key == "F9"
          and team_key.align() is False)
    team_key.option.value = "F5"
    check("the window's own key written in by hand: F8, never one press for both", team_key.key() == "F8")
    open_key.option.value = team_key.option.value = "F8"
    check("the window given F8 by hand too: the team's F9 (decision 52)", team_key.key() == team_key.SPARE == "F9")
    open_key.option.value = "F5"
    team_key.option.value = "F8"
    team_key.align()

    real_active = control_window.active
    control_window.active = lambda: True
    team_key.bind.callback()
    check("pressed while the window is open: nothing started nor stopped, said", started == []
          and notes("team_key_pressed")[-1]["outcome"] == "window_open")
    control_window.active = real_active

    team_key.bind.callback()
    check("pressed with no team kept: nothing started, said", started == []
          and notes("team_key_pressed")[-1]["outcome"] == "empty")
    choices.team.value = ["Vex", "Crankus"]
    choices.chosen.value = {"Vex": {"shield": False, "speed": "Off"}}
    team_key.bind.callback()
    check("pressed: the team kept started with each one's choice, said", started == [(
          ["Vex", "Crankus"], {"Vex": choices.Choice(False, "Off"), "Crankus": choices.Choice()})]
          and notes("team_key_pressed")[-1] == {"event": "team_key_pressed", "run": 0, "key": "F8",
                                                "outcome": "started"})
    team_key.bind.callback()
    check("pressed while the team is on: stopped", not session.team_on()
          and notes("team_key_pressed")[-1]["outcome"] == "stopped" and len(started) == 1)

    panel_assets.texture = lambda _world, name=panel_assets.AVATAR: None
    panel_fonts.build = lambda _root: {"title": object(), "body": object()}
    game_pause.watch = lambda: None
    welcome.seen.value = welcome.EDITION
    updates.seen.value = it_follows.__version__
    state["pc"] = SimpleNamespace(OakCharacter=None)
    model = panel_model.Model(it_follows.mod)
    _root, made = panel_view.build_view(object(), model)
    form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in made.items()}, model)
    made["nav:options"].SetIsChecked(True)
    form.poll()
    check("its row on the OPTIONS page, under the window's key, F8 shown", panel_fixture.text(made, "team_key_label")
          == "TEAM KEY" and made["team_key"].SelectedKey.Key.KeyName == "F8"
          and panel_fixture.text(made, "team_key_hint").startswith("Launches your team, or stops it"))

    def choose(field: str, key: str) -> None:
        made[field].SetSelectedKey(SimpleNamespace(Key=SimpleNamespace(KeyName=key)))
        form.poll()

    choose("team_key", "F9")
    check("a key chosen: written, the keybind given it", team_key.option.value == "F9" and team_key.bind.key == "F9")
    choose("team_key", "F5")
    check("the window's key refused: said, its own shown again", team_key.option.value == "F9"
          and made["team_key"].SelectedKey.Key.KeyName == "F9"
          and panel_fixture.text(made, "notice") == "That key is already It Follows' other key: choose another one.")
    choose("open_key", "F9")
    check("and the team's refused for the window's", open_key.option.value == "F5"
          and made["open_key"].SelectedKey.Key.KeyName == "F5")
    made["team_key"].selecting = True
    check("its field waiting for a key: Escape cancels the wait alone", form.selecting())
    made["team_key"].selecting = False
except Exception as error:  # noqa: BLE001 - a test file says what broke and goes on to its verdict
    import traceback
    traceback.print_exc()
    check(f"exception {type(error).__name__}: {error}", False)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
