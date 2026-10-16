"""Tests the second's pass over the horde in parts (decision 107): PART enemies a part, in the catch-up's order, the
first in the second's own image, each other put off to an image of its own, where the hunter, his place and where he
looks are read again and the part is timed; once the last is done, the float watch, the wave regulated on the whole
pass's lines, where the horde stands, and the wave's tick; a horde of a part or none done at once; a pass not done
when the next begins counted cut, every enemy taken again; a part without the hunter drops the pass; the most parts,
the longest part and the passes cut said, then counted afresh."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402
from sdk_stubs import vector  # noqa: E402

state = sdk_stubs.install()

from it_follows import sweep as sweep_module, wave  # noqa: E402

fails: list[str] = []
calls: list[tuple] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Horde:
    def __init__(self, count: int) -> None:
        self.chasers = [f"enemy_{number}" for number in range(count)]

    def drawn(self) -> list:
        return list(self.chasers)

    def sample(self, chasers: list, player: object, pc: object, here: object, now: float) -> list[dict]:
        calls.append(("sample", list(chasers), player, pc, here, now))
        return [{"target": None, "to_player_m": 10.0} for _ in chasers]


class Hunter:
    def __init__(self, x: float) -> None:
        self.x = x

    def K2_GetActorLocation(self) -> object:
        return vector(self.x, 0.0, 0.0)


later: dict = {}
hunter = [Hunter(100.0)]
parts = types.SimpleNamespace(
    catch=types.SimpleNamespace(queue=lambda chasers: list(reversed(chasers)),
                                look=lambda pc: calls.append(("look", pc))),
    wave=types.SimpleNamespace(regulate=lambda near, count: calls.append(("regulate", near, count)),
                               tick=lambda player, pc, here, now: calls.append(("tick", player, pc, here, now))))
floating = types.SimpleNamespace(look=lambda chasers, now: calls.append(("float", list(chasers), now)))


def made(horde: Horde) -> sweep_module.Sweep:
    return sweep_module.Sweep(horde, parts, floating, lambda name, task: later.setdefault(name, task),
                              lambda: hunter[0], lambda: "pc_again",
                              lambda name, began: calls.append(("timed", name, began)), lambda: 7.0)


def run_later(now: float) -> None:
    later.pop("sweep")(now)


def named(kind: str) -> list[tuple]:
    return [call for call in calls if call[0] == kind]


try:
    horde = Horde(70)
    sweep = made(horde)
    sweep.start("player", "pc", (0.0, 0.0, 0.0), 1.0)
    order = list(reversed(horde.chasers))
    check("the first part, PART enemies in the catch-up's order, made in the second's own image with its hunter",
          calls == [("sample", order[:30], "player", "pc", (0.0, 0.0, 0.0), 1.0)] and list(later) == ["sweep"])
    calls.clear()
    run_later(1.1)
    check("the next part in an image of its own: the hunter and where he looks read again, then timed",
          [call[0] for call in calls] == ["look", "sample", "timed"] and calls[0] == ("look", "pc_again")
          and calls[1] == ("sample", order[30:60], hunter[0], "pc_again", (100.0, 0.0, 0.0), 1.1)
          and calls[2] == ("timed", "sweep", 7.0) and list(later) == ["sweep"])
    calls.clear()
    run_later(1.2)
    check("once the last part is done: the float watch on the horde, the wave regulated on the whole pass, where the "
          "horde stands, the wave's tick; nothing put off again",
          [call[0] for call in calls] == ["look", "sample", "float", "regulate", "tick", "timed"]
          and named("sample")[0][1] == order[60:] and named("float")[0][1:] == (horde.chasers, 1.2)
          and named("regulate")[0][2] == 70 and named("tick")[0][1:] == (hunter[0], "pc_again", (100.0, 0.0, 0.0), 1.2)
          and sweep.horde_at == wave.where([{"target": None, "to_player_m": 10.0}] * 70) and later == {})
    check("the most parts, the longest part and the passes cut said, then counted afresh",
          (said := sweep.gauge())["parts"] == 3 and said["cut"] == 0 and said["part_ms"] >= 0.0
          and sweep.gauge() == {"parts": 0, "part_ms": 0.0, "cut": 0})

    for count in (30, 0):
        calls.clear()
        small = made(Horde(count))
        small.start("player", "pc", None, 2.0)
        check(f"a horde of {count}: the whole pass and its end in the second's own image",
              [call[0] for call in calls] == ["sample", "float", "regulate", "tick"] and later == {}
              and named("regulate")[0][2] == count)

    calls.clear()
    sweep = made(Horde(70))
    sweep.start("player", "pc", None, 3.0)
    sweep.start("player", "pc", None, 4.0)
    check("a pass not done when the next begins: counted cut, every enemy taken again, its end not run",
          sweep.gauge()["cut"] == 1 and len(sweep.queue) == 40 and named("regulate") == [])
    calls.clear()
    hunter[0] = None
    run_later(4.1)
    check("a part without the hunter: the pass dropped, nothing read, nothing put off",
          calls == [] and sweep.queue == [] and later == {})
except Exception as error:
    check(f"exception {type(error).__name__}: {error}", False)

print(f"RESULTAT: {'TOUS LES TESTS PASSENT' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
