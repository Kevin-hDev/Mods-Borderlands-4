"""Tests the kinds of the place (zone_kinds): a zone's camp read from its path; the game's enemies a census kept are
remembered where they stand, one entry each, the horde's and the copies' left out by their camp, those without a zone
kept, those without a kind or a place passed over; one met again is remembered where it stands now, once; the kinds of
the place are those met within PLACE_M of the hunter, those It Follows' camps cannot make passed over, and come back in
turn, in the share the place held them; back at a place after a fast travel, its kinds come back even when the census
meets none there (trial 15); with none met there, the killed one's own; at most MOST remembered, the one met longest
ago forgotten first; what a status line writes."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import zone_kinds  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


LEVEL = "/Game/Maps/WorldLevels/World_P.World_P:PersistentLevel"
OURS = {"OakSpawner_Host", "OakSpawner_Copy"}
START = (0.0, 0.0, 0.0)
# Trial 15: the place left before the fast travel back stood 16.8 km away; places are in centimetres.
AWAY = (1680000.0, 0.0, 0.0)


def zone(camp: str) -> str:
    return f"{LEVEL}.{camp}.Territory"


def ours(camp: str) -> bool:
    return camp in OURS


def knows(kind: str) -> bool:
    return kind != "Char_Odd"


def metres(count: float, at: tuple = START) -> tuple:
    return (at[0] + count * 100.0, at[1], at[2])


try:
    check("a camp's zone names its camp", zone_kinds.camp_of(zone("OakSpawner_2147447991")) == "OakSpawner_2147447991")
    check("no zone, no camp; a path too short has none", zone_kinds.camp_of("") == ""
          and zone_kinds.camp_of("Territory") == "")
    check("the place is 300 m around the hunter, and 2000 enemies are remembered at most",
          zone_kinds.PLACE_M == 300.0 and zone_kinds.MOST == 2000)

    kinds = zone_kinds.ZoneKinds()
    check("none met yet: no kind around, the killed one comes back as it was, and the status says none",
          kinds.around(START, knows) == [] and kinds.pick("Char_CatYoung", []) == "Char_CatYoung"
          and kinds.gauge(START) == {"kinds": 0, "met_last": 0, "remembered": 0})
    met = kinds.saw([("shotgun_1", "Char_SoldierShotgun", zone("OakSpawner_1"), metres(20.0)),
                     ("cat_horde", "Char_CatYoung", zone("OakSpawner_Host"), metres(5.0)),
                     ("bat_copy", "Char_BatBasic", zone("OakSpawner_Copy"), metres(8.0)),
                     ("striker", "Char_StrikerBasic", "", metres(40.0)),
                     ("shotgun_2", "Char_SoldierShotgun", zone("OakSpawner_2"), metres(250.0)),
                     ("nameless", "", zone("OakSpawner_3"), metres(10.0)),
                     ("nowhere", "Char_PsychoBasic_Male", zone("OakSpawner_4"), None)], ours)
    check("the game's enemies met are remembered where they stand: the horde's and the copies' left out by their camp, "
          "one without a zone kept, one without a kind or a place passed over",
          met == 3 and list(kinds.met) == ["shotgun_1", "striker", "shotgun_2"]
          and kinds.met["striker"] == ("Char_StrikerBasic", metres(40.0)))
    around = kinds.around(START, knows)
    check("the kinds of the place: one entry per enemy met within PLACE_M", around ==
          ["Char_SoldierShotgun", "Char_StrikerBasic", "Char_SoldierShotgun"])
    picked = [kinds.pick("Char_CatYoung", around) for _ in range(6)]
    check("decision 56: the killed come back as the place's kinds, in turn, in the share the place held them",
          picked == ["Char_SoldierShotgun", "Char_StrikerBasic", "Char_SoldierShotgun"] * 2)
    check("an enemy met farther than PLACE_M is not of the place",
          kinds.around(metres(-60.0), knows) == ["Char_SoldierShotgun", "Char_StrikerBasic"])
    check("the status says the kinds of the place, how many the last census met and how many are remembered",
          kinds.gauge(START) == {"kinds": 2, "met_last": 3, "remembered": 3}
          and kinds.gauge(None) == {"kinds": 0, "met_last": 3, "remembered": 3})

    kinds.saw([("striker", "Char_StrikerBasic", "", metres(500.0))], ours)
    check("one met again is remembered where it stands now, once, as the newest",
          list(kinds.met) == ["shotgun_1", "shotgun_2", "striker"] and kinds.met["striker"][1] == metres(500.0)
          and kinds.around(START, knows) == ["Char_SoldierShotgun", "Char_SoldierShotgun"])

    met = kinds.saw([("beast_1", "Char_BeastBasic", zone("OakSpawner_9"), AWAY),
                     ("beast_2", "Char_BeastBasic", zone("OakSpawner_9"), metres(30.0, AWAY))], ours)
    check("far away, the kinds of that place", met == 2
          and kinds.around(AWAY, knows) == ["Char_BeastBasic", "Char_BeastBasic"])
    met = kinds.saw([("cat_horde", "Char_CatYoung", zone("OakSpawner_Host"), metres(5.0))], ours)
    check("trial 15: back at the start by fast travel, a census meeting none of the game's enemies there, the kinds "
          "met there before come back, not those of the place left",
          met == 0 and kinds.around(metres(87.0), knows) == ["Char_SoldierShotgun", "Char_SoldierShotgun"]
          and kinds.gauge(metres(87.0)) == {"kinds": 1, "met_last": 0, "remembered": 5})
    check("a stretch where none was met: the killed one's own",
          kinds.pick("Char_BeastBasic", kinds.around(metres(900.0), knows)) == "Char_BeastBasic")

    kinds.saw([("odd", "Char_Odd", zone("OakSpawner_5"), metres(5.0, AWAY))], ours)
    check("a kind It Follows' camps cannot make is passed over",
          kinds.around(AWAY, knows) == ["Char_BeastBasic", "Char_BeastBasic"])
    lone = zone_kinds.ZoneKinds()
    lone.saw([("odd", "Char_Odd", zone("OakSpawner_5"), START)], ours)
    check("none that can be made: the killed one's own",
          lone.pick("Char_CatYoung", lone.around(START, knows)) == "Char_CatYoung")

    check("the kinds met last anywhere, the latest first, those the camps can make",
          kinds.latest(knows) == ["Char_BeastBasic", "Char_BeastBasic", "Char_StrikerBasic", "Char_SoldierShotgun",
                                  "Char_SoldierShotgun"])

    many = zone_kinds.ZoneKinds()
    met = many.saw([(f"enemy_{number}", f"Char_Kind{number}", zone(f"OakSpawner_{number}"), START)
                    for number in range(zone_kinds.MOST + 50)], ours)
    check("at most MOST remembered, the one met longest ago forgotten first",
          met == zone_kinds.MOST + 50 and len(many.met) == zone_kinds.MOST
          and "enemy_49" not in many.met and next(iter(many.met)) == "enemy_50")
    check("at most LATEST of the kinds met last", many.latest(lambda _kind: True)
          == [f"Char_Kind{number}" for number in range(zone_kinds.MOST + 49, zone_kinds.MOST + 49 - zone_kinds.LATEST,
                                                       -1)])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
