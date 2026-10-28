"""Tests a trip to a starting point (start_trip.py) in a fake game: refused outside the open world and while a trip is
under way, nothing moved; a move the game refuses gives the cover back; on his way, the player on Kevin's mark, the
image black and the hunter shielded, each call written before it is made; held on the mark while no floor is there;
a floor kept STABLE_S, and not less, lets him go turned the way Kevin faced; a floor that moves starts the wait again;
a floor deeper than MARK_DROP_CM is none; HOLD_S without a floor sends him back and says so once; arrived() once, only
when the cover is over; a turn the game refuses said, the trip going on; the character gone, the trace broken, an
error and cancel each ending the trip badly, the cover given back, the player sent back when he is still there."""

import pathlib
from types import SimpleNamespace
import sys
import threading

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import trip_fixture  # noqa: E402
from it_follows import start_cover, start_hold as hold, start_places, start_trip  # noqa: E402

fails: list[str] = []
clock = trip_fixture.Clock()
start_trip.clock = start_cover.clock = clock
PLACE = start_places.find("3")
STEP = hold.HOLD_EVERY_S * 1.1
BLACK = ("fade", 0.0, 1.0, 0.0, True)
TRIP, COVER = start_trip.IDENTIFIER, start_cover.IDENTIFIER


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Run:
    """One trip: the fake game, and what the trip told the session."""

    def __init__(self, world: str = "World_P", **refuse: bool) -> None:
        state["info"].clear()
        state["hooks"].clear()
        start_trip._trip.clear()
        start_cover._state.clear()
        self.game = trip_fixture.Game(world=world)
        self.game.install(state)
        self.game.refuse.update(refuse)
        self.arrived: list[float] = []
        self.failed: list[str] = []

    def go(self) -> str:
        return start_trip.go(PLACE, self.game.pc, self.game.character, lambda: self.arrived.append(clock.now),
                             self.failed.append)

    def wait(self, seconds: float) -> None:
        end = clock.now + seconds
        while clock.now < end:
            clock.now += STEP
            trip_fixture.Game.run(state)

    def said(self, words: str) -> bool:
        return any(words in line for line in state["info"])


run = Run(world="Arena_Boss_P")
check("refused outside the open world, nothing moved", run.go() == "not_open_world"
      and not run.game.character.moves and not run.game.camera and not state["hooks"])

run = Run(move=True)
check("a move the game refuses: nothing moved, the cover given back", run.go() == "move_failed"
      and run.game.camera == [BLACK, ("stop",)] and run.game.character.bCanBeDamaged is True and not state["hooks"]
      and not start_trip.travelling())

run = Run()
home = run.game.character.at
check("on his way: on Kevin's mark, the image black, the hunter shielded", run.go() == ""
      and run.game.character.moves == [PLACE.spot] and run.game.camera == [BLACK]
      and run.game.character.bCanBeDamaged is False and set(state["hooks"]) == {TRIP, COVER})
check("the move written before it is made", run.said("call K2_TeleportTo")
      and run.game.lines_before_move[0] > next(index for index, line in enumerate(state["info"])
                                               if "call K2_TeleportTo" in line))
check("a second trip refused while one is under way", run.go() == "trip_going" and len(run.game.character.moves) == 1)
clock.now += STEP
trip_fixture.Game.run(state)
trip_fixture.Game.run(state)
check("put back once an image at most, however often the game calls", len(run.game.character.moves) == 2)
run.wait(2.0)
check("held on the mark while no floor is there, his speed set to nothing",
      len(run.game.character.moves) > 100 and set(run.game.character.moves) == {PLACE.spot}
      and run.game.character.CharacterMovement.Velocity.X == 0.0 and not run.game.pc.turns)
run.game.floor = PLACE.spot[2] - 95.0
run.wait(0.9)
check("a floor there for less than STABLE_S: not let go", not run.game.pc.turns and not start_cover._state["landed"])
run.wait(0.6)
check("a floor kept STABLE_S: turned the way Kevin faced, let go", run.game.pc.turns == [(PLACE.yaw, False)]
      and start_cover._state["landed"] and run.said("let go on it"))
run.game.pc.ignored = False
run.wait(0.3)
check("let go, the cover not over: no run yet", not run.arrived and start_cover.covered())
run.wait(start_cover.GRACE_S + 0.3)
check("the cover over: arrived once, the trip's hook off, the shield back", len(run.arrived) == 1 and not run.failed
      and not state["hooks"] and run.game.character.bCanBeDamaged is True and not start_trip.travelling())
run.wait(1.0)
check("arrived once only", len(run.arrived) == 1)

run = Run()
run.go()
run.game.floor = PLACE.spot[2] - 95.0
run.wait(0.8)
run.game.floor -= 30.0
run.wait(0.8)
check("a floor that moves starts the wait again", not run.game.pc.turns)
run.wait(0.6)
check("then kept STABLE_S: let go", run.game.pc.turns == [(PLACE.yaw, False)])

run = Run()
run.go()
run.game.floor = PLACE.spot[2] - hold.MARK_DROP_CM - 10.0
run.wait(hold.HOLD_S - 0.5)
check("a floor deeper than MARK_DROP_CM is none: still held", start_trip.travelling() and not run.game.pc.turns)
run.wait(1.0)
check("HOLD_S without a floor: sent back where he left from and held there, still covered, nothing said yet",
      not run.failed and run.game.character.at == home and ("stop",) not in run.game.camera
      and run.game.character.bCanBeDamaged is False and start_trip.travelling())
