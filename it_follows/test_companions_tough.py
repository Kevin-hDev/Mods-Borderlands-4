"""Tests trial 172's health and shield (tough.py): the health set to the level's times the hunter's most health
(trial 187: the level given at the start, difficulty.Played, said with why), or to the times a trial gives,
shared by every pool whose type is not the shield's as the game shared it, the game's bonus over the base corrected by
a second write, lowered as well as raised, and made full; a pool without a type, or without health, left alone; the
hunter's health unread: nothing written; no health pool: nothing more, said with the types and maxima read; a shield
held sized to SHIELD_SHARE of that health, else one added then sized, or said when it cannot be; no shield while
SHIELD_SHARE is zero; its shield off: none added nor sized, one the game gave it left as it is; written again, the
same values; each write said first; the shield's fill read each sample: below God never filled again, at God
filled again its level's 45 s after it broke, even under fire, once at a time, a fill that fails said and waited for
again; its health read, or None; its layers read at the end, or why not."""

import pathlib
import sys
import types
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
fails: list[str] = []
FLESH, ARMOR, ENERGY = "HealthType_AI_Flesh", "HealthType_AI_Armor", "HealthType_AI_Energy"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("follow_tough_under_test", HERE / "it_follows" / "companions" / "tough.py")
tough_module = util.module_from_spec(spec)
spec.loader.exec_module(tough_module)
# The levels' own table at the frontier (difficulty.py), never numbers of the test's.
spec = util.spec_from_file_location("follow_difficulty_for_tough", HERE / "it_follows" / "companions" / "difficulty.py")
difficulty = util.module_from_spec(spec)
spec.loader.exec_module(difficulty)
check("a shield of 30 % of the health; It Follows' fill rate", tough_module.SHIELD_SHARE == 0.3
      and tough_module.REFILL_RATE == 0.13)
# The writes below are checked at Predator's 9 times, their numbers worked out by hand since trial 172.
PREDATOR, GOD = difficulty.level("Predator", "normal"), difficulty.level("God", "normal")
AT_PREDATOR = ["Predator", "normal"]

events: list[str] = []


class Pools:
    """Maxima by pool, their types; the game's bonus multiplies a written base, as MV1 read."""

    def __init__(self, maxima: dict, kinds: list, bonus: float = 1.0) -> None:
        self.maxima, self.kinds, self.bonus = dict(maxima), list(kinds), bonus
        self.health = 0.456

    def most(self, actor: object, pool: int) -> float:
        if actor == "broken":
            raise RuntimeError("unread")
        return self.maxima.get(pool, 0.0)

    def set_base(self, actor: object, pool: int, base: float) -> float:
        events.append(f"base {pool} {round(base, 2)}")
        self.maxima[pool] = base * self.bonus
        return self.maxima[pool]

    def set_share(self, actor: object, pool: int, wanted: float) -> None:
        events.append(f"share {pool} {wanted}")

    def share(self, actor: object, pool: int) -> float:
        if actor == "broken":
            raise RuntimeError("unread")
        return self.health


class Shields:
    """It Follows' ShieldPool: add lays a shield in the first free pool, sized on the health held, as the game does."""

    def __init__(self, pools: Pools, added: bool = True) -> None:
        self.pools, self.added, self.level = pools, added, 1.0

    def add(self, actor: object, share: float) -> object:
        events.append(f"add {share}")
        if not self.added:
            return None
        pool = next(pool for pool in range(3) if self.pools.maxima.get(pool, 0.0) <= 0.0)
        size = share * sum(most for most in self.pools.maxima.values() if most > 0.0) + 1234.0
        self.pools.maxima[pool] = size
        self.pools.kinds.append(ENERGY)
        return pool, size

    def fill(self, actor: object, pool: int) -> float:
        events.append(f"fill {pool}")
        return self.level

    def refill(self, actor: object, seconds: float) -> None:
        events.append(f"refill {round(seconds, 2)}")
        if self.level == "refused":
            raise RuntimeError("refused")


def tough(pools: Pools, shields: Shields | None = None, actor: object = "frame") -> object:
    events.clear()
    return tough_module.Tough(lambda: actor, "Frame_1", lambda text: events.append(f"note {text}"), pools,
                              shields if shields is not None else Shields(pools), lambda found: pools.kinds,
                              ENERGY)


