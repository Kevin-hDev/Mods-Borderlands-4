"""Tests the census on the kinds table the mod ships: who is kept (living enemies of every team, flyers and enemies
without a zone standing in the world among them) and who is passed over, counted by reason with its kind once read
(dead, unknown kind, NPC, boss, zone unreadable, reserve, world event, radius unreadable), the death first, then the
kind, then the zone; an unreadable definition passed over without stopping the census; who was seen alive and dead, by
name; the horde of every team, nearest the hunter first; the census's limits in characters and time. Asked for the
bosses (the normal mode, decision 90), a living boss is kept, marked, without its zone even where it has one or the
game refuses it; a dead one still passed over; the Horde's census never keeps one. Asked who killed (the Hardcore),
each enemy and boss read dead with what KillerActor and LastHitBy say, never an NPC; not asked, nothing read. Asked
for the world only (the Horde, decision 105), the characters of the world in play, the bodies in the game's reserve
left out; otherwise every character the game holds; the way said."""

import dataclasses
import itertools
import math
import pathlib
import sys
import time
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

player = sdk_stubs.FakeCharacter()
state = sdk_stubs.install(player)

from census_fixture import BAT, BOSS, CAT, EVENTS, NPC, PSYCHO, UNKNOWN, WORLD, Zone, enemy  # noqa: E402
from it_follows import census, seen as seen_module  # noqa: E402

ORIGIN = (0.0, 0.0, 0.0)
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def read(*characters: object, seconds: float | None = None, bosses: bool = False) -> tuple:
    """A census of the player and these characters, in this order."""
    state["all"]["OakCharacter"] = [player, *characters]
    return census.seen_around(player, seconds, bosses=bosses) if bosses else census.seen_around(player, seconds)


def names(seens: list) -> list[str]:
    return [seen.name for seen in seens]


def camp_zone(name: str) -> str:
    return f"{WORLD}.OakSpawner_{name}.Territory"


def dead_crowd(count: int) -> object:
    """count dead characters, each of its own name, made only as the census reads them."""
    return (enemy(f"Char_Dead_{number}", 100.0, CAT, None, is_dead=True) for number in range(count))


