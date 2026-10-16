"""Tests It Follows' speed (speed): every enemy drawn has its speed bonus raised to the game's own times the factor the
player chose, each write announced first, the first DETAILED of a run written to the log; once a sample the bonus is
read back, left alone
while it holds and written again, announced without a line in the log, once the game changed it; at the let-go the
game's own bonus is written back once, announced first, even when nothing else may be called on the body; an enemy
that cannot be read or written says why and is not counted faster; Normal writes nothing, ever; every enemy let go is
forgotten."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import speed  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


events: list[tuple] = []


class Scale:
    """The bonus: what is written is noted in events; refusing, it raises."""

    def __init__(self, name: str, value: float) -> None:
        self.name, self._value, self.refuse = name, value, False

    @property
    def Value(self) -> float:
        return self._value

    @Value.setter
    def Value(self, value: float) -> None:
        events.append(("write", self.name, round(value, 3)))
        if self.refuse:
            raise RuntimeError("read only")
        self._value = value


def enemy(name: str, value: float = 1.0) -> types.SimpleNamespace:
    movement = types.SimpleNamespace(MaxGroundSpeedScale=Scale(name, value))
    return types.SimpleNamespace(CharacterMovement=movement)


def chaser(name: str, mover: object) -> types.SimpleNamespace:
    """A chaser as It Follows holds it: its name, and its enemy through a weak pointer."""
    return types.SimpleNamespace(name=name, actor=sdk_stubs.FakeWeak(mover))


def announce(call: str, log: bool = True, **fields: object) -> None:
    """Notes the call, whether it is a write again or back, and whether it goes to the log."""
    events.append(("announce", call, fields.get("on"), "again" in fields, "back" in fields, log))


def bonus(mover: object) -> float:
    return round(mover.CharacterMovement.MaxGroundSpeedScale.Value, 3)


try:
    movers = [enemy(f"cat_{index}") for index in range(5)]
    speedy = speed.SpeedBoost(announce, 1.2)
    lines = speedy.start([chaser(f"cat_{index}", mover) for index, mover in enumerate(movers)])
    check("decision 48: every enemy drawn is made faster, not one in two as in the trials",
          [line["on"] for line in lines] == [f"cat_{index}" for index in range(5)]
          and [bonus(mover) for mover in movers] == [1.2] * 5)
    check("each says its bonus before and after", lines[0] == {"on": "cat_0", "scale": [1.0, 1.2]})
    check("each write announced first and written to the log, nothing else called",
          events[:4] == [("announce", "MaxGroundSpeedScale", "cat_0", False, False, True), ("write", "cat_0", 1.2),
                         ("announce", "MaxGroundSpeedScale", "cat_1", False, False, True), ("write", "cat_1", 1.2)])
    many = speed.SpeedBoost(announce, 1.2)
    events.clear()
    crowd = [enemy(f"bat_{index}") for index in range(speed.DETAILED + 2)]
    many.start([chaser(f"bat_{index}", mover) for index, mover in enumerate(crowd)])
    logged = [entry[5] for entry in events if entry[0] == "announce"]
    check("audit of 16 October: the first DETAILED of a run written to the log, the rest announced without a line, "
          "all written", logged == [True] * speed.DETAILED + [False] * 2 and [bonus(mover) for mover in crowd]
          == [1.2] * (speed.DETAILED + 2))
    events.clear()
    many.put_back("bat_21", crowd[21])
    check("given back, a bonus is still written to the log first: the enemy may be dead",
          events[0] == ("announce", "MaxGroundSpeedScale", "bat_21", False, True, True))

    events.clear()
    check("a bonus that held is left alone, nothing written", speedy.keep("cat_0", movers[0]) is None and events == [])
    check("an enemy never made faster is left alone", speedy.keep("cat_9", enemy("cat_9")) is None and events == [])
    movers[2].CharacterMovement.MaxGroundSpeedScale._value = 0.92
    check("a bonus the game changed is written again, announced without a line in the log, the game's value said",
          speedy.keep("cat_2", movers[2]) == {"boost": "again", "game_value": 0.92}
          and events == [("announce", "MaxGroundSpeedScale", "cat_2", True, False, False), ("write", "cat_2", 1.2)]
          and bonus(movers[2]) == 1.2)
    movers[4].CharacterMovement.MaxGroundSpeedScale._value = 1.2 + speed.SAME / 2.0
    check("within SAME of the raised value it held", speed.SAME > 0.0 and speedy.keep("cat_4", movers[4]) is None)
    check("a bonus that cannot be read says so", speedy.keep("cat_0", object()) == {"boost": "failed:AttributeError"})

    events.clear()
    check("at the let-go the game's bonus is written back, announced first and written to the log",
          speedy.put_back("cat_0", movers[0]) == "restored"
          and events == [("announce", "MaxGroundSpeedScale", "cat_0", False, True, True), ("write", "cat_0", 1.0)]
          and movers[0].CharacterMovement.MaxGroundSpeedScale.Value == 1.0)
    check("once", speedy.put_back("cat_0", movers[0]) == "not_boosted" and speedy.keep("cat_0", movers[0]) is None)
    check("one never made faster is not touched", speedy.put_back("cat_9", enemy("cat_9")) == "not_boosted")
    check("without its body nothing is written, and it is forgotten", speedy.put_back("cat_2", None) == "unavailable"
          and speedy.put_back("cat_2", movers[2]) == "not_boosted")
    movers[4].CharacterMovement.MaxGroundSpeedScale.refuse = True
    check("a write back that fails says its error", speedy.put_back("cat_4", movers[4]) == "failed:RuntimeError")

    events.clear()
    speedy = speed.SpeedBoost(announce, 1.2)
    shy = enemy("shy")
    shy.CharacterMovement.MaxGroundSpeedScale.refuse = True
    lines = speedy.start([chaser("gone", None), chaser("between", enemy("between")), chaser("shy", shy),
                          chaser("x", enemy("x"))])
    check("an enemy without a body says why and is not counted faster",
          lines[0] == {"on": "gone", "failed": "AttributeError"} and speedy.keep("gone", None) is None)
    check("a bonus the game refuses to take says so, not counted faster",
          lines[2] == {"on": "shy", "failed": "RuntimeError"} and speedy.put_back("shy", shy) == "not_boosted")
    check("the others are made faster all the same", lines[1] == {"on": "between", "scale": [1.0, 1.2]}
          and lines[3] == {"on": "x", "scale": [1.0, 1.2]})

    factors = (1.1, 1.2, 1.3, 1.4, 1.5)
    tired = [enemy(f"tired_{factor}", 0.9) for factor in factors]
    events.clear()
    said = [speed.SpeedBoost(announce, factor).start([chaser(f"tired_{factor}", mover)])[0]
            for factor, mover in zip(factors, tired)]
    check("decision 48: +10 % to +50 %, the game's own bonus times the factor chosen, the write announced first",
          [bonus(mover) for mover in tired] == [0.99, 1.08, 1.17, 1.26, 1.35]
          and [line["scale"] for line in said] == [[0.9, 0.99], [0.9, 1.08], [0.9, 1.17], [0.9, 1.26], [0.9, 1.35]]
          and [entry for entry in events if entry[1] == "MaxGroundSpeedScale"]
          == [("announce", "MaxGroundSpeedScale", f"tired_{factor}", False, False, True) for factor in factors])
    fastest = speed.SpeedBoost(announce, 1.5)
    runner = enemy("runner", 0.9)
    fastest.start([chaser("runner", runner)])
    runner.CharacterMovement.MaxGroundSpeedScale._value = 0.9
    check("at +50 %, a bonus the game put back is raised again to its own times 1.5",
          fastest.keep("runner", runner) == {"boost": "again", "game_value": 0.9} and bonus(runner) == 1.35
          and fastest.keep("runner", runner) is None)
    check("and at the let-go, the game's own bonus is written back, not the raised one",
          fastest.put_back("runner", runner) == "restored" and bonus(runner) == 0.9)

    events.clear()
    normal = speed.SpeedBoost(announce, 1.0)
    calm = [enemy(f"calm_{index}", 0.9) for index in range(3)]
    started = normal.start([chaser(f"calm_{index}", mover) for index, mover in enumerate(calm)])
    calm[0].CharacterMovement.MaxGroundSpeedScale._value = 0.5
    check("decision 48: Normal writes nothing and says nothing; the game's bonus left alone even when it changes",
          started == [] and normal.keep("calm_0", calm[0]) is None and normal.keep("calm_1", calm[1]) is None
          and normal.put_back("calm_1", calm[1]) == "not_boosted" and events == []
          and [bonus(mover) for mover in calm] == [0.5, 0.9, 0.9])
    check("a factor within SAME of 1 is Normal too, one beyond it is not",
          speed.SpeedBoost(announce, 1.0 + speed.SAME / 2.0).start([chaser("calm_2", calm[2])]) == [] and events == []
          and len(speed.SpeedBoost(announce, 1.0 + 2.0 * speed.SAME).start([chaser("calm_2", calm[2])])) == 1
          and bonus(calm[2]) == round(0.9 * (1.0 + 2.0 * speed.SAME), 3))

    crowd = speed.SpeedBoost(announce, 1.3)
    many = [enemy(f"enemy_{index}") for index in range(1000)]
    crowd.start([chaser(f"enemy_{index}", mover) for index, mover in enumerate(many)])
    raised = len(crowd.base)
    for index, mover in enumerate(many):
        crowd.put_back(f"enemy_{index}", None if index % 3 == 0 else mover)
    check("every enemy let go is forgotten, written back or not: the table holds no more than the horde",
          raised == 1000 and crowd.base == {})
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
