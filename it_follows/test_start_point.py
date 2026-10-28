"""Tests START with a starting point (start_point.py), the trip replaced by one that is told how to end: the trip asked
to the place the settings name, TRAVELLING, or the trip's refusal as it is; on arrival the run made with the settings
of START, the controller and the character then in the game; a run that cannot start then, a character gone, a run
that does not start: the reason kept for the window, which is asked to open; a trip that ends badly the same; a trip
cancelled says nothing; the reason read once; a window that cannot open never raises into the trip; travelling and
cancel the trip's own. Then the real trip in a fake game (trip_fixture.py): the run made once the cover is over."""

import json
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import trip_fixture  # noqa: E402
from it_follows import start_point  # noqa: E402

real_trip = start_point.start_trip
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Trip:
    """start_trip as start_point sees it: go answers `answer` and keeps the two calls; cancel kept."""

    CANCELLED = "cancelled"

    def __init__(self, answer: str = "") -> None:
        self.answer, self.asked, self.cancelled, self.going = answer, [], [], False

    def go(self, place, pc, character, arrived, failed) -> str:
        self.asked.append((place, pc, character))
        self.arrived, self.failed = arrived, failed
        return self.answer

    def travelling(self) -> bool:
        return self.going

    def cancel(self, why: str) -> None:
        self.cancelled.append(why)


class Window:
    def __init__(self, raises: bool = False) -> None:
        self.opened, self.raises = 0, raises

    def __call__(self) -> None:
        self.opened += 1
        if self.raises:
            raise RuntimeError("no window here")


def events(name: str) -> list[dict]:
    lines = [json.loads(line.removeprefix("[It Follows] ")) for line in state["info"]
             if line.startswith("[It Follows] {")]
    return [line for line in lines if line["event"] == name]


settings = types.SimpleNamespace(start_place=11)
pc, hunter = types.SimpleNamespace(OakCharacter=None), object()
pc.OakCharacter = hunter
state["pc"] = pc
made: list[tuple] = []


def begin(given, controller, character, players) -> str:
    made.append((given, controller, character, players))
    return begin.answer


begin.answer = "started"
busy = types.SimpleNamespace(why="")

trip = start_point.start_trip = Trip()
window = Window()
check("the trip asked to the place the settings name: travelling",
      start_point.go(settings, pc, hunter, window, begin, lambda: busy.why) == "travelling"
      and trip.asked == [(start_point.start_places.find(11), pc, hunter)] and not made
      and events("start_trip_asked")[-1]["place"] == 11)
trip.arrived()
check("on arrival the run made with the settings of START, the controller and the character in the game",
      made == [(settings, pc, hunter, None)] and window.opened == 0 and start_point.take_outcome() is None)

trip = start_point.start_trip = Trip("not_open_world")
check("the trip's refusal answered as it is", start_point.go(settings, pc, hunter, window, begin, lambda: busy.why)
      == "not_open_world")

trip = start_point.start_trip = Trip()
start_point.go(settings, pc, hunter, window, begin, lambda: busy.why)
busy.why = "normal_on"
made.clear()
trip.arrived()
check("a run that cannot start on arrival: none made, the arrival's reason kept, the window asked to open",
      not made and window.opened == 1 and start_point.take_outcome() == "arrival_refused")
check("the reason read once", start_point.take_outcome() is None)
busy.why = "coop"
start_point.go(settings, pc, hunter, window, begin, lambda: busy.why)
start_point.start_trip.arrived()
check("a friend joined on the way: no run, said as such", not made and start_point.take_outcome()
      == "arrival_coop")
window.opened -= 1
busy.why = ""
start_point._state["outcome"] = "no_floor"
start_point.go(settings, pc, hunter, window, begin, lambda: busy.why)
check("a new trip forgets the last one's reason", start_point.take_outcome() is None)

pc.OakCharacter = None
start_point.go(settings, pc, hunter, window, begin, lambda: busy.why)
trip = start_point.start_trip
trip.arrived()
check("the character gone on arrival: no run, said to the window", not made and window.opened == 2
      and start_point.take_outcome() == "arrival_refused")
pc.OakCharacter = hunter

begin.answer = "start_failed"
start_point.go(settings, pc, hunter, window, begin, lambda: busy.why)
trip.arrived()
check("a run that does not start: its reason to the window", window.opened == 3
      and start_point.take_outcome() == "arrival_refused")
begin.answer = "started"

start_point.go(settings, pc, hunter, window, begin, lambda: busy.why)
trip.failed("no_floor")
check("a trip that ends badly: its reason to the window, said in the log", window.opened == 4
      and start_point.take_outcome() == "no_floor" and events("start_trip_failed")[-1]["outcome"] == "no_floor"
      and any("No run started at the starting point" in line for line in state["info"]))
trip.failed("cancelled")
check("a trip cancelled says nothing to the window", window.opened == 4 and start_point.take_outcome() is None)
start_point.go(settings, pc, hunter, Window(raises=True), begin, lambda: busy.why)
try:
    trip.failed("hold_failed")
    raised = False
except Exception:
    raised = True
check("a window that cannot open never raises into the trip", not raised
      and events("start_reopen_failed")[-1]["error"] == "RuntimeError" and start_point.take_outcome() == "hold_failed")
start_point.go(settings, pc, hunter, None, begin, lambda: busy.why)
trip.failed("no_floor")
check("no window to ask: the reason kept all the same", start_point.take_outcome() == "no_floor")

trip.going = True
start_point.cancel("the mod switched off")
check("travelling and cancel the trip's own", start_point.travelling() and trip.cancelled == ["the mod switched off"])

# The real trip at the boundary, in a fake game: the run made once the cover is over, with what START gave.
start_point.start_trip = real_trip
game = trip_fixture.Game()
game.install(state)
clock = trip_fixture.Clock()
real_trip.clock = real_trip.cover.clock = clock
made.clear()
window = Window()
check("the real trip asked: on the way", start_point.go(settings, game.pc, game.character, window, begin, lambda: "")
      == "travelling" and real_trip.travelling() and not made)
game.floor = start_point.start_places.find(11).spot[2] - 95.0
game.pc.ignored = False
for _ in range(500):
    clock.now += 0.011
    trip_fixture.Game.run(state)
check("the cover over: the run made once, with START's settings, the window left closed",
      made == [(settings, game.pc, game.character, None)] and not real_trip.travelling() and window.opened == 0
      and not state["hooks"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