pools = Pools({0: 230647.0}, [ARMOR], bonus=1.3)
toughened = tough(pools)
check("its health set to 9 times the hunter's, lowered, the game's bonus corrected, full; a shield added then sized",
      toughened.harden(10874.0, PREDATOR) == {"level": AT_PREDATOR, "hunter": 10874,
                                              "health": {"0": [230647, 97866]}, "shield": [1, 30594, 29360]}
      and round(pools.maxima[0], 6) == 97866.0 and round(pools.maxima[1], 6) == 29359.8)
check("each write said first", events == [
      "note about to write the maximum of pool 0 on Frame_1: 97866", "base 0 97866.0", "base 0 75281.54",
      "share 0 1.0", "note about to call AddHealthPool on Frame_1", "add 0.3",
      "note about to write the maximum of pool 1 on Frame_1: 29360", "base 1 29359.8", "base 1 22584.46",
      "share 1 1.0"])
check("its health read", toughened.health() == 0.46)
events.clear()
check("its shield's fill read each sample", toughened.keep(0.0) == "1.00" and events == ["fill 1"])
toughened.shields.level = 0.0
check("below God, broken, it stays broken", toughened.keep(1.0) == "0.00" and toughened.keep(500.0) == "0.00"
      and not any(event.startswith(("add", "base", "refill")) for event in events) and toughened.refills == 0)
check("its layers read at the end", toughened.layers() == {"most": [97866, 29360, 0], "types": [ARMOR, ENERGY]})

check("a weak one raised to the same health", tough(Pools({0: 17466.0}, [FLESH])).harden(
      10874.0, PREDATOR)["health"] == {"0": [17466, 97866]})
check("trial 183: times given, half the hunter's health and its shield, the level's left alone", tough(
      Pools({0: 17466.0}, [FLESH])).harden(10874.0, PREDATOR, 0.5) == {
          "level": AT_PREDATOR, "hunter": 10874, "health": {"0": [17466, 5437]}, "shield": [1, 2865, 1631]})
pools = Pools({0: 96103.0, 1: 38441.0, 2: 38441.0}, [FLESH, ENERGY, FLESH])
crankus = tough(pools)
check("two pools of health share the health as they shared the game's; the shield held sized, none added",
      crankus.harden(10874.0, PREDATOR) == {"level": AT_PREDATOR, "hunter": 10874,
                                            "health": {"0": [96103, 69904], "2": [38441, 27962]},
                                            "shield": [1, 38441, 29360]}
      and "add 0.3" not in events and crankus.shield == 1
      and abs(pools.maxima[0] + pools.maxima[2] - 97866.0) < 1e-6 and crankus.keep(0.0) == "1.00")
pools = Pools({0: 100.0, 1: 50.0, 2: 70.0}, [FLESH])
check("a pool without a type left alone, a shield added in none of them: said", tough(
      pools, Shields(pools, added=False)).harden(10874.0, PREDATOR) == {
          "level": AT_PREDATOR, "hunter": 10874, "health": {"0": [100, 97866]}, "shield": "no_single_pool"}
      and pools.maxima[1] == 50.0 and pools.maxima[2] == 70.0)
pools = Pools({0: 100.0}, [FLESH])
astray = Shields(pools)
astray.add = lambda actor, share: (events.append("add 0.3"), (2, 30.0))[1]
lost = tough(pools, astray)
check("a shield added where it reads nothing: said, nothing written there, no fill", lost.harden(
      10874.0, PREDATOR)["shield"] == "unsized" and 2 not in pools.maxima and lost.keep(0.0) is None)
check("God: 12 times the hunter's health", tough(Pools({0: 100.0}, [FLESH])).harden(10874.0, GOD)["health"]
      == {"0": [100, 130488]})
bandit = tough(Pools({0: 100.0}, [FLESH]))
check("Bandit, as It Follows plays nothing: 4 times, said with why, its shield never filled again", bandit.harden(
      10874.0, difficulty.level("Bandit", "off"))["health"] == {"0": [100, 43496]} and bandit.refill_after_s is None
      and bandit.harden(10874.0, difficulty.level("Bandit", "off"))["level"] == ["Bandit", "off"])
