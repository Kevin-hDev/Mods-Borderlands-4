"""Tests the shot: where the ray lands, what it says it hit, and the rule that saves the punch."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import aim  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
kismet = state["kismet"]

kismet.hit = (500.0, "StaticMeshActor")
shot = aim.look(player, (0.0, 0.0, 100.0), (1.0, 0.0, 0.0), 3000.0)
check("a ray that meets a wall gives its distance", shot is not None and shot.distance == 500.0)
check("the anchor sits where the ray stopped", shot.anchor == (500.0, 0.0, 100.0))
check("it says what it met", shot.hit_name == "StaticMeshActor")
check("the ray goes out to the full range", kismet.calls[-1][1].X == 3000.0)
check("on the channel that sees the game's blocking panels", kismet.calls[-1][2] == aim.TRACE_CHANNEL)

kismet.hit = (197.0, "LootableObject", "IO_TranshumanistShrine_UAID_123")
identified = aim.look(player, (0.0, 0.0, 100.0), (1.0, 0.0, 0.0), 3000.0)
check("the ray keeps the shrine instance family", identified is not None and
      identified.hit_object_name == "IO_TranshumanistShrine_UAID_123")

kismet.hit = None
check("a ray that meets nothing gives nothing", aim.look(player, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 3000.0) is None)

kismet.hit = (700.0, "")
blind = aim.look(player, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 3000.0)
check("a hit the game will not name still gives an anchor", blind is not None and blind.anchor == (0.0, 0.0, 700.0))
check("and its name is simply empty", blind.hit_name == "")

check("a character reads as alive", aim.is_being("BPChar_Enemy_Ripper"))
check("a pawn reads as alive", aim.is_being("AIPawn_Basic"))
check("a vehicle reads as alive", aim.is_being("Vehicle_Outrunner"))
check("a wall does not", not aim.is_being("StaticMeshActor"))
check("nothing at all does not", not aim.is_being(""))
check("the observed OakSpawnPoint is not a pawn", not aim.is_being("OakSpawnPoint"))
check("spawn points remain nonliving with lowercase names", not aim.is_being("oakspawnpoint"))
check("a real pawn with Spawn in its name stays living", aim.is_being("SpawnedAIPawn"))
check("a character with Spawn in its name stays living", aim.is_being("BPChar_SpawnGuard"))
check("the observed OakCharacter stays living", aim.is_being("OakCharacter"))

surface = aim.Shot(anchor=(0.0, 0.0, 0.0), distance=800.0, hit_name="StaticMeshActor")
enemy = aim.Shot(anchor=(0.0, 0.0, 0.0), distance=800.0, hit_name="BPChar_Enemy_Ripper")
near_wall = aim.Shot(anchor=(0.0, 0.0, 0.0), distance=90.0, hit_name="StaticMeshActor")
shrine = aim.Shot(anchor=(0.0, 0.0, 0.0), distance=197.0, hit_name="LootableObject",
                  hit_object_name="IO_TranshumanistShrine_UAID_123")
ordinary_loot = aim.Shot(anchor=(0.0, 0.0, 0.0), distance=197.0, hit_name="LootableObject",
                         hit_object_name="LootableObject_123")

check("a surface is grappled", aim.grapples(surface, 200.0, True))
nest = aim.Shot(anchor=surface.anchor, distance=800.0, hit_name="OakSpawnPoint")
check("a distant spawn point hit no longer yields a punch", aim.grapples(nest, 200.0, True, True))
check("an enemy is punched", not aim.grapples(enemy, 200.0, True))
check("an enemy is grappled when the punch is turned off", aim.grapples(enemy, 200.0, False))
check("known nearby walls can be grappled", aim.grapples(near_wall, 200.0, True))
check("nearby walls remain grappleable with melee priority disabled", aim.grapples(near_wall, 200.0, False))
check("a Transhumanist shrine keeps its native melee interaction", not aim.grapples(shrine, 200.0, True))
check("an ordinary lootable surface remains grappleable", aim.grapples(ordinary_loot, 200.0, True))
check("nothing aimed at is punched, which is what the game does", not aim.grapples(None, 200.0, True))

# The game's own grapple points: kept for the game when the player asked to keep them.
pad = aim.Shot(anchor=(0.0, 0.0, 0.0), distance=800.0, hit_name="BP_GrapplePoint_C")
check("a game grapple point reads as one", aim.is_game_grapple("BP_GrapplePoint_C"))
check("a plain wall does not", not aim.is_game_grapple("StaticMeshActor"))
check("by default the mod takes the game's pads too, so there is one grapple and not two",
      aim.grapples(pad, 200.0, True))
check("asked to keep them, the mod stands aside on a pad",
      not aim.grapples(pad, 200.0, True, keep_game_grapple=True))
check("and still takes an ordinary wall", aim.grapples(surface, 200.0, True, keep_game_grapple=True))
check("an enemy is still punched, whatever that setting says",
      not aim.grapples(enemy, 200.0, True, keep_game_grapple=True))

# The ray almost never meets the point itself: of 24 shots at the game's own pads, 13 met the level
# cell behind it, 9 a static mesh and 2 the point. So the point is looked for near the aimed spot.
wall = aim.Shot(anchor=(1000.0, 0.0, 200.0), distance=1000.0, hit_name="GbxPackedLevelStreamingCell")
state["points"] = [sdk_stubs.FakePoint(1050.0, 0.0, 220.0)]
check("a point near the aimed spot is found", aim.game_point_near(wall.anchor))
check("so the mod stands aside on a pad even when the ray met the wall behind it",
      not aim.grapples(wall, 200.0, True, keep_game_grapple=True))
check("and it takes it when the player did not ask to keep the game's",
      aim.grapples(wall, 200.0, True, keep_game_grapple=False))
state["points"] = [sdk_stubs.FakePoint(9000.0, 9000.0, 9000.0)]
check("a point far away is not the thing aimed at", not aim.game_point_near(wall.anchor))
check("so the mod takes the shot", aim.grapples(wall, 200.0, True, keep_game_grapple=True))
state["points"] = []
check("a level with no points leaves the shot to the mod", aim.grapples(wall, 200.0, True, keep_game_grapple=True))
check("how many the level holds is written once",
      sum("the game's grapple points" in line for line in state["misc"]) == 1)

state["points_raise"] = True
state["errors"].clear()
check("a level that will not answer does not swallow the shot", aim.grapples(wall, 200.0, True, keep_game_grapple=True))
check("and the failure is written", any("could not be listed" in line for line in state["errors"]))
state["points_raise"] = False

# Bounded: a runaway list must not freeze a key press.
state["points"] = [sdk_stubs.FakePoint(9000.0, 9000.0, 9000.0) for _ in range(aim.MAX_POINTS + 200)]
check("a level full of points is not walked to the end", not aim.game_point_near(wall.anchor))
state["points"] = []

# What the game answers here is not established, so the first names go to the log to be read later.
aim.reset()
state["misc"].clear()
kismet.hit = (500.0, "StaticMeshActor")
aim.look(player, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 3000.0)
aim.look(player, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 3000.0)
check("what was aimed at is written once, not once per shot",
      sum("aimed at StaticMeshActor" in line for line in state["misc"]) == 1)
kismet.hit = (500.0, "BPChar_Enemy_Ripper")
aim.look(player, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 3000.0)
check("a new kind is written too", any("aimed at BPChar_Enemy_Ripper" in line for line in state["misc"]))

for number in range(aim.MAX_NAMED + 10):
    kismet.hit = (500.0, f"Thing_{number}")
    aim.look(player, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 3000.0)
check("the list of names is bounded", len(aim._named) <= aim.MAX_NAMED)

aim.reset()
state["misc"].clear()
try:
    aim.grapples(enemy, 200.0, True, explain=True)
    unknown_near = aim.Shot(anchor=near_wall.anchor, distance=90.0, hit_name="")
    aim.grapples(unknown_near, 200.0, True, explain=True)
    aim.grapples(None, 200.0, True, explain=True)
    aim.grapples(pad, 200.0, True, True, explain=True)
    check("a refusal records its reason and measured distance",
          any("living target" in line and "BPChar_Enemy_Ripper" in line and "800" in line
              for line in state["misc"]))
    for reason in ("too close", "no surface in range", "native grapple"):
        check(f"refusal is explained: {reason}", any(reason in line for line in state["misc"]))
    before = len(state["misc"])
    aim.grapples(nest, 200.0, True, explain=True)
    check("an accepted nest hit is not logged as refused", len(state["misc"]) == before)
    for _ in range(aim.MAX_REFUSALS + 10):
        aim.grapples(enemy, 200.0, True, explain=True)
    check("refusal logging stops at its budget", len(state["misc"]) == aim.MAX_REFUSALS)
except TypeError:
    check("press refusal diagnostics are available", False)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
