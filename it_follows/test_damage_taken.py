"""Tests BUFF and BUFF+ on the hunter (damage_taken): Normal writes nothing, ever; the multiplier's base and value
raised from the game's own, announced first; once a sample nothing written while it holds, a value the game computed
again from the raised base left to it, a base the game wrote anew taken as its own and raised again; at the stop the
game's base written back and the value without the raise, nothing written over a base the game rewrote; a hunter
without the field, gone, or refusing the write says so. The Hardcore's factor changed during a game: written from the
game's base and the value without the old raise, back to the level's, from a base the game wrote anew, started when
nothing was raised yet, and given back at the stop."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import damage_taken  # noqa: E402

fails: list[str] = []
events: list[tuple] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Pair:
    """DamageTakenMultiplier: what is written is noted in events; refusing, it raises."""

    def __init__(self, base: float, value: float) -> None:
        self._base, self._value, self.refuse = base, value, False

    def _write(self, field: str, value: float) -> None:
        events.append(("write", field, round(value, 4)))
        if self.refuse:
            raise RuntimeError("read only")

    @property
    def BaseValue(self) -> float:
        return self._base

    @BaseValue.setter
    def BaseValue(self, value: float) -> None:
        self._write("BaseValue", value)
        self._base = value

    @property
    def Value(self) -> float:
        return self._value

    @Value.setter
    def Value(self, value: float) -> None:
        self._write("Value", value)
        self._value = value


def hunter(base: float = 1.0, value: float = 0.9) -> types.SimpleNamespace:
    """A hunter whose value is below its base: a skill of his lowers the damage he takes."""
    return types.SimpleNamespace(DamageState=types.SimpleNamespace(DamageTakenMultiplier=Pair(base, value)))


def taken(factor: float) -> damage_taken.DamageTaken:
    return damage_taken.DamageTaken(lambda call, log=True, **fields: events.append(("announce", call, log, fields)),
                                    factor)


def writes() -> list[tuple]:
    return [event[1:] for event in events if event[0] == "write"]


try:
    player = hunter()
    normal = taken(1.0)
    check("Normal writes nothing, ever", normal.start(player) == {} and normal.keep(player) is None
          and normal.put_back(player) == "not_raised" and events == [])

    buff = taken(1.1)
    said = buff.start(player)
    pair = player.DamageState.DamageTakenMultiplier
    check("Buff raises the base and the value from the game's own, announced first",
          events == [("announce", "DamageTakenMultiplier", True, {"value": 0.99}), ("write", "BaseValue", 1.1),
                     ("write", "Value", 0.99)])
    check("what it was and what it is, for the log", said == {"base": [1.0, 1.1], "value": [0.9, 0.99]})
    events.clear()
    check("once a sample, nothing written while it holds", buff.keep(player) is None and events == [])
    pair._value = 1.1 * 0.8
    check("a value the game computed again from the raised base is left to it",
          buff.keep(player) == {"taken": "computed", "value": 0.88} and writes() == [] and buff.keep(player) is None)
    pair._base, pair._value = 1.0, 0.8
    check("a base the game wrote anew is taken as its own and raised again, without a line",
          buff.keep(player) == {"taken": "again", "game_base": 1.0}
          and writes() == [("BaseValue", 1.1), ("Value", 0.88)] and events[0][2] is False)
    events.clear()
    check("at the stop the game's base written back, the value without the raise", buff.put_back(player) == "restored"
          and writes() == [("BaseValue", 1.0), ("Value", 0.8)])
    check("then let go: nothing read nor written again", buff.keep(player) is None
          and buff.put_back(player) == "not_raised")

    player = hunter()
    plus = taken(1.2)
    plus.start(player)
    player.DamageState.DamageTakenMultiplier._base = 1.5
    events.clear()
    check("a base the game rewrote since the last sample is left to it at the stop",
          plus.put_back(player) == "left_to_game" and writes() == [])

    stranger = types.SimpleNamespace()
    lacking = taken(1.1)
    check("a hunter without the field says so, and nothing is held", lacking.start(stranger)
          == {"failed": "AttributeError"} and lacking.keep(stranger) is None and lacking.put_back(stranger)
          == "not_raised")
    gone = taken(1.1)
    gone.start(hunter())
    check("a hunter gone at the stop says so", gone.put_back(None) == "unavailable")
    player = hunter()
    refusing = taken(1.1)
    refusing.start(player)
    player.DamageState.DamageTakenMultiplier.refuse = True
    check("a write refused at the stop says why", refusing.put_back(player) == "failed:RuntimeError")

    player = hunter()
    hard = taken(1.1)
    hard.start(player)
    events.clear()
    check("a new factor written from the game's base, the value without the old raise",
          hard.change(player, 1.21) == {"base": [1.0, 1.21], "value": [0.9, 1.089]}
          and writes() == [("BaseValue", 1.21), ("Value", 1.089)] and events[0][2] is True)
    check("then back to the level's", hard.change(player, 1.1) == {"base": [1.0, 1.1], "value": [0.9, 0.99]})
    pair = player.DamageState.DamageTakenMultiplier
    pair._base, pair._value = 1.0, 0.8
    check("from a base the game wrote anew, taken as its own",
          hard.change(player, 1.21) == {"base": [1.0, 1.21], "value": [0.8, 0.968]})
    events.clear()
    check("given back at the stop", hard.put_back(player) == "restored"
          and writes() == [("BaseValue", 1.0), ("Value", 0.8)])
    fresh = taken(1.0)
    check("nothing raised yet: started with the new factor",
          fresh.change(hunter(), 1.1) == {"base": [1.0, 1.1], "value": [0.9, 0.99]})
    check("a hunter without the field says so", taken(1.1).change(stranger, 1.2) == {"failed": "AttributeError"})
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
