"""Tests the run's heartbeat: the animation update hooked after each call under the run's own name; a tick a second
at most, the first a second after the start; an error in a tick stops the run with its kind; the hook removed at the
stop, a second stop touching nothing, a removal that fails said; a beat given its own name (the normal mode's) hooked
under it. Work put off: one task an image, the first once the character that gave the tick is updated again (or after
LATER_MOST_S), in the order put off, a name never waiting twice, an error stopping the run, nothing run once stopped;
the hook's calls a second counted, with the µs a call with nothing to do took in the beat, ticks and tasks put off
left out (audit of 16 October 2026, A11)."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import frame  # noqa: E402

fails: list[str] = []
clock = [100.0]
frame.time = types.SimpleNamespace(monotonic=lambda: clock[0])
real_perf_counter = frame.perf_counter


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Anim:
    """An animated character's update: known by its address only."""

    def __init__(self, address: int) -> None:
        self.address = address

    def _get_address(self) -> int:
        return self.address


PLAYER, ENEMY = Anim(1), Anim(2)


def call(at: float, obj: object = None) -> None:
    clock[0] = at
    hooked = state["hooks"].get(frame.IDENTIFIER)
    if hooked is not None:
        hooked.fn(obj, None, None, None)


try:
    ticks: list[float] = []
    failures: list[str] = []
    beat = frame.Beat(ticks.append, failures.append)
    beat.start()
    check("the animation update is hooked under the run's own name", frame.IDENTIFIER in state["hooks"]
          and state["hooks"][frame.IDENTIFIER].enabled)
    for at in (100.0, 100.5, 100.99):
        call(at)
    check("no tick before a second", ticks == [])
    for at in (101.0, 101.3, 101.9, 102.0, 102.4, 104.7):
        call(at)
    check("a tick a second at most, at the call that passes it", ticks == [101.0, 102.0, 104.7])

    def broken(_now: float) -> None:
        raise ValueError("bad sample")

    beat.tick = broken
    call(106.0)
    check("an error in a tick stops the run with its kind", failures == ["error:ValueError"])
    check("the stop removes the hook", beat.stop() == "removed" and frame.IDENTIFIER not in state["hooks"])
    call(110.0)
    check("no tick once stopped", ticks == [101.0, 102.0, 104.7])
    check("a second stop touches nothing", beat.stop() == "inactive")
    stuck = frame.Beat(ticks.append, failures.append)
    stuck.start()

    def refuse() -> None:
        raise RuntimeError("cannot")

    stuck.hook.disable = refuse
    check("a removal that fails says so", stuck.stop() == "remove_failed")
    state["hooks"].clear()
    other = frame.Beat(ticks.append, failures.append, "it_follows:normal")
    other.start()
    check("a beat given its own name hooks under it, never under the run's",
          "it_follows:normal" in state["hooks"] and frame.IDENTIFIER not in state["hooks"]
          and other.stop() == "removed" and not state["hooks"])

    done: list[tuple] = []
    def second_put_off(at: float) -> None:
        done.append(("tick", at))
        spread.defer("census", lambda t: done.append(("census", t)))
        spread.defer("camps", lambda t: done.append(("camps", t)))
        spread.defer("census", lambda t: done.append(("twice", t)))

    spread = frame.Beat(second_put_off, failures.append)
    spread.start()
    call(201.0, PLAYER)
    check("the tick puts work off: nothing more in its image", done == [("tick", 201.0)] and len(spread.later) == 2)
    call(201.001, ENEMY)
    call(201.002, ENEMY)
    check("the same image's other characters run nothing", done == [("tick", 201.0)])
    call(201.016, PLAYER)
    check("the next image, known by the character of the tick updated again: one task, the first put off",
          done[-1] == ("census", 201.016) and len(spread.later) == 1)
    call(201.017, ENEMY)
    check("one task an image only", len(done) == 2)
    call(201.033, PLAYER)
    check("then the next: a name put off twice ran once", done[-1] == ("camps", 201.033) and spread.later == {}
          and not [entry for entry in done if entry[0] == "twice"])
    spread.defer("late", lambda t: done.append(("late", t)))
    call(201.040, ENEMY)
    check("waiting for a character never updated again", done[-1][0] == "camps")
    call(201.034 + frame.LATER_MOST_S, ENEMY)
    check("gives the task its image after LATER_MOST_S", done[-1][0] == "late")
    spread.defer("broken", lambda t: (_ for _ in ()).throw(KeyError("x")))
    spread.defer("after", lambda t: done.append(("after", t)))
    failures.clear()
    spread.fail = lambda reason: (failures.append(reason), spread.stop())
    call(201.2, ENEMY)
    check("a task that raises stops the run with its kind, the tasks after it dropped",
          failures == ["error:KeyError"] and spread.later == {} and spread.hook is None)
    call(201.3, PLAYER)
    check("nothing run once stopped", done[-1][0] == "late")
    counted = frame.Beat(lambda at: None, failures.append)
    clock[0] = 300.0
    counted.start()
    precise = [0.0]

    def two_us() -> float:
        precise[0] += 0.000002
        return precise[0]

    frame.perf_counter = two_us
    for step in range(90):
        call(300.0 + step / 100.0, ENEMY)
    clock[0] = 300.9
    said = counted.gauge()
    check("the hook's calls a second counted, and the µs a call with nothing to do took, then counted again from "
          "nothing", said["hook_calls_s"] == 100.0 and said["hook_idle_us"] == 2.0 and counted.calls == 0
          and counted.idle_calls == 0 and counted.idle_s == 0.0)
    clock[0] = 302.0
    call(302.0, ENEMY)
    counted.defer("task", lambda at: None)
    call(302.1, PLAYER)
    said = counted.gauge()
    check("a tick and a task put off are not calls with nothing to do",
          said["hook_idle_us"] is None and said["hook_calls_s"] > 0.0)
    frame.perf_counter = real_perf_counter
    counted.stop()
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