halved = tough(Pools({0: 100.0}, [FLESH]))
check("times given at God: half the hunter's health, the shield filled again 45 s after it broke", halved.harden(
      10874.0, GOD, 0.5)["health"] == {"0": [100, 5437]} and halved.refill_after_s == 45.0)
check("a type without health left alone", tough(Pools({0: 100.0}, [FLESH, ENERGY])).harden(
      10874.0, PREDATOR)["shield"] == [1, 30594, 29360])
pools = Pools({0: 100.0}, [FLESH])
first = tough(pools).harden(10874.0, PREDATOR)
second = tough(pools).harden(10874.0, PREDATOR)
check("written again: the same health and the same shield, never raised twice", first["health"]["0"][1]
      == second["health"]["0"][1] == 97866 and second["shield"] == [1, 29360, 29360] and "add 0.3" not in events)

for hunter in ("unread:RuntimeError", "unread:-1.0", None, 10874):
    events.clear()
    check(f"the hunter's health {hunter!r}: nothing written", tough(Pools({0: 100.0}, [FLESH])).harden(
          hunter, PREDATOR) == {"level": AT_PREDATOR, "hunter": hunter, "health": "not_written", "shield": "none"}
          and not any(event.startswith(("base", "add")) for event in events))
check("no health pool: nothing more, said with the types and maxima read", tough(Pools({}, [FLESH])).harden(
      10874.0, PREDATOR) == {"level": AT_PREDATOR, "hunter": 10874, "health": "no_pool", "shield": "none",
                             "types": [FLESH], "maxima": [0]})
check("no type read at all (trial 190, cause unknown): no health pool, said", tough(Pools({0: 100.0}, [])).harden(
      10874.0, PREDATOR) == {"level": AT_PREDATOR, "hunter": 10874, "health": "no_pool", "shield": "none",
                             "types": [], "maxima": []} and not any(event.startswith("base") for event in events))
check("only a shield: no health pool", tough(Pools({0: 50.0}, [ENERGY])).harden(10874.0, PREDATOR)["health"]
      == "no_pool")
pools = Pools({0: 100.0}, [FLESH])
bare = tough(pools)
check("its shield off (the window's card): its health set, no shield added nor sized, none read after",
      bare.harden(10874.0, PREDATOR, shielded=False) == {"level": AT_PREDATOR, "hunter": 10874,
                                                         "health": {"0": [100, 97866]}, "shield": "off"}
      and not any(event.startswith("add") for event in events) and 1 not in pools.maxima and bare.keep(0.0) is None)
pools = Pools({0: 96103.0, 1: 38441.0}, [FLESH, ENERGY])
own = tough(pools)
check("its shield off, one the game gave it: left as the game has it", own.harden(
      10874.0, PREDATOR, shielded=False)["shield"] == "off" and pools.maxima[1] == 38441.0
      and not any(event.startswith(("base 1", "share 1")) for event in events))
tough_module.SHIELD_SHARE = 0.0
plain = tough(Pools({0: 100.0}, [FLESH]))
check("SHIELD_SHARE zero: no shield, no fill", plain.harden(10874.0, PREDATOR)["shield"] == "none"
      and plain.keep(0.0) is None and "add 0.0" not in events)
tough_module.SHIELD_SHARE = 0.3
check("no shield yet: no fill", tough(Pools({0: 100.0}, [FLESH])).keep(0.0) is None)
check("trial 178's bars: no shield, None", tough(Pools({0: 100.0}, [FLESH])).shield_share() is None)
pools = Pools({0: 100.0}, [FLESH])
read_only = tough(pools)
read_only.harden(10874.0, PREDATOR)
read_only.shields.level = 0.12345
events.clear()
check("trial 178's bars: its shield read, rounded, nothing written nor refilled", read_only.shield_share() == 0.123
      and events == ["fill 1"] and read_only.broken_at is None)
read_only.shields.fill = lambda actor, pool: (_ for _ in ()).throw(RuntimeError("unread"))
check("trial 178's bars: a shield unread, None", read_only.shield_share() is None)

