"""Tests BL4 Arena's cover as It Follows copies it (start_cover.py): covered, the image black at once and held, the
hunter shielded, under It Follows' hook; the keys back before the trip lets the player go change nothing; let go, the
keys back: the image back in FADE_IN_S, the shield GRACE_S later, back to its value before; the character gone gives
both back at once; a cover past MAX_S, the trip's longest hold and room for the keys, gives both back; each line of
the log one of the trip's events; nothing let go nor given back when nothing is covered."""

import json
import pathlib
import sys
import threading

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import trip_fixture  # noqa: E402
from it_follows import start_cover as cover, start_hold as hold  # noqa: E402

fails: list[str] = []
clock = trip_fixture.Clock()
cover.clock = clock
BLACK = ("fade", 0.0, 1.0, 0.0, True)
BACK_IN = ("fade", 1.0, 0.0, cover.FADE_IN_S, False)


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def fresh() -> trip_fixture.Game:
    state["info"].clear()
    state["hooks"].clear()
    cover._state.clear()
    game = trip_fixture.Game()
    game.install(state)
    return game


def tick(seconds: float = cover.EVERY_S * 1.01) -> None:
    clock.now += seconds
    trip_fixture.Game.run(state)


def events() -> list[dict]:
    return [json.loads(line.removeprefix("[It Follows] ")) for line in state["info"]]


game = fresh()
cover.cover(4, game.character, game.pc)
check("covered: the image black at once and held, the hunter shielded, under It Follows' hook",
      game.camera == [BLACK] and game.character.bCanBeDamaged is False and cover.covered()
      and list(state["hooks"]) == ["it_follows:start_cover"])
check("each line of the log one of the trip's events, with its number",
      events() and all(event["event"] == "start_trip" and event["trip"] == 4 for event in events()))
game.pc.ignored = False
tick()
tick(5.0)
check("the keys back before the trip lets the player go: still black and shielded",
      game.camera == [BLACK] and game.character.bCanBeDamaged is False and cover.covered())
cover.landed()
tick()
check("let go, the keys back: the image back in FADE_IN_S, the shield still on",
      game.camera == [BLACK, BACK_IN] and game.character.bCanBeDamaged is False and cover.covered())
tick(cover.GRACE_S)
check("GRACE_S later the shield back to its value before, the cover over",
      game.character.bCanBeDamaged is True and not cover.covered() and not state["hooks"])
check("ended as it should: the trip may start its run", cover.ended_well())

game = fresh()
cover.cover(5, game.character, game.pc)
game.pc.ignored = False
cover.landed()
state["pc"] = None
game.character = None
cover._state["pawn"] = lambda: None
tick()
check("the character gone: both given back at once", game.camera == [BLACK, ("stop",)] and not cover.covered())

game = fresh()
cover.cover(6, game.character, game.pc)
tick(cover.MAX_S + 0.1)
check("past MAX_S, 25 s of hold (trial 97: 2.1 to 6.4 s) and 30 s for the keys: both given back",
      hold.HOLD_S == 25.0 and cover.MAX_S == 55.0 and game.camera == [BLACK, ("stop",)]
      and game.character.bCanBeDamaged is True and not cover.covered())
check("given up: not ended as it should, no run", not cover.ended_well())

game = fresh()
cover.cover(7, game.character, game.pc)
check("under way: not ended", not cover.ended_well())
cover.give_back("the trip ended badly")
clock.now += 1.0
cover._frame(None, None, None, None)
check("its hook called once more after giving back, in the same pass: the state left empty",
      not cover._state)
cover.cover(8, game.character, game.pc)
check("and the next trip covered as the first", cover.covered() and cover._state["number"] == 8)
cover.give_back("done")
game.refuse["fade"] = True
game.character = None
cover.cover(9, None, game.pc)
check("nothing set to wait for: the trip goes on, counted as ended well", not cover.covered()
      and cover.ended_well())

game = fresh()
cover.cover(10, game.character, game.pc)
looked = cover._state["ticked"]
clock.now += cover.EVERY_S * 2
worker = threading.Thread(target=lambda: trip_fixture.Game.run(state))
worker.start()
worker.join(5)
check("a call on another thread than the game's: nothing looked at (trial 206)",
      cover._state["ticked"] == looked)
trip_fixture.Game.run(state)
check("the next on the game's thread: looked at", cover._state["ticked"] == clock.now)
cover.give_back("done")
state["info"].clear()
cover.landed()
cover.give_back("nothing covered")
check("nothing let go nor given back when nothing is covered", not state["info"] and not cover._state)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
