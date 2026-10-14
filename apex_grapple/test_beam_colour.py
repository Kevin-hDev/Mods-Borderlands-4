"""Tests beam_colour.py: the game's rope left in its own blue, given both its colours in any other, a refusal costing
the colour alone and said once."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import beam_colour, look_assets, look_settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Beam:
    def __init__(self, refuses: str | None = None) -> None:
        self.written, self.refuses = [], refuses

    def SetVariableLinearColor(self, name, colour):
        if name == self.refuses:
            raise RuntimeError("no such parameter")
        self.written.append((name, (colour.R, colour.G, colour.B, colour.A)))


beam = Beam()
beam_colour.paint(beam)
check("the game's own blue, at first: the effect is left untouched",
      look_settings.game_rope_colour.value == "BLUE" and beam.written == [])

look_settings.game_rope_colour.value = "GREEN"
beam = Beam()
beam_colour.paint(beam)
green = (*look_assets.COLOURS["GREEN"], 1.0)
check("another colour: both the rope's colours take it, by the names the effect lists",
      beam.written == [("User.Color", green), ("User.BeamColor", green)])

beam = Beam(refuses="User.Color")
beam_colour.paint(beam)
beam_colour.paint(Beam(refuses="User.Color"))
check("a refusal costs that colour alone, the other still written, and is said once",
      beam.written == [("User.BeamColor", green)]
      and len([line for line in state["errors"] if "User.Color" in line]) == 1)
look_settings.game_rope_colour.value = "BLUE"

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
