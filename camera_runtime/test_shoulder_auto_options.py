"""The automatic shoulder's options: on by default, two delays kept within their ranges."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


class Option:
    def __init__(self, identifier, value, *_args, **_texts):
        self.identifier, self.value = identifier, value


sys.modules["mods_base"] = types.SimpleNamespace(BoolOption=Option, SliderOption=Option)

from apex_camera_runtime.shoulder_auto import RETURN_S, SWAP_S  # noqa: E402
from apex_camera_runtime.shoulder_auto_options import (MAX_RETURN_S, MAX_SWAP_S, MIN_RETURN_S,  # noqa: E402
                                                        MIN_SWAP_S, ShoulderAutoOptions)
from apex_camera_runtime.shoulder_transition_options import ShoulderTransitionOptions  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


options = ShoulderAutoOptions()
check("on by default with the third trial's delays", options.values() == (True, SWAP_S, RETURN_S))
check("saved under stable names", [option.identifier for option in options.options]
      == ["shoulder_auto", "shoulder_auto_swap", "shoulder_auto_return"])
options.switch.value, options.swap.value, options.back.value = False, 0.5, 2.0
check("the player's choices are read", options.values() == (False, 0.5, 2.0))
options.switch.value, options.swap.value, options.back.value = "no", 9.0, -1.0
check("a hand-edited file stays on and in range", options.values() == (True, MAX_SWAP_S, MIN_RETURN_S))
options.swap.value, options.back.value = float("nan"), True
check("an unreadable delay falls back to its default", options.values()[1:] == (SWAP_S, RETURN_S))
check("the ranges hold the defaults", MIN_SWAP_S <= SWAP_S <= MAX_SWAP_S and MIN_RETURN_S <= RETURN_S <= MAX_RETURN_S)
shared = ShoulderTransitionOptions()
check("the CAMERA page lists the switch and its delays first",
      [option.identifier for option in shared.options[:3]] == ["shoulder_auto", "shoulder_auto_swap",
                                                                "shoulder_auto_return"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
