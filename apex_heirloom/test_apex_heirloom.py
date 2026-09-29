"""Tests the mod as the SDK builds it: one mod, Apex Heirloom, with both parts' settings, keys and hooks; a fresh install
switches itself on with both parts running; each part's switch stops and starts it alone, the other running on; the
mod's own switch stops both, forgetting a key held and a restriction begun, and starts only those whose switch is on;
switching on gives each key its option's."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fake_player  # noqa: E402
import heirloom_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = heirloom_stubs.install()
import fake_world  # noqa: E402

world = fake_world.World(state)
state["settings_exists"] = False

import apex_heirloom  # noqa: E402
from apex_heirloom import frame, heirloom_settings, holster_settings, keys, lifecycle, parts, restriction  # noqa: E402
from apex_heirloom import control_actions, control_config, panel_preferences as prefs, settings  # noqa: E402


def running() -> tuple[bool, bool]:
    return lifecycle.STATE.running, keys.running()


mod = state["mods"][0]
check("one mod is built, Apex Heirloom 1.0.1", len(state["mods"]) == 1 and mod.kwargs["name"] == "Apex Heirloom"
      and apex_heirloom.__version__ == "1.0.1")
check("both keys are given to the SDK", mod.kwargs["keybinds"] == [keys.keyboard_bind, keys.controller_bind])
check("both parts' settings and both keys are given to the SDK, the window's own preferences last",
      mod.kwargs["options"] == [*settings.ALL, keys.keyboard_key, keys.controller_key, prefs.language,
                                prefs.controller_icons, prefs.last_page]
      and heirloom_settings.heirloom in settings.ALL and holster_settings.holster in settings.ALL)
check("choosing the mod in the SDK's menu opens its window",
      getattr(mod, "_apex_heirloom_panel_display_installed", False) is True)
check("the arms' frames, for the knife and for a key held, and the weapon restriction are given to the SDK",
      mod.kwargs["hooks"] == [lifecycle.arms_frame, frame.tick, restriction.on_restriction])
check("a fresh install switches itself on, both parts running", mod.is_enabled and running() == (True, True))
check("the holster says nothing of its keys before the arms' next frame",
      not any(line.startswith("[Tidy Weapons] on:") for line in state["misc"]))
frame.tick(world.instance, None, None, None)
check("... then writes it runs, with the keys in use", state["misc"][-1].startswith("[Tidy Weapons] on: keyboard "))
frame.tick(world.instance, None, None, None)
check("... once", sum(line.startswith("[Tidy Weapons] on:") for line in state["misc"]) == 1)

heirloom_settings.heirloom.value = False
check("the heirloom's switch off stops the heirloom alone", running() == (False, True))
heirloom_settings.heirloom.value = True
holster_settings.holster.value = False
check("the holster's switch off stops the holster alone, and it is written",
      running() == (True, False) and state["misc"][-1] == "[Tidy Weapons] off")
holster_settings.holster.value = True
check("each switch on again starts its part", running() == (True, True))

keys.keyboard_bind.callback(fake_player.event("IE_Pressed"))
restriction._restriction = ("OakCharacter_1", True)
mod.disable()
check("the mod off stops both parts", running() == (False, False))
check("and forgets a key held and a restriction begun with the hand empty",
      keys.pending() is False and restriction._restriction is None)
heirloom_settings.heirloom.value = False
heirloom_settings.heirloom.value = True
check("a switch changed while the mod is off, turned on included, starts nothing", running() == (False, False))
heirloom_settings.heirloom.value = False

# As mods_base loads a settings file edited by hand: its own copy of the keys, after the options, unchecked.
keys.keyboard_bind.key, keys.controller_bind.key = "LeftMouseButton", "Gamepad_LeftX"
mod.enable()
check("the mod on starts only the parts whose switch is on", running() == (False, True))
check("switching on gives each key its option's, the one the window shows",
      keys.keyboard_bind.key == keys.keyboard_key.value and keys.keyboard_bind.key != "LeftMouseButton"
      and keys.controller_bind.key == keys.controller_key.value == "Gamepad_FaceButton_Left")
check("each part is one of the two the mod runs", parts.PARTS == (parts.HEIRLOOM, parts.HOLSTER)
      and parts.HEIRLOOM.switch is heirloom_settings.heirloom and parts.HOLSTER.switch is holster_settings.holster)

# The window's Restore (panel_model.restore) with the holster off: the holster's switch comes before the keys and
# their settings (settings.ALL, then control_config.ALL), and starts the holster before they change (audit of
# 2026-09-26: the line written at once named the keys from before).
holster_settings.holster.value = False
keys.keyboard_key.value, holster_settings.keyboard_hold.value, holster_settings.hold_time.value = "G", False, 0.6
control_actions.save_values(mod, tuple((option, option.default_value)
                                       for option in (*settings.ALL, *control_config.ALL)))
frame.tick(world.instance, None, None, None)
check("Restore turning the holster on: the keys line says the keys and settings it put back",
      keys.running() and state["misc"][-1] == f"[Tidy Weapons] on: keyboard {keys.keyboard_bind.default_key} (hold), "
                                              "controller Gamepad_FaceButton_Left (hold), hold 0.40 s")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