try:
    camp = Zone(2000.0, "OakSpawner_Camp")
    host = enemy("Char_Psycho_1", 2500.0, PSYCHO, camp)
    mover = enemy("Char_Psycho_2", 20000.0, PSYCHO, Zone(21000.0, "OakSpawner_A"))
    too_close = enemy("Char_Psycho_3", 16900.0, PSYCHO, Zone(17500.0, "OakSpawner_B"))
    farther = enemy("Char_Psycho_4", 30000.0, PSYCHO, Zone(31000.0, "OakSpawner_C"))
    other_team = enemy("Char_Cat_5", 18000.0, CAT, Zone(24000.0, "OakSpawner_D"))
    left_out = {
        "a world event's enemy": enemy("Char_Psycho_6", 600.0, PSYCHO, Zone(500.0, "SL_Events_Camp", folder=EVENTS)),
        "an enemy in the game's reserve": enemy("Char_Psycho_7", 380000.0, PSYCHO, None),
        "a dead enemy": enemy("Char_Psycho_8", 100.0, PSYCHO, Zone(0.0, "OakSpawner_E"), is_dead=True),
        "an enemy whose state the game does not say": enemy("Char_Psycho_9", 100.0, PSYCHO,
                                                            Zone(0.0, "OakSpawner_F"), is_dead=None),
        "an NPC": enemy("Char_MissionNPC_10", 100.0, NPC, Zone(100.0, "OakSpawner_G")),
        "a boss": enemy("Char_CatBoss_11", 50.0, BOSS, Zone(50.0, "OakSpawner_H")),
        "a zone whose radius cannot be read": enemy("Char_Psycho_13", 90.0, PSYCHO,
                                                    Zone(90.0, "OakSpawner_J", radius_cm=None)),
        "an enemy whose zone the game refuses": enemy("Char_Psycho_14", 90.0, PSYCHO, RuntimeError("no")),
        "a class default": enemy("Default__OakCharacter", 0.0, PSYCHO, Zone(0.0, "OakSpawner_K")),
    }
    flyer = enemy("Char_Bat_12", 80.0, BAT, Zone(80.0, "OakSpawner_I"))
    homeless = enemy("Char_Psycho_15", 5000.0, PSYCHO, None)
    found, stats, sighting = read(host, mover, too_close, farther, other_team, *left_out.values(), flyer, homeless)
    kept = names(found)
    check("living enemies of every team are kept, the reading complete",
          kept == ["Char_Psycho_1", "Char_Psycho_2", "Char_Psycho_3", "Char_Psycho_4", "Char_Cat_5", "Char_Bat_12",
                   "Char_Psycho_15"] and stats["stopped"] == "complete")
    check("each is It Follows' own Seen, without a team",
          all(type(seen) is seen_module.Seen for seen in found) and not hasattr(found[0], "team"))
    check("trial 6r: a flyer is kept, said not to walk by the kinds table; the walkers walk",
          found[5].walks is False and found[5].zone_path.endswith("OakSpawner_I.Territory")
          and all(seen.walks is True for seen in found[:5]))
    check("trial 6r: an enemy without a zone standing in the world is kept, without zone, centre or radius",
          found[6].zone is None and found[6].zone_path == "" and found[6].centre is None and found[6].radius_m == 0.0
          and found[6].at == (5000.0, 0.0, 0.0) and found[6].walks is True)
    for label, pawn in left_out.items():
        check(f"{label} is left out", pawn.Name not in kept)
    check("the player is left out", all(seen.actor is not player for seen in found))
    check("trial 6p: why each character was passed over is counted, with its kind once read; neither the player nor a "
          "class default", stats["skipped"] == {
              f"world_event:{PSYCHO}": 1, f"in_reserve:{PSYCHO}": 1, "dead_or_unknown": 2, f"not_enemy:{NPC}": 1,
              f"boss:{BOSS}": 1, f"radius_unreadable:{PSYCHO}": 1, f"zone_unreadable:{PSYCHO}": 1}
          and stats["read"] == 17 and stats["kept"] == 7)
    check("a kept enemy carries its actor, its zone, the zone's centre and radius in metres, and where it stands",
          found[0].actor is host and found[0].zone is camp and found[0].zone_path == camp.path
          and found[0].centre == (2000.0, 0.0, 0.0) and found[0].radius_m == 30.0
          and found[0].at == (2500.0, 0.0, 0.0) and found[0].definition == PSYCHO)
    check("the zone of a character not said alive is never asked: the game reuses a dead one's body",
          left_out["a dead enemy"].asks == 0 and left_out["an enemy whose state the game does not say"].asks == 0)
    check("the sighting names the enemies kept, alive, and the characters read dead",
          sighting.alive == frozenset(kept) and sighting.dead == frozenset({"Char_Psycho_8"}))
    check("decisions 56 and 68: the sighting gives each kept enemy's name, kind, zone path and place, in the census's "
          "order, for the kinds "
          "of the place; an enemy without a zone with an empty path",
          sighting.kept == tuple((seen.name, seen.definition, seen.zone_path, seen.at) for seen in found)
          and sighting.kept[5] == (found[5].name, BAT, found[5].zone_path, found[5].at)
          and sighting.kept[6] == (found[6].name, PSYCHO, "", found[6].at) and found[6].at is not None)

    skipped: dict = {}
    for number in range(census.MAX_SKIPPED_KINDS + 3):
        census._tally(skipped, f"no_zone:Char_{number}")
    census._tally(skipped, "no_zone:Char_0")
    check("at most 24 reasons are named, the later ones counted as other",
          len(skipped) == 25 and skipped["other"] == 3 and skipped["no_zone:Char_0"] == 2)

    cat_near = seen_module.Seen(None, "cat_near", CAT, None, camp_zone("Cats"), (500.0, 0.0, 0.0), 30.0,
                                (600.0, 0.0, 0.0))
    check("trial 6o: the horde is every enemy kept, of every team, a flyer too, nearest the hunter first",
          names(census.everyone([*found, cat_near], ORIGIN, 12))
          == ["Char_Bat_12", "cat_near", "Char_Psycho_1", "Char_Psycho_15", "Char_Psycho_3", "Char_Cat_5",
              "Char_Psycho_2", "Char_Psycho_4"])
    check("at most the limit, the nearest kept",
          names(census.everyone(found, ORIGIN, 3)) == ["Char_Bat_12", "Char_Psycho_1", "Char_Psycho_15"])
    check("nearest the hunter wherever he stands",
          names(census.everyone(found, (20000.0, 0.0, 0.0), 3)) == ["Char_Psycho_2", "Char_Cat_5", "Char_Psycho_3"])
    every = census.everyone(found, ORIGIN, 12)
    within = names(census.everyone(found, ORIGIN, 12, 30.0))
    check("decision 97: within a distance when asked, nearest first",
          within == [seen.name for seen in every if math.dist(seen.at, ORIGIN) <= 3000.0]
          and 0 < len(within) < len(every))
    lost_bat = census._kept(enemy("Char_Bat_16", 6000.0, BAT, None), "Char_Bat_16", ORIGIN, False)
    check("a flyer without a zone in the world is kept, said not to walk",
          isinstance(lost_bat, seen_module.Seen) and lost_bat.zone is None and lost_bat.walks is False)
    unseen = seen_module.Seen(None, "unseen", PSYCHO, None, camp_zone("Elsewhere"), (900.0, 0.0, 0.0), 30.0, None)
    loner = seen_module.Seen(None, "loner", PSYCHO, None, f"{WORLD}.GbxTerritory_2147478961.Territory",
                             (300.0, 0.0, 0.0), 70.0, (300.0, 0.0, 0.0))
    check("an enemy whose place is unknown is not drawn; one whose zone is part of no camp is",
          names(census.everyone([unseen, loner, found[0]], ORIGIN, 6)) == ["loner", "Char_Psycho_1"])
    check("without the hunter's position or any enemy nothing is drawn",
          census.everyone(found, None, 6) == [] and census.everyone([], ORIGIN, 6) == [])

    long_name = "Char_" + "Q" * 100
    found, stats, _ = read(
        enemy("Char_Blank_20", 70.0, None, Zone(70.0, "OakSpawner_M")),
        enemy("Char_Broken_21", 70.0, RuntimeError("no"), Zone(70.0, "OakSpawner_N")),
        enemy("Char_Odd_22", 70.0, UNKNOWN, Zone(70.0, "OakSpawner_O")),
        enemy("Char_Odd_23", 70.0, long_name, Zone(70.0, "OakSpawner_P")),
        enemy("Char_Psycho_24", 90.0, PSYCHO, Zone(90.0, "OakSpawner_R", radius_cm=math.inf)),
        enemy("Char_Cat_25", 300.0, CAT, Zone(300.0, "OakSpawner_S")))
    check("a definition that cannot be read is an unknown kind, and the census goes on (the trials raised KeyError)",
          stats["skipped"].get("unknown_kind:?") == 2 and names(found) == ["Char_Cat_25"]
          and stats["stopped"] == "complete")
    check("a definition the kinds table does not know is an unknown kind, named by its first 60 characters; a radius "
          "that is not finite cannot be read",
          stats["skipped"] == {"unknown_kind:?": 2, f"unknown_kind:{UNKNOWN}": 1, f"unknown_kind:{long_name[:60]}": 1,
                               f"radius_unreadable:{PSYCHO}": 1})

    ordered = [enemy("Char_CatBoss_30", 50.0, BOSS, RuntimeError("no"), is_dead=True),
               enemy("Char_Blank_31", 50.0, None, RuntimeError("no"), is_dead=None),
               enemy("Char_Odd_32", 50.0, UNKNOWN, RuntimeError("no")),
               enemy("Char_MissionNPC_33", 380000.0, NPC, None),
               enemy("Char_CatBoss_34", 50.0, BOSS, RuntimeError("no"))]
    found, stats, _ = read(*ordered)
    check("the death is checked first, then the kind, then the zone: a dead boss is dead, an NPC in the reserve an "
          "NPC, a boss whose zone the game refuses a boss",
          found == [] and stats["skipped"] == {"dead_or_unknown": 2, f"unknown_kind:{UNKNOWN}": 1,
                                               f"not_enemy:{NPC}": 1, f"boss:{BOSS}": 1})
    check("the zone of a character passed over for its death or its kind is never asked",
          all(pawn.asks == 0 for pawn in ordered))

    bosses = [enemy("Char_CatBoss_35", 4000.0, BOSS, Zone(4000.0, "OakSpawner_Y")),
              enemy("Char_CatBoss_36", 50.0, BOSS, RuntimeError("no")),
              enemy("Char_CatBoss_37", 50.0, BOSS, Zone(50.0, "OakSpawner_Z"), is_dead=True),
              enemy("Char_Psycho_38", 90.0, PSYCHO, Zone(90.0, "OakSpawner_Q"))]
    found, stats, sighting = read(*bosses, bosses=True)
    check("asked for the bosses: the living ones kept, marked, without their zone, never asked for it",
          names(found) == ["Char_CatBoss_35", "Char_CatBoss_36", "Char_Psycho_38"]
          and [seen.boss for seen in found] == [True, True, False]
          and found[0].zone is None and found[0].zone_path == "" and found[0].at == (4000.0, 0.0, 0.0)
          and bosses[0].asks == 0 and bosses[1].asks == 0)
    check("a dead boss still passed over and read dead", stats["skipped"] == {"dead_or_unknown": 1}
          and sighting.dead == frozenset({"Char_CatBoss_37"}))
    pc = types.SimpleNamespace(Pawn=player)
    victim = enemy("Char_Psycho_39", 90.0, PSYCHO, None, is_dead=True)
    victim.KillerActor, victim.LastHitBy = player, None
    fallen = enemy("Char_CatBoss_43", 90.0, BOSS, None, is_dead=True)
    fallen.KillerActor, fallen.LastHitBy = None, pc
    extra = enemy("Char_MissionNPC_44", 90.0, NPC, None, is_dead=True)
    extra.KillerActor, extra.LastHitBy = player, None
    rival = enemy("Char_Psycho_45", 90.0, PSYCHO, None, is_dead=True)
    rival.KillerActor, rival.LastHitBy = types.SimpleNamespace(Name="Char_CatAdult_46",
                                                               Class=types.SimpleNamespace(Name="OakCharacter")), None
    state["all"]["OakCharacter"] = [player, victim, fallen, extra, rival]
    _, _, sighting = census.seen_around(player, kills=True, pc=pc)
    check("asked who killed: each enemy and boss read dead, never an NPC",
          sighting.killed == (("Char_Psycho_39", ("player", "none")), ("Char_CatBoss_43", ("none", "player")),
                              ("Char_Psycho_45", ("other:OakCharacter", "none"))))
    check("one another character killed: named with its killer", sighting.killed_by_other
          == (("Char_Psycho_45", "Char_CatAdult_46"),))
    check("not asked, nothing read", read(victim, fallen, extra)[2].killed == ())
    found, stats, _ = read(*bosses)
    check("the Horde's census never keeps one", names(found) == ["Char_Psycho_38"] and found[0].boss is False
          and stats["skipped"] == {"dead_or_unknown": 1, f"boss:{BOSS}": 2})

    found, stats, _ = read(enemy("Char_Psycho_40", 100000.0, PSYCHO, None),
                           enemy("Char_Psycho_41", 100100.0, PSYCHO, None),
                           enemy("Char_Psycho_42", None, PSYCHO, None))
    check("an enemy without a zone 1 km away stands in the world; past 1 km, or where its place cannot be read, it is "
          "in the game's reserve",
          names(found) == ["Char_Psycho_40"] and stats["skipped"] == {f"in_reserve:{PSYCHO}": 2})

    player.HealthState = types.SimpleNamespace(bCurrentlyDead=True)
    try:
        _, _, sighting = read(
            enemy("Char_Cat_50", 300.0, CAT, Zone(300.0, "OakSpawner_T")),
            enemy("Char_Cat_51", 300.0, CAT, Zone(300.0, "OakSpawner_U"), is_dead=True),
            enemy("Char_MissionNPC_52", 300.0, NPC, None, is_dead=True),
            enemy("Char_CatBoss_53", 300.0, BOSS, None, is_dead=True),
            enemy("Char_Cat_54", 300.0, CAT, Zone(300.0, "OakSpawner_V"), is_dead=None),
            enemy("Default__Char_Cat", 0.0, CAT, Zone(0.0, "OakSpawner_W"), is_dead=True),
            enemy("Char_Cat_55\r\n", 300.0, CAT, Zone(300.0, "OakSpawner_X"), is_dead=True))
    finally:
        del player.HealthState
    check("every character read dead is named, whatever its kind, its name cleaned; neither the player, a class "
          "default nor one whose death the game does not say",
          sighting.dead == frozenset({"Char_Cat_51", "Char_MissionNPC_52", "Char_CatBoss_53", "Char_Cat_55"}))
    check("the living named are the enemies kept", sighting.alive == frozenset({"Char_Cat_50"}))
    state["all"]["OakCharacter"] = [player, enemy("Char_Cat_60", 300.0, CAT, Zone(300.0, "OakSpawner_K")),
                                    enemy("Char_Cat_61", 300.0, CAT, Zone(300.0, "OakSpawner_L")),
                                    enemy("Char_Cat_62", 300.0, CAT, Zone(300.0, "OakSpawner_M"), is_dead=True)]
    found, stats, sighting = census.seen_around(player, known={"Char_Cat_60", "Char_Cat_62"})
    check("a name known read alive: seen alive, never kept nor read further; one known read dead is dead",
          names(found) == ["Char_Cat_61"] and sighting.alive == frozenset({"Char_Cat_60", "Char_Cat_61"})
          and sighting.dead == frozenset({"Char_Cat_62"}) and stats["kept"] == 1 and stats["read"] == 4)
    try:
        sighting.alive = frozenset()
        frozen = False
    except dataclasses.FrozenInstanceError:
        frozen = True
    check("a sighting cannot be changed, nor its names",
          frozen and type(sighting.alive) is frozenset and type(sighting.dead) is frozenset)

    in_reserve = enemy("Char_Cat_70", 320000.0, CAT, None, is_dead=True)
    in_world = enemy("Char_Cat_71", 300.0, CAT, Zone(300.0, "OakSpawner_N"))
    asked: list[tuple] = []

    def actors_of(*, WorldContextObject: object, ActorClass: object, OutActors: list) -> tuple:
        asked.append((WorldContextObject, ActorClass.Name))
        return ..., [player, in_world]

    state["classes"]["GameplayStatics"] = types.SimpleNamespace(
        ClassDefaultObject=types.SimpleNamespace(GetAllActorsOfClass=actors_of))
    state["classes"][census.CHARACTER_CLASS] = types.SimpleNamespace(Name=census.CHARACTER_CLASS)
    state["all"]["OakCharacter"] = [player, in_world, in_reserve]
    found, stats, sighting = census.seen_around(player, in_world=True)
    check("decision 105: asked for the world only, the characters of the hunter's world, a body in the game's "
          "reserve left out, the way said",
          names(found) == ["Char_Cat_71"] and sighting.dead == frozenset() and stats["search"] == "actors"
          and asked == [(player, census.CHARACTER_CLASS)] and stats["read"] == 2)
    found, stats, sighting = census.seen_around(player)
    check("otherwise every character the game holds, the body in the reserve read dead: the normal mode's Hardcore "
          "counts it", names(found) == ["Char_Cat_71"] and sighting.dead == frozenset({"Char_Cat_70"})
          and stats["search"] == "find_all" and len(asked) == 1)

    state["all"]["OakCharacter"] = itertools.repeat(host, 100_000)
    _, stats, _ = census.seen_around(player, 600.0)
    check("at most 1000 characters are read out of 100 000", stats["stopped"] == "scan_limit" and stats["read"] == 1000)
    state["all"]["OakCharacter"] = [host] * 1000
    _, stats, _ = census.seen_around(player, 600.0)
    check("1000 characters are read completely", stats["stopped"] == "complete" and stats["read"] == 1000)
    state["all"]["OakCharacter"] = dead_crowd(100_000)
    _, stats, sighting = census.seen_around(player, 600.0)
    check("the dead named are bounded by the scan", stats["stopped"] == "scan_limit" and len(sighting.dead) == 1000)

    ticks = itertools.count(0.0, 0.5)
    census.time = types.SimpleNamespace(monotonic=lambda: next(ticks))
    try:
        state["all"]["OakCharacter"] = dead_crowd(100)
        _, by_default, sighting = census.seen_around(player)
        ticks = itertools.count(0.0, 0.5)
        state["all"]["OakCharacter"] = dead_crowd(100)
        _, given, _ = census.seen_around(player, 1.0)
    finally:
        census.time = time
    check("by default a census reads for 3 s at most, its dead named only among those read",
          by_default["stopped"] == "time_limit" and by_default["read"] == 6 and len(sighting.dead) == 6)
    check("or for the time it is given", given["stopped"] == "time_limit" and given["read"] == 2)
    saved = census.MAX_SECONDS
    census.MAX_SECONDS = -1.0
    try:
        found, stats, sighting = read(host)
    finally:
        census.MAX_SECONDS = saved
    check("past its time limit the reading stops", stats["stopped"] == "time_limit" and found == []
          and sighting.alive == frozenset())
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
