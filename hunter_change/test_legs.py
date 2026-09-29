"""The first-person legs: found under the body mesh and scaled evenly; set back to whole; searched within a bound;
missing or refused legs said and answered false."""

import math
import sys
import types

import sdk_stubs

state = sdk_stubs.install()

import fake_game  # noqa: E402
from fake_game import rule  # noqa: E402
from hunter_change import legs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


character = fake_game.load(state, "Gravitar", "8107146506D5906AD9BCCD4479661B4D")
check("found under the body mesh and scaled evenly", legs.fit(character, 153.0 / 217.0)
      and math.isclose(fake_game.legs_scale(character), 153.0 / 217.0)
      and state["structs"][-1].struct == "Vector"
      and state["structs"][-1].X == state["structs"][-1].Y == state["structs"][-1].Z)
check("set back to whole", legs.fit(character, 1.0) and fake_game.legs_scale(character) == 1.0)

crowded = fake_game.Character([], fake_game.Legs())
crowded.Mesh.AttachChildren = [types.SimpleNamespace(Name="Other")] * legs.MAX_CHILDREN + crowded.Mesh.AttachChildren
check("searched within a bound", not legs.fit(crowded, 0.5))
crowded.Mesh.AttachChildren = []
check("missing legs said", not legs.fit(crowded, 0.5) and "legs" in state["errors"][-1])
rule["scale_refused"] = True
check("refused legs said", not legs.fit(character, 0.5) and fake_game.legs_scale(character) == 1.0
      and "refused" in state["errors"][-1])
rule["scale_refused"] = False

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
