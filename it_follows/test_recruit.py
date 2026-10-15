"""Tests the recruiter on the real census: a census due once every 5 s and not before, counted when made; the enemies
kept around the hunter not yet taken, nearest first, at most the room left, without any cap on a run, read within
0.25 s; what the census read, why it passed the others over (trial 8e) and how long it took said, without a list of
names; who the census saw alive and dead handed on; nobody without a place, or without the hunter's; no game object
kept between censuses."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

player = sdk_stubs.FakeCharacter()
state = sdk_stubs.install(player)

from census_fixture import CAT, PSYCHO, YOUNG_CAT, Zone, enemy  # noqa: E402
from it_follows import census, recruit  # noqa: E402

ORIGIN = (0.0, 0.0, 0.0)
fails: list[str] = []
calls: list = []
real_seen_around = census.seen_around


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def seen_around(target: object, seconds: float | None = None, known: frozenset = frozenset()) -> tuple:
    """The real census, its arguments written down."""
    calls.append((target, seconds) if not known else (target, seconds, known))
    return real_seen_around(target, seconds, known=known)


def names(seens: list) -> list[str]:
    return [seen.name for seen in seens]


census.seen_around = seen_around
try:
    state["all"]["OakCharacter"] = [
        player,
        enemy("far", 9000.0, PSYCHO, Zone(9000.0, "OakSpawner_A")),
        enemy("near", 1000.0, CAT, Zone(1000.0, "OakSpawner_B")),
        enemy("taken", 500.0, PSYCHO, Zone(500.0, "OakSpawner_C")),
        enemy("nowhere", None, PSYCHO, Zone(700.0, "OakSpawner_D")),
        enemy("mid", 4000.0, PSYCHO, Zone(4000.0, "OakSpawner_E")),
        *(enemy(f"Char_CatYoung_{number}", 380000.0, YOUNG_CAT, None) for number in range(3)),
        enemy("gone", 200.0, PSYCHO, Zone(200.0, "OakSpawner_F"), is_dead=True),
    ]
    recruiter = recruit.Recruiter(100.0)
    check("no census before 5 s", not recruiter.due(104.9))
    check("one once 5 s have passed, then not again at once",
          recruiter.due(105.0) and not recruiter.due(105.1) and recruiter.due(110.0))
    chosen, said, sighting = recruiter.choose(player, ORIGIN, {"taken"}, 2)
    check("the enemies not taken, with a place, nearest first, at most the room left",
          names(chosen) == ["near", "mid"] and recruiter.joined == 2)
    counts = {key: said.get(key) for key in ("read", "kept", "stopped")}
    check("the census is read within 0.25 s, its counts said",
          calls == [(player, 0.25)] and counts == {"read": 10, "kept": 5, "stopped": "complete"}
          and said.get("took_ms", -1.0) >= 0.0)
    check("trial 8e: and why the others were passed over",
          said.get("skipped") == {f"in_reserve:{YOUNG_CAT}": 3, "dead_or_unknown": 1})
    check("only these few fields are said, never a list of names",
          set(said) == {"read", "kept", "skipped", "stopped", "took_ms"})
    check("who the census saw alive and dead is handed on",
          sighting.alive == frozenset({"far", "near", "taken", "nowhere", "mid"})
          and sighting.dead == frozenset({"gone"}))
    calls.clear()
    _, said, sighting = recruiter.choose(player, ORIGIN, {"taken"}, 0, known={"taken"})
    check("the horde's own handed to the census: read alive, never kept",
          calls == [(player, 0.25, {"taken"})] and said["kept"] == 4 and "taken" in sighting.alive)
    check("decision 97: only those keep says yes to, nearest first, at most the room",
          names(recruiter.choose(player, ORIGIN, {"taken"}, 5, keep=lambda seen: seen.name != "near")[0][:1])
          == ["mid"] and "near" not in names(recruiter.choose(player, ORIGIN, set(), 5,
                                                               keep=lambda seen: seen.name != "near")[0]))
    recruiter.joined = 2
    check("no room, nobody", recruiter.choose(player, ORIGIN, set(), 0)[0] == [] and recruiter.joined == 2)
    check("a room below nothing, nobody",
          recruiter.choose(player, ORIGIN, set(), -1)[0] == [] and recruiter.joined == 2)
    check("without the hunter's place, nobody",
          recruiter.choose(player, None, set(), 5)[0] == [] and recruiter.joined == 2)
    recruiter.joined = 600
    check("no cap on a run: past the trials' 600, the enemies still join, each one counted",
          names(recruiter.choose(player, ORIGIN, set(), 5)[0]) == ["taken", "near", "mid", "far"]
          and recruiter.joined == 604)
    check("and a census is still due", recruiter.due(10_000.0))
    check("no game object is kept between censuses", set(vars(recruiter)) == {"read_at", "joined"})
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")
finally:
    census.seen_around = real_seen_around

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
