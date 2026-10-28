"""Tests look_load.py: an object already in the game's memory is taken as it is, another is loaded through the
engine's AssetRegistryHelpers then found by its path; every missing one is named; an error of the game that is not a
missing object is not taken for one."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import look_assets, look_hook, look_load, look_rope  # noqa: E402
import look_fixture  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


HOOK = look_assets.PIECES["hook"]["mesh"]
record = look_fixture.install(state)
in_memory = types.SimpleNamespace(path=look_assets.MATERIAL)
state["objects"][(look_load.MATERIAL, look_assets.MATERIAL)] = in_memory
wanted = look_rope.wanted("A", "ORANGE") + look_hook.wanted()
found = look_load.fetch(wanted)
check("every piece the rope and the hook need is found, by its path",
      set(found) == {path for _, path in wanted} and found[HOOK].path == HOOK)
check("one already in memory is taken as it is, never loaded again",
      found[look_assets.MATERIAL] is in_memory and look_assets.MATERIAL not in record["loaded"])
check("the others are loaded through the engine, each once though the rope and the hook share some",
      len(record["loaded"]) == len(set(record["loaded"])) == len({path for _, path in wanted}) - 1)
check("C's rope also needs its glow, in the game's effect material",
      look_assets.ROPE["halo"]["material"] in {path for _, path in look_rope.wanted("C", "RED")}
      and look_assets.PIECES["rope_halo"]["mesh"] in {path for _, path in look_rope.wanted("C", "RED")}
      and look_assets.PIECES["rope_halo"]["mesh"] not in {path for _, path in look_rope.wanted("A", "RED")})
check("C in a colour needs its glow's image of that colour, A none of them",
      look_assets.ROPE["halo"]["images"]["RED"] in {path for _, path in look_rope.wanted("C", "RED")}
      and look_assets.ROPE["halo"]["images"]["GREEN"] not in {path for _, path in look_rope.wanted("C", "RED")}
      and not set(look_assets.ROPE["halo"]["images"].values())
              & {path for _, path in look_rope.wanted("A", "RED")})

# The game's memory forgets our objects; the fake SDK's modules stay those the mod imported.
OURS = {pair for pair in look_fixture.every_asset()}
for pair in OURS:
    state["objects"].pop(pair, None)
gone = (HOOK, look_assets.PIECES["rope_a"]["mesh"])
look_fixture.install(state, missing=gone)
try:
    look_load.fetch(wanted)
    missing = None
except look_load.Missing as error:
    missing = error
check("without our container, every missing piece is named, the first in the message",
      missing is not None and set(missing.paths) == set(gone) and missing.paths[0] in str(missing))

for pair in OURS:
    state["objects"].pop(pair, None)
look_fixture.install(state)


def refused(data):
    raise RuntimeError("the engine refused the request")


state["extra_classes"]["AssetRegistryHelpers"] = types.SimpleNamespace(
    ClassDefaultObject=types.SimpleNamespace(GetAsset=refused))
try:
    look_load.fetch(look_hook.wanted())
    raised = None
except look_load.Missing:
    raised = "missing"
except RuntimeError:
    raised = "failure"
check("an error of the engine is a failure, not a missing piece", raised == "failure")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