pools = Pools({0: 100.0}, [FLESH])
god = tough(pools)
god.harden(10874.0, GOD)
shield = god.shields
events.clear()
shield.level = 0.4
check("at God, a shield worn but not broken: only read", god.keep(10.0) == "0.40" and events == ["fill 1"])
shield.level = 0.0
check("broken: said once, the wait started", god.keep(11.0) == "0.00,broken" and god.keep(12.0) == "0.00")
check("still broken before 45 s: nothing", god.keep(55.9) == "0.00" and not any("refill" in e for e in events))
events.clear()
check("45 s after it broke: filled over It Follows' 7.7 s, said first", god.keep(56.0) == "0.00,refill"
      and events == ["fill 1", "note about to call RefillHealthPercentOvertime on Frame_1", "refill 7.69"]
      and god.refills == 1)
events.clear()
check("broken again while it fills: nothing until the fill's end", god.keep(60.0) == "0.00" and god.keep(63.6) == "0.00"
      and not any("refill" in e for e in events))
events.clear()
check("the fill over, at its very end, and still broken: its end noted, the wait starts again",
      god.keep(56.0 + 1.0 / 0.13) == "0.00,broken" and god.ends == [0.0]
      and "note fill ended on Frame_1: 0.00" in events)
check("the end noted once; the next wait counted from the fill's end", god.keep(70.0) == "0.00" and god.ends == [0.0]
      and god.keep(108.6) == "0.00" and god.keep(108.7) == "0.00,refill" and god.refills == 2)
shield.level = 1.0
check("filled: read, the wait forgotten, its end noted", god.keep(200.0) == "1.00" and god.broken_at is None
      and god.ends == [0.0, 1.0])
god.ends.extend([0.5] * 30)
del god.ends[tough_module.MOST_ENDS:]
god.filled_until = 199.0
check("no more ends kept than MOST_ENDS", god.keep(200.5) == "1.00" and len(god.ends) == tough_module.MOST_ENDS)
shield.level = 0.0
god.keep(201.0)
shield.level = 0.5
god.keep(202.0)
shield.level = 0.0
check("worn between two breaks: the wait counted from the second", god.keep(203.0) == "0.00,broken"
      and god.keep(247.9) == "0.00" and god.keep(248.0) == "0.00,refill")
failing = tough(Pools({0: 100.0}, [FLESH]))
failing.harden(10874.0, GOD)
failing.shields.level = 0.0
failing.keep(0.0)
failing.shields.level = "refused"
failing.shields.fill = lambda actor, pool: 0.0
check("a fill that fails: said, not counted, the wait started again", failing.keep(45.0)
      == "0.00,refill_failed:RuntimeError" and failing.refills == 0 and failing.keep(46.0) == "0.00,broken")

# It Follows' real ShieldPool at the frontier, only the game faked: a fake piece once hid a failure (trial 176).
library_calls: list[dict] = []
PARAMETER = types.SimpleNamespace(TypeHandle=7)
state["classes"]["DamageStatics"] = types.SimpleNamespace(
    ClassDefaultObject=types.SimpleNamespace(RefillHealthPercentOvertime=lambda **given: library_calls.append(given)),
    _find=lambda function: types.SimpleNamespace(_find=lambda parameter: PARAMETER))
sys.modules["unrealsdk.unreal"].FGameDataHandle = lambda kind, name: ("handle", kind, name)
from it_follows import shield_pool  # noqa: E402

pools = Pools({0: 100.0, 1: 30.0}, [FLESH, ENERGY])
real = tough(pools, shield_pool.ShieldPool(pools))
real.harden(10874.0, GOD)
pools.health = 0.0
real.keep(0.0)
check("It Follows' own refill asked of the game: the shield's type, all of it, over 7.7 s, a tick of 0.1 s",
      real.keep(45.0) == "0.00,refill" and library_calls == [{
          "Context": "frame", "HealthType": ("handle", 7, ENERGY), "Percent": 1.0, "MaxPercent": 1.0,
          "Duration": 1.0 / 0.13, "TickRate": 0.1}])
check("health unread: None", tough(Pools({0: 1.0}, [FLESH]), actor="broken").health() is None)
check("layers unread: said", tough(Pools({0: 1.0}, [FLESH]), actor="broken").layers() == "unread:RuntimeError")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
