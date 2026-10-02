"""Tests the mod's settings: the six elements and the game names behind them, the sliders and what they hold
whatever the settings file says."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import beam, settings  # noqa: E402
from benefix_ohm_attack.slider_option import BoundedSliderOption  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("fire is the default element", settings.element.default_value == "Fire"
      and settings.chosen() == ("Fire", beam.Effect(sdk_stubs.FIRE_BEAM)))
check("the menu offers six choices, the five elements and the beam without one, each under a name of letters only",
      list(settings.element.choices) == ["Fire", "Shock", "Corrosive", "Cryo", "Radiation", "Kinetic"]
      and all(name.isalpha() and len(name) <= 16 for name in settings.ELEMENTS))
check("each element is one of the game's damage types and one of the game's beams",
      all(kind in ("Fire", "Shock", "Corrosive", "Cryo", "Radiation", "Normal")
          and effect.path.startswith("/Game/Gear/Weapons/_Shared/Effects/Systems/GenericLaser/NS_")
          and effect.path.rsplit("/", 1)[-1].split(".")[0] == effect.path.rsplit(".", 1)[-1]
          for kind, effect in settings.ELEMENTS.values()))
kinetic = settings.ELEMENTS["Kinetic"]
check("the beam without an element does plain damage, as the lightning of the Ohm I Got, aimed by a position",
      kinetic[0] == "Normal" and kinetic[1].position is True
      and kinetic[1].path.endswith("/NS_BOR_OhmIGot_Beam_Energy_Lightning.NS_BOR_OhmIGot_Beam_Energy_Lightning")
      and not any(effect.position for name, (_kind, effect) in settings.ELEMENTS.items() if name != "Kinetic"))

settings.element._from_json("KineticB")
check("an element's name the menu no longer offers, read from the settings file, leaves the default one",
      settings.element.value == "Fire" and len(state["errors"]) == 1)
settings.element.value = "Plasma"
check("and one put in the option any other way is fired and told as the default",
      settings.element_name() == "Fire" and settings.chosen()[0] == "Fire")
settings.element.value = "Cryo"
check("an element of the menu is itself", settings.element_name() == "Cryo" and settings.chosen()[0] == "Cryo")
settings.element.value = "Fire"

sliders = (settings.damage, settings.drain, settings.regen, settings.regen_delay)
check("every slider of the mod holds its value within its bounds, whatever the file says",
      all(type(slider) is BoundedSliderOption for slider in sliders)
      and [option for option in settings.ALL if hasattr(option, "min_value")] == list(sliders))
check("the defaults: 75 damage a second, 20 energy spent a second, 25 given back, after 2 seconds, the bar shown",
      [slider.default_value for slider in sliders] == [75, 20, 25, 2.0] and settings.show_bar.default_value is True)
check("the energy may never run out (0 spent), and always comes back (at least 1 given back)",
      settings.drain.min_value == 0 and settings.regen.min_value == 1)
check("the beam hits five times a second, a kilometre away at most", settings.HITS_PER_SECOND == 5.0 and settings.REACH == 100000.0)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
