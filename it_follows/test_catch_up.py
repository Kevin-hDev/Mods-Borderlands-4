"""Tests It Follows' catch-up (catch_up) at the distances of levels 80 and 25 (decision 47: placed at 30 and 40 m,
brought back beyond 50 and 60 m). An enemy is due once farther than far_m, even one coming back, and at most once every
EVERY_S, or every DRIVING_EVERY_S while the hunter goes faster than DRIVING_M_S, his speed taken between his last two
known places, the line then saying so; it is brought back only where the hunter does not look, both where it stands
and where it goes; its new place lies on the hunter's own way, behind_m from him, between two points of that way,
SPACING_M farther along for each other enemy in the same second, PLACES at most (trial 6z bis), those never brought back
first, then the one brought back longest ago; trials 6k and 6l: never where the hunter swam, and only on the ground
found under that point (none found, or water, refused), else FARTHER_M back along his way, then (trial 6m) on a ring as
far around him out of his sight, never near where he swam, then (trial 6n) on rings RING_FARTHER_M farther out, the
ring traced from RING_UP_CM above him; the line saying where from, why each place was not taken and what was met, at
most TRACES_PER_SAMPLE traces a second for all, a search that found nothing not made again in that second; one standing
still STUCK_S farther than STUCK_NEAR_M is brought back too, said; the teleport faces the hunter, with the game's
structures, and is announced first, without a line in the log; a refused or failing teleport says so. Decision 66:
each one goes the next offset of Kevin's spread farther, and is due again only that much past far_m; a search in vain
is not made again in that second at the same offset only. His way is
forgotten when his place jumps farther than JUMP_M, no speed taken; an enemy let go is forgotten; with the real ground
trace, the enemy lands on the ground found."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import catch_up_fixture as fixture  # noqa: E402
from it_follows import catch_up as catch_module, ground as ground_module, levels, spread  # noqa: E402
from it_follows.characters import reads  # noqa: E402

fixture.keep_struct_names()
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


events: list[tuple] = []
# Decision 47: level 80 places at 30 m and brings back beyond 50 m, as the trials did; level 25 at 40 and beyond 60.
LEVEL_80 = (30.0, 50.0)
LEVEL_25 = (40.0, 60.0)
# No spread: each one at its place of the second.
FLAT = ((100, 0.0),)


def announce(call: str, log: bool = True, **fields: object) -> None:
    events.append(("announce", call, fields.get("on"), log))


def cat(name: str, answer: object = True) -> fixture.Enemy:
    return fixture.Enemy(name, answer=answer, events=events)


class Ground:
    """Stands in for ground.GroundTrace: the ground right under each point unless told otherwise per call, in turn."""

    def __init__(self, *answers: tuple) -> None:
        self.answers, self.asked, self.ups = list(answers), [], []
        self.broken: str | None = None

    @property
    def calls(self) -> int:
        return len(self.asked)

    def ground(self, name: str, mover: object, point: tuple, up_cm: float | None = None) -> tuple:
        self.asked.append(point)
        self.ups.append(up_cm)
        return self.answers.pop(0) if self.answers else ("found", point, "Landscape")


def catch_up(ground: object, level: tuple = LEVEL_80, shares: tuple = FLAT) -> catch_module.CatchUp:
    return catch_module.CatchUp(announce, ground, *level, spread.Spread(shares))


class Barren(Ground):
    """No ground anywhere while barren."""

    def __init__(self) -> None:
        super().__init__()
        self.barren = True

    def ground(self, name: str, mover: object, point: tuple, up_cm: float | None = None) -> tuple:
        if self.barren:
            self.asked.append(point)
            return "no_ground", None, None
        return super().ground(name, mover, point, up_cm)


def looking(yaw: float) -> object:
    return types.SimpleNamespace(GetControlRotation=lambda: sdk_stubs.rotator(yaw))


def run_east(catch: object, seconds: int, yaw: float = 0.0, step_cm: float = 800.0, swum: tuple = ()) -> tuple:
    """The hunter runs along +X, at 8 m/s unless told, a point a second, looking east, swimming the seconds in swum;
    his last point."""
    here = (0.0, 0.0, 100.0)
    for second in range(seconds):
        here = (second * step_cm, 0.0, 100.0)
        catch.walk(here, looking(yaw), float(second), second in swum)
    return here


def stay(catch: object, name: str, enemy: object, here: tuple, at: tuple | None, start: float, seconds: int) -> list:
    """The enemy stays at the same place for some seconds, the hunter standing still; what consider said each second."""
    return [catch.consider(name, enemy, at, here, reads.metres(at, here), start + second) for second in range(seconds)]


def behind_him(here: tuple, metres: float) -> tuple:
    return (here[0] - metres * 100.0, 0.0, 100.0)


def field(line: dict | None, key: str) -> object:
    """A field of what consider said, None when it said nothing: the check fails instead of stopping the file."""
    return None if line is None else line.get(key)


try:
    catch = catch_up(Ground())
    here = run_east(catch, 12)
    behind = behind_him(here, 200.0)
    one = cat("cat_a")
    result = catch.consider("cat_a", one, behind, here, reads.metres(behind, here), 100.0)
    check("an enemy farther than far_m is brought back at once onto the hunter's way, the teleport announced first, "
          "without a line in the log",
          result == {"catch_up": "moved", "from": "way", "spot": [58.0, 0.0, 1.0], "way": [58.0, 0.0, 1.0],
                     "met": "Landscape"}
          and events == [("announce", "K2_TeleportTo", "cat_a", False), ("teleport", "cat_a")])
    check("its new place is behind_m from the hunter, on his way, facing him, given as the game's structures",
          math.isclose(math.dist(one.went[:3], here), LEVEL_80[0] * 100.0, abs_tol=1.0)
          and one.went[1:] == (0.0, 100.0, 0.0)
          and (one.given[0].struct_name, one.given[1].struct_name) == ("Vector", "Rotator")
          and (one.given[1].Pitch, one.given[1].Roll) == (0.0, 0.0))
    check("not again before EVERY_S", catch.consider("cat_a", one, behind, here, 200.0, 101.0) is None
          and catch.consider("cat_a", one, behind, here, 200.0, 100.0 + catch_module.EVERY_S - 0.5) is None)
    check("then again", field(catch.consider("cat_a", one, behind, here, 200.0, 100.0 + catch_module.EVERY_S),
                              "catch_up") == "moved")
    gauge = catch.gauge()
    check("what each search said and the traces it took counted for the status line, then counted afresh",
          gauge["moved"] == 2 and gauge["traces"] >= 2 and catch.gauge() == {"traces": 0})

    catch = catch_up(Ground())
    here = run_east(catch, 12)
    coming = behind_him(here, 150.0)
    check("trial 6i: one coming back by itself is brought back too",
          field(catch.consider("cat_b", cat("cat_b"), coming, here, reads.metres(coming, here), 200.0), "catch_up")
          == "moved")
    near, edge = behind_him(here, 40.0), behind_him(here, LEVEL_80[1])
    check("never one within far_m, while not stuck", stay(catch, "cat_c", cat("cat_c"), here, near, 300.0, 5)
          == [None] * 5 and stay(catch, "cat_c", cat("cat_c"), here, edge, 310.0, 2) == [None] * 2)
    lower = catch_up(Ground(), LEVEL_25)
    lower_here = run_east(lower, 12)
    check("level 25: one 55 m away, or at far_m, is not brought back; one beyond 60 m is; at level 80 the one 55 m "
          "away is",
          stay(lower, "cat_p", cat("cat_p"), lower_here, behind_him(lower_here, 55.0), 320.0, 2) == [None] * 2
          and stay(lower, "cat_p", cat("cat_p"), lower_here, behind_him(lower_here, 60.0), 330.0, 2) == [None] * 2
          and lower.consider("cat_q", cat("cat_q"), behind_him(lower_here, 60.1), lower_here, 60.1, 340.0)
          == {"catch_up": "moved", "from": "way", "spot": [48.0, 0.0, 1.0], "way": [48.0, 0.0, 1.0],
              "met": "Landscape"}
          and field(catch.consider("cat_p", cat("cat_p"), behind_him(here, 55.0), here, 55.0, 350.0), "catch_up")
          == "moved")

    events.clear()
    catch = catch_up(Ground())
    here = run_east(catch, 12, step_cm=3000.0)
    behind = behind_him(here, 200.0)
    driven = catch.consider("cat_v", cat("cat_v"), behind, here, 200.0, 400.0)
    check("trial 6j: while the hunter drives faster than DRIVING_M_S, a due enemy is brought back behind him, the "
          "line saying he drives", catch.hunter_m_s == 30.0 and field(driven, "catch_up") == "moved"
          and field(driven, "driving") is True
          and math.isclose(math.dist(tuple(driven["spot"]), reads.spot(here)), LEVEL_80[0], abs_tol=0.1)
          and events == [("announce", "K2_TeleportTo", "cat_v", False), ("teleport", "cat_v")])
    check("again every DRIVING_EVERY_S, sooner than EVERY_S",
          catch_module.DRIVING_EVERY_S < catch_module.EVERY_S
          and catch.consider("cat_v", cat("cat_v"), behind, here, 200.0, 400.0 + catch_module.DRIVING_EVERY_S - 0.5)
          is None
          and field(catch.consider("cat_v", cat("cat_v"), behind, here, 200.0, 400.0 + catch_module.DRIVING_EVERY_S),
                    "driving") is True)
    slowed = (here[0] + 800.0, 0.0, 100.0)
    catch.walk(slowed, looking(0.0), 12.0)
    way_point = reads.spot(catch._spot(slowed, LEVEL_80[0] * 100.0)[0])
    check("once he slows, EVERY_S again, and the line no longer says he drives", catch.hunter_m_s == 8.0
          and catch.consider("cat_v", cat("cat_v"), behind, slowed, 208.0, 404.0 + catch_module.DRIVING_EVERY_S)
          is None
          and catch.consider("cat_v", cat("cat_v"), behind, slowed, 208.0, 402.0 + catch_module.EVERY_S)
          == {"catch_up": "moved", "from": "way", "spot": way_point, "way": way_point, "met": "Landscape"})
    catch = catch_up(Ground())
    here = run_east(catch, 12, yaw=180.0, step_cm=3000.0)
    check("while he drives looking back at it, it is left there", catch.hunter_m_s == 30.0
          and catch.consider("cat_y", cat("cat_y"), behind_him(here, 200.0), here, 200.0, 420.0)
          == {"catch_up": "in_sight", "driving": True})
    catch = catch_up(Ground())
    catch.walk((0.0, 0.0, 100.0), looking(0.0), 0.0)
    catch.walk((800.0, 0.0, 100.0), looking(0.0), 1.0)
    catch.walk(None, looking(0.0), 2.0)
    none_known = catch.hunter_m_s
    catch.walk((4800.0, 0.0, 100.0), looking(0.0), 3.0)
    check("his speed is unknown without a place, then taken from the last place known: at DRIVING_M_S he is not "
          "driving", none_known is None and catch.hunter_m_s == catch_module.DRIVING_M_S
          and "driving" not in catch.consider("cat_w", cat("cat_w"), (-20000.0, 0.0, 100.0), (4800.0, 0.0, 100.0),
                                              248.0, 450.0)
          and catch.consider("cat_w", cat("cat_w"), (-20000.0, 0.0, 100.0), (4800.0, 0.0, 100.0), 248.0,
                             450.0 + catch_module.DRIVING_EVERY_S) is None)

    catch = catch_up(Ground())
    here = run_east(catch, 12, yaw=180.0)
    check("an enemy where the hunter looks is left there",
          catch.consider("cat_d", cat("cat_d"), behind_him(here, 200.0), here, 200.0, 405.0)
          == {"catch_up": "in_sight"})
    catch.walk(here, object(), 12.0)
    check("and so is every enemy when where he looks cannot be read",
          catch.consider("cat_e", cat("cat_e"), behind_him(here, 200.0), here, 200.0, 406.0)
          == {"catch_up": "in_sight"})
    catch.walk(here, looking(0.0), 13.0)
    catch.given, catch.traces_left = 1, 5
    catch.look(looking(90.0))
    check("decision 107: where he looks read again for a later part of the second, its places and traces kept",
          catch.view == 90.0 and catch.given == 1 and catch.traces_left == 5)
    catch.look(object())
    check("read again where it cannot be: unknown", catch.view is None)

    for level, spot in ((LEVEL_80, [-14.0, 0.0, 1.0]), (LEVEL_25, [-24.0, 0.0, 1.0])):
        catch = catch_up(Ground(), level)
        here = run_east(catch, 3)
        aside = (here[0] - 10000.0, -20000.0, 100.0)
        check(f"trial 6m: while the hunter's way is shorter than behind_m ({level[0]:.0f} m), it goes on the ring as "
              "far, straight behind where he looks",
              catch.consider("cat_f", cat("cat_f"), aside, here, reads.metres(aside, here), 505.0)
              == {"catch_up": "moved", "from": "ring", "spot": spot, "way": spot, "met": "Landscape"})

    catch = catch_up(Ground())
    here = run_east(catch, 20, yaw=180.0)
    ahead = (here[0] + 20000.0, 0.0, 100.0)
    check("nor on his way while the hunter looks back down it, the trace not even made: on the ring behind his look",
          catch.consider("cat_g", cat("cat_g"), ahead, here, reads.metres(ahead, here), 555.0)
          == {"catch_up": "moved", "from": "ring", "spot": [182.0, 0.0, 1.0], "way": [182.0, 0.0, 1.0],
              "met": "Landscape", "refused": ["in_sight"] * len(catch_module.FARTHER_M)}
          and [[round(value, 3) for value in point] for point in catch.ground.asked] == [[18200.0, 0.0, 100.0]])

    for level, distances in ((LEVEL_80, [30, 34, 38, 42, 46]), (LEVEL_25, [40, 44, 48, 52, 56])):
        catch = catch_up(Ground(), level)
        here = run_east(catch, 12)
        places = catch_module.PLACES
        cats = [cat(f"cat_{index}") for index in range(places + 2)]
        behind = behind_him(here, 200.0)
        results = [catch.consider(one.name, one, behind, here, 200.0, 605.0) for one in cats]
        check(f"trial 6z bis: in one second, each other enemy goes 4 m farther along the way, five at most (level "
              f"placing at {level[0]:.0f} m)",
              [field(result, "catch_up") for result in results] == ["moved"] * places + ["later", "later"]
              and places == 5
              and [round(math.dist(one.went[:3], here) / 100.0) for one in cats[:places]] == distances)
    catch.walk(here, looking(0.0), 12.0)
    check("the next second, the others' turn",
          catch.consider(cats[places].name, cats[places], behind, here, 200.0, 606.0)
          == {"catch_up": "moved", "from": "way", "spot": [48.0, 0.0, 1.0], "way": [48.0, 0.0, 1.0],
              "met": "Landscape"})
    check("decision 47: at every level, the five places of one second lie nearer than far_m: none lands already due",
          all(one.behind_m + catch_module.SPACING_M * (catch_module.PLACES - 1) < one.far_m
              for one in levels.LEVELS.values()))

    catch = catch_up(Ground(), LEVEL_80, levels.SPREAD)
    here = run_east(catch, 12)
    cats = [cat(f"cat_s{index}") for index in range(catch_module.PLACES)]
    for one in cats:
        catch.consider(one.name, one, behind_him(here, 200.0), here, 200.0, 805.0)
    check("decision 66: each one brought back goes the next offset of Kevin's spread farther than its place of the "
          "second", [round(math.dist(one.went[:3], here) / 100.0) for one in cats] == [30, 44, 38, 42, 61])
    catch.walk(here, looking(0.0), 12.0)
    farther, level = cats[4], cats[0]
    check("one put 15 m farther is due only 15 m past far_m, one put at its place of the second past far_m",
          catch.consider(farther.name, farther, behind_him(here, 64.9), here, 64.9, 811.0) is None
          and field(catch.consider(farther.name, farther, behind_him(here, 65.1), here, 65.1, 811.0), "catch_up")
          == "moved"
          and field(catch.consider(level.name, level, behind_him(here, 50.1), here, 50.1, 811.0), "catch_up")
          == "moved")
    for index in range(10):
        name = f"cat_n{index}"
        catch.walk(here, looking(0.0), 13.0 + index)
        catch.consider(name, cat(name), behind_him(here, 200.0), here, 200.0, 812.0 + index)
    check("none put 5 m nearer is due before far_m: each one's own is the level's, or 10 or 15 m past it",
          set(catch.far_of.values()) == {50.0, 60.0, 65.0})
    catch = catch_up(Ground(), LEVEL_80, levels.SPREAD)
    here = run_east(catch, 12)
    catch.arrived("cat_born", 62.0)
    catch.arrived("cat_close", 20.0)
    catch.arrived("cat_unknown", None)
    check("a copy born 62 m behind him is due only past 82 m, one born nearer past far_m, one whose distance is not "
          "known as any other",
          catch.consider("cat_born", cat("cat_born"), behind_him(here, 81.9), here, 81.9, 850.0) is None
          and field(catch.consider("cat_born", cat("cat_born"), behind_him(here, 82.1), here, 82.1, 850.0),
                    "catch_up") == "moved"
          and field(catch.consider("cat_close", cat("cat_close"), behind_him(here, 50.1), here, 50.1, 850.0),
                    "catch_up") == "moved"
          and "cat_unknown" not in catch.far_of)
    barren = Barren()
    catch = catch_up(barren, LEVEL_80, levels.SPREAD)
    here = run_east(catch, 12)
    first = catch.consider("cat_t", cat("cat_t"), behind_him(here, 200.0), here, 200.0, 905.0)
    barren.barren = False
    second = catch.consider("cat_u", cat("cat_u"), behind_him(here, 200.0), here, 200.0, 905.0)
    check("a search in vain at one offset does not stop a search at another in that second",
          field(first, "catch_up") == "no_place" and field(second, "catch_up") == "moved")

    catch = catch_up(Ground())
    here = run_east(catch, 12)
    refusing, failing = cat("cat_r", answer=False), cat("cat_x", answer=RuntimeError("bad"))
    check("a teleport the game refuses, or that fails, says so",
          field(catch.consider("cat_r", refusing, behind_him(here, 200.0), here, 200.0, 705.0), "catch_up")
          == "refused"
          and field(catch.consider("cat_x", failing, behind_him(here, 200.0), here, 200.0, 705.0), "catch_up")
          == "call_failed:RuntimeError")
    check("an enemy whose distance is unknown is never due",
          stay(catch, "cat_u", cat("cat_u"), here, None, 800.0, 8) == [None] * 8)
    check("the way keeps TRAIL_POINTS points", len(catch.trail) == 12
          and len(run_east(catch, 100) and catch.trail) == catch_module.TRAIL_POINTS)

    events.clear()
    catch = catch_up(Ground())
    here = run_east(catch, 12, swum=(8,))
    result = catch.consider("cat_s", cat("cat_s"), behind_him(here, 200.0), here, 200.0, 900.0)
    check("trials 6k and 6l: never where the hunter swam: FARTHER_M back along his way instead, the line saying why",
          result == {"catch_up": "moved", "from": "way", "spot": [48.0, 0.0, 1.0], "way": [48.0, 0.0, 1.0],
                     "met": "Landscape", "refused": ["swum"]}
          and catch.ground.asked == [(4800.0, 0.0, 100.0)])
    catch = catch_up(Ground())
    here = run_east(catch, 12, swum=(11,))
    check("nor where he swims now, on his way since his last point", catch._spot(here, 100.0)[1] is True
          and catch._spot(here, 3000.0)[1] is False)

    for level, asked, spot in ((LEVEL_80, [(5800.0, 0.0, 100.0), (4800.0, 0.0, 100.0)], [47.0, 0.5, 0.3]),
                               (LEVEL_25, [(4800.0, 0.0, 100.0), (3800.0, 0.0, 100.0)], [37.0, 0.5, 0.3])):
        shore = (asked[1][0] - 100.0, 50.0, 30.0)
        catch = catch_up(Ground(("water", None, "Lake"), ("found", shore, "Rock")), level)
        here = run_east(catch, 12)
        one = cat("cat_n")
        result = catch.consider("cat_n", one, behind_him(here, 200.0), here, 200.0, 910.0)
        check(f"trial 6l: on water, 10 m farther back (level placing at {level[0]:.0f} m); it goes onto the ground "
              "found there, facing the hunter, what was met said",
              result == {"catch_up": "moved", "from": "way", "spot": spot, "way": reads.spot(asked[1]),
                         "met": "Rock", "refused": ["water"], "water_met": ["Lake"]}
              and catch.ground.asked == asked and one.went[:3] == shore
              and math.isclose(one.went[3], math.degrees(math.atan2(-50.0, here[0] - shore[0]))))
    tries = len(catch_module.FARTHER_M) + len(catch_module.RING_DEG) * len(catch_module.RING_FARTHER_M)
    catch = catch_up(Ground(*[("no_ground", None, None)] * tries))
    here = run_east(catch, 20)
    events.clear()
    check("no ground along FARTHER_M nor on the rings: no place, nothing moved; not searched again for another enemy "
          "in that second; tried again the next second",
          catch.consider("cat_m", cat("cat_m"), behind_him(here, 200.0), here, 200.0, 920.0)
          == {"catch_up": "no_place", "refused": ["no_ground"] * tries} and not events
          and catch.consider("cat_m2", cat("cat_m2"), behind_him(here, 200.0), here, 200.0, 920.0)
          == {"catch_up": "no_place", "refused": ["as_before"]} and len(catch.ground.asked) == tries
          and catch.ground.ups == [None] * len(catch_module.FARTHER_M)
          + [catch_module.RING_UP_CM] * (tries - len(catch_module.FARTHER_M))
          and (catch.walk(here, looking(0.0), 20.0) or True)
          and field(catch.consider("cat_m", cat("cat_m"), behind_him(here, 200.0), here, 200.0, 921.0), "catch_up")
          == "moved")
    catch = catch_up(Ground(*[("water", None, "Lake")] * len(catch_module.FARTHER_M)))
    here = run_east(catch, 20)
    ring = catch.consider("cat_o", cat("cat_o"), behind_him(here, 200.0), here, 200.0, 925.0)
    check("trial 6m: his whole way behind over water, it goes on the ring, the names of the water met said",
          field(ring, "catch_up") == "moved" and field(ring, "from") == "ring"
          and field(ring, "spot") == [122.0, 0.0, 1.0]
          and field(ring, "water_met") == ["Lake"] * len(catch_module.FARTHER_M))

    class Lake(Ground):
        """Water all along the hunter's way, ground beside it."""

        def ground(self, name: str, mover: object, point: tuple, up_cm: float | None = None) -> tuple:
            super().ground(name, mover, point, up_cm)
            return ("water", None, "Lake") if abs(point[1]) < 1.0 else ("found", point, "Landscape")

    catch = catch_up(Lake())
    here = run_east(catch, 20, swum=(15,))
    wet = catch.consider("cat_q", cat("cat_q"), behind_him(here, 200.0), here, 200.0, 926.0)
    check("but never on a ring point within SWUM_NEAR_M of where he swam: the next one",
          field(wet, "from") == "ring" and (field(wet, "refused") or [None])[-1] == "swum"
          and field(wet, "spot") == [129.0, 19.3, 1.0]
          and (12200.0, 0.0, 100.0) not in catch.ground.asked)

    class Shore(Ground):
        """The sea all along the hunter's way, and around him nearer than 60 m, he standing at 152 m along +X; the
        shore, higher than him, met only when traced from high enough."""

        def ground(self, name: str, mover: object, point: tuple, up_cm: float | None = None) -> tuple:
            super().ground(name, mover, point, up_cm)
            shore = (up_cm or 0.0) >= 1500.0 and math.dist(point[:2], (15200.0, 0.0)) > 5999.0
            return ("found", point, "Landscape") if shore else ("no_ground", None, None)

    catch = catch_up(Shore())
    here = run_east(catch, 20)
    shore = catch.consider("cat_z", cat("cat_z"), behind_him(here, 200.0), here, 200.0, 926.5)
    check("trial 6n: the sea all around within 38 m, it goes on a ring 60 m out, straight behind where he looks",
          field(shore, "catch_up") == "moved" and field(shore, "from") == "ring"
          and field(shore, "spot") == [92.0, 0.0, 1.0])

    class Late(Ground):
        """Ground found at every tries-th trace only."""

        def ground(self, name: str, mover: object, point: tuple, up_cm: float | None = None) -> tuple:
            super().ground(name, mover, point, up_cm)
            return ("found", point, "Landscape") if len(self.asked) % tries == 0 else ("no_ground", None, None)

    catch = catch_up(Late())
    here = run_east(catch, 20)
    fits = catch_module.TRACES_PER_SAMPLE // tries
    lines = [catch.consider(f"cat_{index}", cat(f"cat_{index}"), behind_him(here, 200.0), here, 200.0, 927.0)
             for index in range(fits + 1)]
    first_ask = len(catch.ground.asked)
    catch.walk(here, looking(0.0), 12.0)
    catch.consider(f"cat_{fits}", cat(f"cat_{fits}"), behind_him(here, 200.0), here, 200.0, 928.0)
    check("no more than TRACES_PER_SAMPLE traces a second for all enemies, the rest said; again the next second",
          catch_module.TRACES_PER_SAMPLE == 80 and fits < catch_module.PLACES
          and [field(line, "catch_up") for line in lines] == ["moved"] * fits + ["no_place"]
          and first_ask == catch_module.TRACES_PER_SAMPLE and (field(lines[-1], "refused") or [None])[-1] == "budget"
          and len(catch.ground.asked) > catch_module.TRACES_PER_SAMPLE)
    catch = catch_up(Ground())
    catch.last.update(cat_a=5.0, cat_c=2.0)
    check("trial 6z bis: each second's places go first to those never brought back, then to the one brought back "
          "longest ago, among equals as listed",
          [one.name for one in catch.queue([cat(name) for name in ("cat_a", "cat_b", "cat_c", "cat_d")])]
          == ["cat_b", "cat_d", "cat_c", "cat_a"])
    catch = catch_up(Ground(("call_failed:KeyError", None, None)))
    here = run_east(catch, 12)
    check("a failing trace stops the search at once, said",
          catch.consider("cat_k", cat("cat_k"), behind_him(here, 200.0), here, 200.0, 930.0)
          == {"catch_up": "no_place", "refused": ["call_failed:KeyError"]} and len(catch.ground.asked) == 1)
    catch = catch_up(Ground(("found", (9800.0, 0.0, 100.0), "Landscape")))
    here = run_east(catch, 12)
    check("ground found where the hunter looks is not taken either",
          catch.consider("cat_l", cat("cat_l"), behind_him(here, 200.0), here, 200.0, 940.0)
          == {"catch_up": "moved", "from": "way", "spot": [48.0, 0.0, 1.0], "way": [48.0, 0.0, 1.0],
              "met": "Landscape", "refused": ["in_sight"]})

    catch = catch_up(Ground())
    here = run_east(catch, 12)
    still = behind_him(here, 20.0)
    said = [catch.consider("cat_t", cat("cat_t"), still, here, 20.0, 1000.0 + second) for second in range(6)]
    check("trial 6l: one standing still STUCK_S farther than STUCK_NEAR_M is brought back, said, though within far_m",
          said[:5] == [None] * 5 and field(said[5], "catch_up") == "moved" and field(said[5], "stuck") is True
          and catch_module.STUCK_NEAR_M < min(one.far_m for one in levels.LEVELS.values()))
    near = behind_him(here, 5.0)
    check("not one standing near the hunter",
          [catch.consider("cat_u", cat("cat_u"), near, here, 5.0, 1000.0 + second) for second in range(8)]
          == [None] * 8)
    check("nor one that moves more than STUCK_MOVE_M a second",
          [catch.consider("cat_v", cat("cat_v"), (here[0] - 2000.0 - 150.0 * second, 0.0, 100.0), here,
                          20.0 + 1.5 * second, 1000.0 + second) for second in range(8)] == [None] * 8)
    check("nor one whose place is unknown for a moment",
          [catch.consider("cat_x", cat("cat_x"), None if second == 3 else still, here, 20.0, 1000.0 + second)
           for second in range(8)] == [None] * 8)
    catch = catch_up(Ground())
    here = run_east(catch, 12, yaw=180.0)
    said = [catch.consider("cat_y", cat("cat_y"), behind_him(here, 20.0), here, 20.0, 1000.0 + second)
            for second in range(6)]
    check("one stuck where the hunter looks is left there, said", said[5] == {"catch_up": "in_sight", "stuck": True})

    catch = catch_up(Ground())
    here = run_east(catch, 12)
    respawn = (here[0] - 25000.0, 0.0, 100.0)
    catch.walk(respawn, looking(0.0), 12.0)
    check("his place jumped farther than JUMP_M (a death, a fast travel): his way is forgotten, no speed taken",
          list(catch.trail) == [(respawn, False)] and catch.hunter_m_s is None)
    check("so the enemy goes on the ring around his new place, not on the old way between it and the old place",
          catch.consider("cat_j", cat("cat_j"), behind_him(respawn, 200.0), respawn, 200.0, 1100.0)
          == {"catch_up": "moved", "from": "ring", "spot": [-192.0, 0.0, 1.0], "way": [-192.0, 0.0, 1.0],
              "met": "Landscape"}
          and [[round(value, 3) for value in point] for point in catch.ground.asked] == [[-19200.0, 0.0, 100.0]])
    for step in range(1, 6):
        catch.walk((respawn[0] + 800.0 * step, 0.0, 100.0), looking(0.0), 12.0 + step)
    renewed = (respawn[0] + 4000.0, 0.0, 100.0)
    check("then a new way grows from there, his speed taken again",
          catch.hunter_m_s == 8.0 and len(catch.trail) == 6
          and catch.consider("cat_j2", cat("cat_j2"), behind_him(renewed, 200.0), renewed, 200.0, 1110.0)
          == {"catch_up": "moved", "from": "way", "spot": [-152.0, 0.0, 1.0], "way": [-152.0, 0.0, 1.0],
              "met": "Landscape"})
    catch = catch_up(Ground())
    here = run_east(catch, 12)
    catch.walk((here[0] + catch_module.JUMP_M * 100.0, 0.0, 100.0), looking(0.0), 12.0)
    kept = len(catch.trail) == 13 and catch.hunter_m_s == catch_module.JUMP_M
    catch.walk(None, looking(0.0), 13.0)
    catch.walk((here[0] + catch_module.JUMP_M * 200.0 + 1.0, 0.0, 100.0), looking(0.0), 14.0)
    check("JUMP_M itself is still a way, even at 200 m/s; past it, even after a place unknown, the way is forgotten",
          catch_module.JUMP_M == 200.0 and kept and len(catch.trail) == 1 and catch.hunter_m_s is None)

    catch = catch_up(Ground())
    here = run_east(catch, 12)
    behind = behind_him(here, 200.0)
    catch.consider("cat_k", cat("cat_k"), behind, here, 200.0, 1200.0)
    catch.consider("cat_l", cat("cat_l"), behind, here, 200.0, 1200.0)
    held = "cat_k" in catch.last and "cat_k" in catch.still and "cat_k" in catch.far_of
    catch.forget("cat_k")
    catch.forget("nobody")
    check("an enemy let go is forgotten, when it was brought back, where it stood and its own far_m; the others are "
          "kept",
          held and "cat_k" not in catch.last and "cat_k" not in catch.still and "cat_k" not in catch.far_of
          and "cat_l" in catch.last and "cat_l" in catch.still and "cat_l" in catch.far_of)
    catch.walk(here, looking(0.0), 12.0)
    check("so a body the game gives back under that name is new to the catch-up: first served, due at once",
          catch.queue([cat("cat_l"), cat("cat_k")])[0].name == "cat_k"
          and field(catch.consider("cat_k", cat("cat_k"), behind, here, 200.0, 1201.0), "catch_up") == "moved"
          and catch.consider("cat_l", cat("cat_l"), behind, here, 200.0, 1201.0) is None)
    catch = catch_up(Ground())
    here = run_east(catch, 12)
    for index in range(10_000):
        catch.walk(here, looking(0.0), 12.0 + index)
        name = f"enemy_{index}"
        catch.consider(name, cat(name), behind_him(here, 200.0), here, 200.0, 1300.0 + index)
        catch.forget(name)
    check("10 000 enemies brought back and let go: nothing kept of them, the way still a minute",
          catch.last == {} and catch.still == {} and catch.far_of == {}
          and len(catch.trail) == catch_module.TRAIL_POINTS)

    events.clear()
    traces = fixture.TraceLibrary(events, ground_z=40.0)
    state["classes"]["KismetSystemLibrary"] = types.SimpleNamespace(ClassDefaultObject=traces)
    real = ground_module.GroundTrace(announce)
    catch = catch_up(real)
    here = run_east(catch, 12)
    one = cat("cat_real")
    line = catch.consider("cat_real", one, behind_him(here, 200.0), here, 200.0, 1400.0)
    traced = traces.asked[0] if traces.asked else None
    check("with the real ground trace: the way's point traced from TRACE_UP_CM above to DROP_CM below, the enemy put "
          "its half height and CLEARANCE_CM above the ground met, facing the hunter, each call announced first",
          line == {"catch_up": "moved", "from": "way", "spot": [58.0, 0.0, 1.2], "way": [58.0, 0.0, 1.0],
                   "met": fixture.LANDSCAPE}
          and traced is not None and (traced[1].X, traced[1].Z, traced[2].Z)
          == (5800.0, 100.0 + ground_module.TRACE_UP_CM, 100.0 - ground_module.DROP_CM)
          and one.went is not None and math.isclose(one.went[0], 5800.0, abs_tol=1.0)
          and one.went[1:] == (0.0, 40.0 + 60.0 + ground_module.CLEARANCE_CM, 0.0)
          and events == [("announce", "LineTraceSingle", "cat_real", True), ("trace",),
                         ("announce", "K2_TeleportTo", "cat_real", False), ("teleport", "cat_real")])
    catch = catch_up(real)
    here = run_east(catch, 3)
    asked = len(traces.asked)
    aside = (here[0] - 10000.0, -20000.0, 100.0)
    line = catch.consider("cat_ring", cat("cat_ring"), aside, here, reads.metres(aside, here), 1410.0)
    traced = traces.asked[-1] if len(traces.asked) == asked + 1 else None
    check("and a ring point traced from RING_UP_CM above the hunter down to DROP_CM below him",
          field(line, "from") == "ring" and field(line, "spot") == [-14.0, 0.0, 1.2] and traced is not None
          and (traced[1].Z, traced[2].Z) == (100.0 + catch_module.RING_UP_CM, 100.0 - ground_module.DROP_CM))

    catch = catch_up(ground_module.GroundTrace(announce))
    here = run_east(catch, 12)
    traces.raises = RuntimeError("trace")
    for index in range(3):
        catch.walk(here, looking(0.0), 1500.0 + index)
        catch.consider(f"cat_broken_{index}", cat(f"cat_broken_{index}"), behind_him(here, 200.0), here, 200.0,
                       1500.0 + index)
    traces.raises = None
    check("review: a trace that failed ends the catch-up's traces for the run, said in the status line; only the "
          "trace made counted", catch.gauge() == {"no_place": 3, "traces": 1, "broken": "call_failed:RuntimeError"})
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
