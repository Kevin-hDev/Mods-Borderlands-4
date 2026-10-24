"""Tests Companions as a whole (companions/__init__.py), with no file of It Follows anywhere Python looks: Companions
must work without It Follows (Kevin, 23 October 2026: « Companions doit fonctionner sans it follows, c'est deux mods
independant l'un de l'autre »). The mod built under its name and version, with its settings, its window's, its two
keys and their keybinds: none to open the window at first, F8 for the team; a first install, without its settings
file, switched on as the SDK would leave it off; the keys the settings file gives handed to the SDK's keybinds at
load (review of 23 October 2026: neither was tested); switched on, it joins
the team's owners, not first, and its team starts and stops; switched off, its team stopped and the owners left, even
when the team's stop raises; nothing of It Follows imported at any point."""

import importlib.util
import json
import pathlib
import sys
import tempfile
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import mods_base  # noqa: E402

NEVER_WRITTEN = pathlib.Path(tempfile.mkdtemp(prefix="companions_first_")) / "companions.json"
CHOSEN = {"open_key": "F11", "companions_key": "F12"}


def first_install(cls=sdk_stubs.FakeMod, **kwargs):
    """As mods_base builds a mod at a first install: the settings file not written yet, the mod off; the load of a
    file gives the keys; enable() runs on_enable, as the real one does."""
    for option in kwargs["options"]:
        option.value = CHOSEN.get(option.identifier, option.value)

    class FirstInstall(cls):
        def enable(self) -> None:
            if not self.is_enabled:
                self.is_enabled = True
                self.on_enable()

    built = FirstInstall(**kwargs)
    built.settings_file, built.is_enabled = NEVER_WRITTEN, False
    return built


built_as = mods_base.build_mod
mods_base.build_mod = first_install

# companion_fixture imports Companions: built here as at a first install.
import companion_fixture as fake  # noqa: E402
mods_base.build_mod = built_as

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    found = [json.loads(text.removeprefix("[Companions] ")) for text in state["info"]
             if text.startswith("[Companions] {")]
    return [line for line in found if line["event"] == event]


def it_follows_loaded() -> list[str]:
    return [name for name in sys.modules if name == "it_follows" or name.startswith("it_follows.")]


check("no It Follows where Python looks", importlib.util.find_spec("it_follows") is None)
import companions  # noqa: E402
from companions import open_key, panel_preferences, session, settings, team_key  # noqa: E402
from companions.characters.companions import owners, team as team_module  # noqa: E402

mod = companions.mod
check("a first install: switched on, as the SDK would leave a mod without settings file off, joined the owners",
      mod.is_enabled and notes("enabled")[-1]["version"] == "1.0.3" and owners.leads() == "companions")
check("the keys the settings file gives: handed to the SDK's keybinds at load", open_key.bind.key == "F11"
      and team_key.bind.key == "F12")
open_key.option.value, team_key.option.value = open_key.DEFAULT, team_key.DEFAULT
open_key.align()
team_key.align()
check("built as Companions 1.0.3, with its settings", mod.name == "Companions" and companions.__version__ == "1.0.3"
      and mod.options == [*settings.TEAM, settings.bars, *settings.HIDDEN, *panel_preferences.ALL,
                          open_key.option, team_key.option])
check("the keys: none to open the window at first (decision 71), F8 for the team, each bound by the SDK",
      mod.keybinds == [open_key.bind, team_key.bind] and open_key.key() is None and open_key.bind.key is None
      and team_key.key() == "F8" and team_key.bind.key == "F8")
listed = types.SimpleNamespace(iter_display_options=lambda: iter(()))
companions.panel_open.install(listed)
check("a mod's page in the SDK's list opens Companions' window, under its own marker",
      getattr(listed, "_companions_panel_display_installed", False) is True)
game = fake.Game(state)
owners.reset_for_tests()
companions._on_enable()
check("switched on: said, joined the team's owners, not first, leading alone", notes("enabled")[-1]["version"] ==
      "1.0.3" and owners.leads() == "companions" and notes("team_owner_joined")[-1]["first"] is False)
check("its team starts, then stops", session.start_team(["Crankus", "Vex"]) == "started"
      and session.stop_team() == "stopped")
session.start_team(["Crankus"])
companions._on_disable()
check("switched off: the team stopped, the owners left, said", not session.team_on() and owners.leads() is None
      and notes("team_stop")[-1]["why"] == "mod_disabled" and "failed" not in notes("disabled")[-1])
companions._on_enable()
session.start_team(["Crankus"])
real_stop = session.stop_team
session.stop_team = lambda _reason="": (_ for _ in ()).throw(RuntimeError("stop"))
companions._on_disable()
session.stop_team = real_stop
check("the team's stop raising: the owners left all the same, said", owners.leads() is None
      and notes("disabled")[-1]["failed"] == ["team:RuntimeError"])
session.stop_team()
check("nothing of It Follows imported", it_follows_loaded() == [])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