run.game.floor = home[2] - 95.0
run.wait(0.5)
check("a floor under home for less than STABLE_S: still held", not run.failed and start_trip.travelling())
run.wait(0.7)
check("a floor under home kept STABLE_S: the cover given back, said once, not turned",
      run.failed == ["no_floor"] and ("stop",) in run.game.camera and run.game.character.bCanBeDamaged is True
      and not state["hooks"] and not run.arrived and not run.game.pc.turns and run.game.character.at == home)
run.wait(1.0)
check("said once only", run.failed == ["no_floor"])

run = Run()
run.go()
run.wait(hold.HOLD_S + 0.5)
run.wait(hold.HOLD_S + 0.5)
check("no floor under home either: given back there all the same, the first reason said",
      run.failed == ["no_floor"] and run.game.character.at == home and not state["hooks"]
      and run.game.character.bCanBeDamaged is True)

run = Run(turn=True)
run.go()
run.game.floor = PLACE.spot[2] - 95.0
run.game.pc.ignored = False
run.wait(1.5 + start_cover.FADE_IN_S + start_cover.GRACE_S + 0.5)
check("a turn the game refuses said, the trip going on to the run", run.said("SetControlRotation, facing")
      and run.said("failed (RuntimeError") and len(run.arrived) == 1)

run = Run()
run.go()
run.wait(0.5)
run.game.character.freed = True
run.wait(0.1)
check("the character gone: the trip ended badly, the cover given back, nothing moved after",
      run.failed == ["character_gone"] and ("stop",) in run.game.camera and not state["hooks"]
      and run.game.character.at == PLACE.spot)

run = Run()
run.go()
run.game.refuse["trace"] = True
run.wait(0.5)
check("the trace broken: the trip ended badly, sent back", run.failed == ["hold_failed"]
      and run.game.character.at == home and not state["hooks"])

run = Run()
run.go()
run.game.refuse["broken"] = True
run.wait(0.1)
run.game.refuse["broken"] = False
check("an error in the hold: ended badly, never raised out of the hook", run.failed == ["hold_failed"]
      and run.said("stopped on an error (RuntimeError") and not state["hooks"])

run = Run()
run.go()
run.game.floor = PLACE.spot[2] - 95.0
run.wait(1.5)
start_cover.give_back("given up")
run.wait(0.1)
check("the cover given up after the player was let go: no run, sent back and held there",
      not run.arrived and start_trip.travelling() and run.game.character.at == home)
run.game.floor = home[2] - 95.0
run.wait(1.5)
check("then back on a floor: said as an error, no run", run.failed == ["hold_failed"] and not run.arrived)

run = Run()
run.go()
run.wait(hold.HOLD_S + 0.5)
run.game.refuse["trace"] = True
run.wait(0.5)
check("a second fault on the way back: given back there, the first reason said", run.failed == ["no_floor"]
      and not state["hooks"] and run.game.character.bCanBeDamaged is True)

run = Run()
run.go()
run.wait(0.5)
start_trip._end("a first end", start_trip.NO_FLOOR)
start_trip.cancel("the mod switched off")
check("cancel on the way back: given back at once, said as cancelled", run.failed == ["cancelled"]
      and not state["hooks"] and run.game.character.bCanBeDamaged is True)

run = Run()
run.go()
run.wait(0.5)
start_trip.cover = SimpleNamespace(**{**vars(start_cover), "give_back": lambda why: 1 / 0})
run.game.character.freed = True
try:
    run.wait(0.1)
    quiet = True
except Exception:
    quiet = False
start_trip.cover = start_cover
check("an error once the trip has ended: written, never raised out of the hook", quiet
      and run.said("start_trip_error_after_end") and not start_trip.travelling())
state["hooks"].clear()
start_cover._state.clear()

times = iter([10.0, 10.02, 10.04, 40.04, 40.06])
monotonic = hold.time.monotonic
hold.time.monotonic = lambda: next(times)
hold._clock.update(last=None, left_out=0.0)
read = [hold.clock() for _ in range(5)]
hold.time.monotonic = monotonic
check("the trip's clock leaves a pause out: 30 s paused on the black screen count for nothing",
      [round(value - read[0], 2) for value in read] == [0.0, 0.02, 0.04, 0.04, 0.06])

run = Run()
run.go()
held = start_trip._trip["ticked"]
clock.now += hold.HOLD_EVERY_S * 2
worker = threading.Thread(target=lambda: start_trip._frame(None, None, None, None))
worker.start()
worker.join(5)
check("a call on another thread than the game's: the hunter not held (trial 206)",
      start_trip._trip["ticked"] == held)
start_trip._frame(None, None, None, None)
check("the next on the game's thread: held", start_trip._trip["ticked"] == clock.now)
start_trip.cancel("the mod switched off")
check("cancel: ended badly as cancelled, sent back, the cover given back", run.failed == ["cancelled"]
      and run.game.character.at == home and ("stop",) in run.game.camera and not start_trip.travelling())
state["info"].clear()
start_trip.cancel("nothing under way")
check("cancel with no trip: nothing", not state["info"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
