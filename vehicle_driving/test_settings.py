"""Tests the settings: names, defaults and bounds as Kevin validated them, the factors, the loss per degree."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


sdk_stubs.install()

from vehicle_driving import settings  # noqa: E402

shown = [(option.identifier, option.display_name, option.value, option.args) for option in settings.OPTIONS]
check("the six settings of the menu, in order, with Kevin's defaults and bounds (spec section 2)", shown == [
    ("max_speed", "Max speed", 125, (100, 300)),
    ("acceleration", "Acceleration", 250, (100, 500)),
    ("turn_speed", "Turn speed", 250, (100, 500)),
    ("jump_height", "Jump height", 200, (100, 400)),
    ("grip", "Grip", True, ()),
    ("turn_loss", "Speed lost in a 90 degree turn", 9, (0, 30)),
])
check("every slider moves by whole percents", all(
    option.kwargs.get("step") == 1 and option.kwargs.get("is_integer") for option in settings.OPTIONS if option.args))
check("each multiplier's description names the game's own value",
      all("100 is the game's own" in option.kwargs["description"] for option in settings.OPTIONS[:4]))
check("the turn loss says the game's braking adds to it", "braking adds" in settings.turn_loss.kwargs["description"])
check("the factors are the sliders over 100",
      settings.factors() == {"max_speed": 1.25, "acceleration": 2.5, "turn_speed": 2.5, "jump_height": 2.0})
loss = settings.loss_per_degree()
check("a 90 degree turn loses exactly the set share", abs((1.0 - loss) ** 90 - 0.91) < 1e-9)
check("9 percent is about session 9's 0.1 percent a degree", 0.00104 < loss < 0.00105)
settings.turn_loss.value = 0
check("at 0 the grip loses nothing", settings.loss_per_degree() == 0.0)

# The console menu does not hold a slider to its bounds: 250 typed for Max speed, shown [100-200], was driven with
# (2026-09-19).
check("within bounds nothing is said", settings.keep_in_bounds() == [])
settings.max_speed.value = 500
told = settings.keep_in_bounds()
check("a slider above its bounds is brought back to its top, and said so",
      settings.max_speed.value == 300 and told == ["setting max_speed=500 outside 100-300, set to 300"])
settings.turn_loss.value = -5
settings.keep_in_bounds()
check("and one below, to its bottom", settings.turn_loss.value == 0)
settings.max_speed.value = float("nan")
settings.keep_in_bounds()
check("a value that is not a number goes back to its default", settings.max_speed.value == 125)
check("a switch is left alone", settings.grip.value is True)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
