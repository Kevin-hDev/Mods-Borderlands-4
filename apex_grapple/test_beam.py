"""Tests the rope on screen: where the beam is put, that it follows, and that it never costs a pull."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import beam, game, rope_ends  # noqa: E402

# The eleven names the game printed on 2026-09-20.
_NAMES = ["User.Color Scale", "User.Color", "User.Lifetime", "User.Radius", "User.Width",
          "User.Target", "User.Emissive Scale", "User.OffsetCamera", "User.Delay", "User.Source",
          "User.BeamColor"]

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
state["pc"] = sdk_stubs.player(player, state["mappings"])
game.refresh(0, at_once=True)
niagara = state["niagara"]

beam.start(player, (100.0, 200.0, 300.0))
check("the game's own effect is spawned", len(niagara.spawned) == 1)
# The one difference the probe found on 2026-09-21 between the rope that shows and the one that does
# not: the game's own beam is attached to nothing and belongs to the world.
check("free in the world, as the game puts its own rope there", niagara.spawned[0]["how"] == "loose")
hand = game.hand_spot(player)
check("at the player's hand", (niagara.spawned[0]["Location"].X,
                               niagara.spawned[0]["Location"].Y,
                               niagara.spawned[0]["Location"].Z) == hand)
check("it is NS_Grapple_Beam, the effect the game's settings name",
      niagara.spawned[0]["SystemTemplate"] is game.beam_effect())
# Nothing attached outlives the character; a free one would pile up, and this build offers no way
# to destroy one by hand.
check("and it takes itself away once deactivated", niagara.spawned[0]["bAutoDestroy"] is True)
check("which way was used is written", any("spawned loose" in line for line in state["misc"]))
# The one field of 173 that differed and was neither identity nor of the mod's own making: the game
# places its rope facing its anchor, and the mod placed its own facing nothing at all.
turned = niagara.spawned[0]["Rotation"]
check("and it is placed facing the anchor, as the game places its own",
      abs(turned.Yaw) > 0.01 or abs(turned.Pitch) > 0.01)
check("the fields the game's rope carries and a bare spawn does not are copied",
      beam._component.bVisibleInRayTracing is True)
# Preserve initialization order while changing the coordinate convention.
check("it is not lit on the spot", niagara.spawned[0]["bAutoActivate"] is False)
check("its far end is the hand-to-anchor length", any(n == niagara.end_name and math.isclose(v.X, math.sqrt(66125.0)) for n, v in niagara.set))
check("and its near end is written", any(n == niagara.source_name for n, v in niagara.set))
check("written on the effect itself, the library having no position setter at all",
      rope_ends._setter == "component.SetVariablePosition")

# The names are read from the effect itself, never guessed: eight guessed ones all failed.
check("the effect's own parameter names are written",
      any("Color Scale" in line and "User.Target" in line for line in state["misc"]))
check("the name it answered to is written", any("takes its far end as" in line for line in state["misc"]))
check("and it is the one the setter really wants", beam._end_name == niagara.end_name)
check("the names are read out of what the effect prints, prefix and spaces kept",
      rope_ends.parameter_names("[{Name: 'User.Beam End'}, {Name: 'User.Color Scale'}]")
      == ["User.Beam End", "User.Color Scale"])
# The whole store goes to the log too: the mod writes two of the effect's eleven parameters, and a
# width of zero is invisible in exactly the way a rope written to the wrong place is.
check("what the asset itself carries is written down",
      any("grapple beam defaults" in line for line in state["misc"]))

component = beam._component
check("it is lit once both ends are written", component.lit_with is not None)
check("and by then it holds the rope length",
      any(name == niagara.end_name and math.isclose(value.X, math.sqrt(66125.0)) for name, value in component.lit_with))
check("and the hand with it", any(name == niagara.source_name for name, value in component.lit_with))

before = len(niagara.set)
beam.follow((1.0, 1.0, 1.0), (500.0, 0.0, 0.0))
check("both ends follow on the next frame", len(niagara.set) == before + 2)
check("without searching again", sum("takes its far end as" in line for line in state["misc"]) == 1)

beam.start(player, (1.0, 2.0, 3.0))
check("a second start while it is up spawns nothing more", len(niagara.spawned) == 1)

beam.stop()
check("stopping destroys the effect", len(state["destroyed"]) == 1)
beam.stop()
check("a second stop does nothing", len(state["destroyed"]) == 1)

# An effect whose far end goes by no name we know is still drawn, and says so.
beam.reset()
niagara.end_name = niagara.source_name = "SomethingElseEntirely"
state["errors"].clear()
beam.start(player, (0.0, 0.0, 0.0))
check("an unknown far end does not stop the beam", len(niagara.spawned) == 2)
check("and it is written, with one refusal per way of writing",
      any("nothing sets the grapple beam far end" in line and "Refusals:" in line
          for line in state["errors"]))
check("a way of writing that does not exist at all is named too",
      any("library.SetNiagaraVariablePosition" in line for line in state["errors"]))
check("and what the effect and the library really offer is written down",
      sum("offers:" in line for line in state["misc"]) >= 1)
beam.stop()
niagara.end_name, niagara.source_name = "Target", "Source"

# A beam that cannot be lit costs the rope alone, and says so instead of failing silently.
beam.reset()
niagara.spawned.clear()
state["errors"].clear()
broken = niagara._component
def no_switch():
    component = broken()
    del component.Activate
    return component


niagara._component = no_switch
beam.start(player, (0.0, 0.0, 0.0))
check("a beam with no way of being lit is written down once",
      sum("could not be lit" in line for line in state["errors"]) == 1)
niagara._component = broken
beam.stop()

# A build without the free spawn still gets a rope, the old way.
beam.reset()
niagara.spawned.clear()
niagara.loose_fails = True
state["errors"].clear()
beam.start(player, (0.0, 0.0, 0.0))
check("a game with no free spawn falls back to the player", niagara.spawned[0]["how"] == "attached")
check("and says so rather than failing", any("spawned attached" in line for line in state["misc"]))
check("nothing is written as an error", not state["errors"])
beam.stop()
niagara.loose_fails = False

# The effect missing from the game must cost the rope alone, never the pull.
beam.reset()
state["objects"].pop(("NiagaraSystem", "/Game/PlayerCharacters/_Shared/Skills/Effects/Systems/GrappleGrabber/"
                                       "NS_Grapple_Beam.NS_Grapple_Beam"))
game.forget()
state["errors"].clear()
beam.start(player, (0.0, 0.0, 0.0))
check("an effect the game has not loaded says so instead of raising",
      any("NS_Grapple_Beam was not found" in line for line in state["errors"]))
beam.follow((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
check("and there is no effect left to follow", beam._component is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
