"""Tests the enemies' staggers made rarer (normal/staggers.py) on fake settings: at the game's own factor nothing found
nor written; the loaded asset's two chances times the level's, announced before, the class's default object never
touched; a pass that finds ours writes nothing again; while the asset held lives no search is made again (audit of
24 October 2026, N1), once it is gone the asset loaded again with the game's is found and gets ours at the next pass;
the game's first read kept for the next play, which never takes ours for the game's; a play that finds ours left
holds them and gives them back; at the end the game's given back, an asset changed since left, one gone said so;
nothing written, "none"; the settings unfound said, not raised."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows.normal import staggers  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Settings:
    def __init__(self, name: str) -> None:
        self.Name, self.StaggerChance, self.LaunchChance = name, 0.4, 0.2


calls: list[tuple] = []


def announce(call: str, **fields: object) -> None:
    calls.append((call, fields))


def chances(asset: Settings) -> tuple:
    return round(asset.StaggerChance, 4), round(asset.LaunchChance, 4)


asset, default = Settings("HitReactionSettings"), Settings("Default__OakHitReactionSettings")
state["all"]["OakHitReactionSettings"] = [default, asset]
searched: list[str] = []
finding = sys.modules["unrealsdk"].find_all
sys.modules["unrealsdk"].find_all = lambda name, exact=True: (searched.append(name), finding(name, exact))[1]

try:
    game = staggers.Staggers(1.0, announce)
    check("at the game's factor nothing written", game.keep() == {} and calls == [] and game.put_back() == "none")
    play = staggers.Staggers(0.5, announce)
    kept = play.keep()
    check("the chances times the level's, the default object untouched", chances(asset) == (0.2, 0.1)
          and chances(default) == (0.4, 0.2) and kept == {"staggers": 0.5, "written": ["HitReactionSettings"]})
    check("announced before", calls == [("set_hit_reaction_chances", {"asset": "HitReactionSettings",
                                                                      "StaggerChance": 0.2, "LaunchChance": 0.1})])
    check("a pass that finds ours writes nothing, and searches nothing: the asset is held",
          play.keep() == {} and len(calls) == 1 and searched == [staggers.ASSET_CLASS])
    reloaded = Settings("HitReactionSettings")
    state["all"]["OakHitReactionSettings"] = [default, reloaded]
    check("while the asset held lives, it is the one read", play.keep() == {} and chances(reloaded) == (0.4, 0.2)
          and len(searched) == 1)
    asset.freed = True
    check("once gone, the asset loaded again is found and gets ours at the next pass",
          play.keep()["written"] == ["HitReactionSettings"] and chances(reloaded) == (0.2, 0.1) and len(searched) == 2)
    check("at the end the game's given back", play.put_back() == {"HitReactionSettings": "given_back"}
          and chances(reloaded) == (0.4, 0.2) and calls[-1][1]["StaggerChance"] == 0.4)
    check("given back once: then none", play.put_back() == "none")
    left = staggers.Staggers(0.5, announce)
    left.keep()
    after = staggers.Staggers(0.5, announce)
    count = len(calls)
    check("a play that finds ours left holds them, writes nothing", after.keep() == {} and len(calls) == count)
    check("and gives them back", after.put_back() == {"HitReactionSettings": "given_back"}
          and chances(reloaded) == (0.4, 0.2))
    zero = staggers.Staggers(0.0, announce)
    zero.keep()
    check("Predator's no staggers: both zero", chances(reloaded) == (0.0, 0.0))
    other = staggers.Staggers(0.75, announce)
    other.keep()
    check("the next play takes the game's first read, not ours", chances(reloaded) == (0.0, 0.0)
          and other.put_back() == "none")
    zero.put_back()
    check("given back from zero", chances(reloaded) == (0.4, 0.2))
    other.keep()
    reloaded.StaggerChance = 0.9
    check("an asset changed since left", other.put_back() == {"HitReactionSettings": "changed"}
          and reloaded.StaggerChance == 0.9)
    reloaded.StaggerChance, reloaded.LaunchChance = 0.4, 0.2
    other.keep()
    state["all"]["OakHitReactionSettings"] = [default]
    check("an asset gone said so", other.put_back() == {"HitReactionSettings": "gone"})
    sys.modules["unrealsdk"].find_all = lambda name, exact=True: (_ for _ in ()).throw(RuntimeError("no"))
    check("the settings unfound said, not raised",
          staggers.Staggers(0.5, announce).keep() == {"refused": "unfound:RuntimeError"})
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
