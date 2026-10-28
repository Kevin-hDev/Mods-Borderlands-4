"""Tests the frame clock's sleep and wake-up: the game's three signals hooked after the game runs them, under the mod's
own identifier; the clock kept while anyone drives and for a window after, then put to sleep, said once; a signal
waking it, said with its cause, the window opened so the frame looks for itself; a signal while awake only widening the
window; a cause the game will not name said plainly; a reset leaving it awake."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402
from sdk_stubs_options import FakeHook  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = sdk_stubs.install()

from vehicle_driving import wake  # noqa: E402

MS = 1_000_000
RESTART = "/Script/Engine.PlayerController:ClientRestart"
PAWN = "/Script/Engine.Controller:OnRep_Pawn"
ECHO = ("/Game/PlayerCharacters/_Shared/GBXScripts/Script_Echo4.Script_Echo4_C"
        ":GbxActorScriptEvt__VehicleScriptEvents_OnStartedDriving")


def named(name: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(func=types.SimpleNamespace(Name=name))


check("the three signals seen at each entry in game are hooked after the game runs them, under the mod's own name",
      wake.woken.funcs == [(RESTART, "POST"), (PAWN, "POST"), (ECHO, "POST")]
      and wake.woken.identifier == "vehicle_driving:wake")

clock = FakeHook(lambda *a: None, "frame", "POST", "vehicle_driving:frame")
clock.enable()
wake.watch(clock)

wake.settle(1000 * MS, True)
check("someone drives: the clock runs", clock.enabled and clock.disables == 0)
wake.settle(1000 * MS + wake.WINDOW_NS - 1, False)
check("nobody drives any more: the clock runs on for the window", clock.enabled)
wake.settle(1000 * MS + wake.WINDOW_NS, False)
check("then sleeps, said once", not clock.enabled and clock.disables == 1
      and state["misc"][-1] == "[Vehicle Driving] asleep: nobody drives")
wake.settle(1000 * MS + wake.WINDOW_NS, False)
check("asleep, a late frame changes nothing", clock.disables == 1 and len(state["misc"]) == 1)

wake.settle(2000 * MS, True)
wake.settle(2000 * MS + wake.WINDOW_NS, False)
check("a clock running again without a signal, as mods_base enables it with the mod, sleeps again",
      not clock.enabled and clock.disables == 2)
clock.enable()
wake.wake_at(5000 * MS, "ClientRestart")
check("a signal wakes the clock, said with its cause",
      clock.enabled and clock.enables == 3 and state["misc"][-1] == "[Vehicle Driving] woken by ClientRestart")
wake.settle(5000 * MS + wake.WINDOW_NS - 1, False)
check("the body may not be there yet: the clock looks for the window", clock.enabled)
wake.wake_at(5500 * MS, "OnRep_Pawn")
check("a signal while awake only widens the window", clock.enables == 3 and len(state["misc"]) == 3)
wake.settle(5000 * MS + wake.WINDOW_NS, False)
check("widened from the last signal", clock.enabled)
wake.settle(5500 * MS + wake.WINDOW_NS, False)
check("and sleeps at its end", not clock.enabled)

wake.time.perf_counter_ns = lambda: 8000 * MS
wake.woken(object(), None, None, named("ClientRestart"))
check("the hook wakes the clock with the function's name", clock.enabled
      and state["misc"][-1] == "[Vehicle Driving] woken by ClientRestart")
wake.settle(10 ** 15, False)
wake.woken(object(), None, None, object())
check("a function the game will not name still wakes it", clock.enabled
      and state["misc"][-1] == "[Vehicle Driving] woken by a signal of the game")

wake.settle(2 * 10 ** 15, False)
check("asleep before the mod is switched off", not clock.enabled and clock.enables == 5)
wake.reset()
clock.enable()
wake.wake_at(2 * 10 ** 15 + 1, "ClientRestart")
check("after a reset it counts as awake, as mods_base enables the clock with the mod: a signal enables nothing more",
      clock.enables == 6 and state["misc"][-1] != "[Vehicle Driving] woken by ClientRestart")
wake.settle(2 * 10 ** 15 + 1 + wake.WINDOW_NS, False)
check("and it sleeps as before once nobody drives", not clock.enabled)

print(f"RESULTAT: {'ECHEC' if fails else 'OK'} ({len(fails)} echec(s))")
sys.exit(1 if fails else 0)
