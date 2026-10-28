"""Tests what the player sets for the heirloom, in the window's order (sketch H2): its switch first, on; the heirloom,
the knife first; each heirloom's skin, its own look first; the glow's force, 1 to 5, 3 by default; the mode, Apex by
default, both modes named as their lists are; each heirloom's size, 100 % the size Kevin set, the knife's under the name
it was saved under before the axe; the draw's start and speed as he set them. A settings file edited by hand reads as
the nearest bound or the default: a heirloom no longer offered as the knife, a skin a heirloom has not as its own look.
Chosen as the window saves it: the heirloom, with its own hold and size, keeping the skin it last wore; its skin;
the force. Which skins glow."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import definition_fixture  # noqa: E402
import heirloom_stubs  # noqa: E402

heirloom_stubs.install()
from apex_heirloom import heirloom_settings as h  # noqa: E402
from apex_heirloom.apex_fit import Fit  # noqa: E402
from apex_heirloom.heirloom_catalog import HEIRLOOMS, OFFERED  # noqa: E402

KNIFE, AXE = HEIRLOOMS["jakobs_knife"]["hold"], HEIRLOOMS["axe"]["hold"]
from apex_heirloom.apex_moves_timing import LIMITS, Timing  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


skins, sizes = h.SKINS, h.SIZES
check("in the window's order: the switch, on by default, the heirloom, each one's skin, the glow, the mode, each one's "
      "size, then the draw", h.heirloom.value is True
      and h.ALL == (h.heirloom, h.model, skins["jakobs_knife"], skins["axe"], h.glow, h.mode, sizes["jakobs_knife"],
                    sizes["axe"], h.draw_start, h.draw_speed))
check("the heirlooms the mod offers, the knife first and by default", h.model.choices == list(OFFERED)
      == ["jakobs_knife", "axe"] and h.model.value == "jakobs_knife" == h.DEFAULT == h.chosen_heirloom())
check("each heirloom's skins, as its catalog sets them, its own look first and by default: the knife has only its own",
      all(skins[name].choices == [skin["name"] for skin in HEIRLOOMS[name]["skins"]] for name in OFFERED)
      and all(skins[name].value == "own" == skins[name].choices[0] for name in OFFERED)
      and skins["jakobs_knife"].choices == ["own"] and len(skins["axe"].choices) == 8
      and [skins[name].identifier for name in OFFERED] == ["skin_jakobs_knife", "skin_axe"])
check("the glow's force, 1 to 5 in whole steps, 3 by default", (h.glow.min_value, h.glow.max_value) == (1, 5)
      and h.glow.value == 3 == h.chosen_force() and h.glow.step == 1 and h.glow.is_integer)
check("Apex by default; both modes named, each as its list",
      h.mode.value == "Apex" and h.chosen_mode() == "apex"
      and h.MODES == {"Apex": "apex", "Borderlands": "borderlands"}
      and h.mode.choices == ["Apex", "Borderlands"])
definition = definition_fixture.load()
if definition is None:
    definition_fixture.skip("the default mode is the knife's lists' default")
else:
    check("the default mode is the knife's lists' default", h.chosen_mode() == definition["lists"]["default"])
check("a mode about to be chosen is read as its list; one the menu does not know as the default",
      h.chosen_mode("Borderlands") == "borderlands" and h.chosen_mode("Halo") == "apex")
check("each heirloom at 100 %, between 50 and 150, which is the size Kevin set: the knife's hold as its own",
      all(sizes[name].value == 100 and (sizes[name].min_value, sizes[name].max_value) == (50, 150) for name in OFFERED)
      and h.fit() == Fit.of(KNIFE) and h.fit().size == 62.0)
check("the knife's size keeps the name it was saved under before the axe, a player's size kept; the axe's its own",
      sizes["jakobs_knife"].identifier == "size" and sizes["axe"].identifier == "size_axe")
check("the draw starts and plays as Kevin set it, within the timing's bounds",
      (h.draw_start.value, h.draw_speed.value) == (Timing.start, Timing.speed)
      and (h.draw_start.min_value, h.draw_start.max_value) == LIMITS["start"]
      and (h.draw_speed.min_value, h.draw_speed.max_value) == LIMITS["speed"]
      and h.timing() == Timing())
sizes["jakobs_knife"].value, h.draw_start.value, h.draw_speed.value = 150, 0.1, 1.5
check("a size is a fraction of Kevin's, and the draw takes the values set, the put-away keeping its own",
      h.fit() == Fit.of(KNIFE, 150) and h.fit().size == 93.0 and h.timing() == Timing(start=0.1, speed=1.5))
sizes["jakobs_knife"].value, h.draw_start.value, h.draw_speed.value = 900, "fast", float("nan")
check("a settings file edited by hand: out of bounds, the nearest; not a number, the default",
      h.fit() == Fit.of(KNIFE, 150) and h.timing() == Timing())
h.model.value, skins["axe"].value, h.glow.value = "sword", "rust", 9
check("... a heirloom no longer offered reads as the knife, a skin it has not as its own look, a force past 5 as 5",
      h.chosen_heirloom() == "jakobs_knife" and h.chosen_skin("axe") == "own" and h.chosen_force() == 5)
h.glow.value = "bright"
check("... a force that is no number as 3", h.chosen_force() == 3)
h.model.value, skins["axe"].value, h.glow.value = "jakobs_knife", "own", 3
check("each setting a player sees says what it does", all(option.kwargs.get("description") for option in h.ALL))

h.model.value = "axe"
check("the axe chosen, with its own hold at its own size", h.chosen_heirloom() == "axe" and h.fit() == Fit.of(AXE, 100))
skins["axe"].value = "blood"
check("the axe's skin chosen", h.chosen_skin() == "blood")
h.model.value = "jakobs_knife"
check("another heirloom chosen comes in the skin it last wore, and the axe keeps its own for when it comes back",
      h.chosen_skin() == "own" and h.chosen_skin("axe") == "blood")
h.glow.value = 5
check("a force chosen", h.chosen_force() == 5)
h.glow.value = 3
check("the axe's own look has our glow, the game's skins and the knife none",
      h.glows("axe", "own") and not h.glows("axe", "hacker") and not h.glows("jakobs_knife", "own")
      and not h.glows("axe", "rust"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
