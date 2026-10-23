"""Tests the companions left on their way when their team stops (companions/strays.py), the game faked
(companion_fixture.py): nothing asked, no watch; one asked, its own hook set, said; not born yet, looked for again;
born of its spawner, taken out of the world, said, the hook removed once none is left; never born, given up after
FIND_S of play, a pause or a map loading not counted; an unknown companion given up at once; a spawner a team asks
again watched no more; MOST at most, the oldest dropped; the world not read, said once, those looked for still given
up in time; a beat on another thread does nothing; a second team's stop adds to the same watch, one hook. Through the
team: test_companions_team.py."""

import json
import pathlib
import sys
import threading

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import companion_fixture as fake  # noqa: E402
from characters.companions import respawn, strays  # noqa: E402

fails: list[str] = []
HOOK = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
IDENTIFIER = "characters:companions_strays"
CRANKUS = "Char_GunToter_SiblingRivalry_Crankus"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    found = [json.loads(text.removeprefix("[Characters] ")) for text in state["info"]
             if text.startswith("[Characters] {")]
    return [{key: value for key, value in line.items() if key != "run"} for line in found if line["event"] == event]


def beat(clock: fake.Clock, moment: float) -> None:
    clock.now = moment
    hook = state["hooks"].get(IDENTIFIER)
    if hook is not None:
        hook.fn()


def play(clock: fake.Clock, until: float, step: float = 0.1) -> None:
    """The game running from now until then, a beat each step."""
    while clock.now + step <= until + 1e-9:
        beat(clock, round(clock.now + step, 6))


def spawners() -> list[str]:
    watch = strays._watch["strays"]
    return [] if watch is None else [one["spawner"] for one in watch.looked]


check("two teams' worth looked for at most; a beat counts a quarter of a second at most", strays.MOST == 16
      and strays.MAX_STEP_S == 0.25)
game = fake.Game(state)
clock = fake.Clock()
strays.watch([], clock, HOOK, IDENTIFIER)
check("nothing asked: no watch, no hook", strays._watch["strays"] is None and IDENTIFIER not in state["hooks"])

strays.watch([("Crankus", "OakSpawner_1", 100.0)], clock, HOOK, IDENTIFIER)
check("one asked: its own hook on the animation update, said", state["hooks"][IDENTIFIER].enabled
      and notes("strays_watched")[-1] == {"event": "strays_watched", "companions": ["Crankus"], "looked": 1})
beat(clock, 100.1)
check("not born yet: looked for again", spawners() == ["OakSpawner_1"] and IDENTIFIER in state["hooks"])
stray = game.companion(1, (300.0, 0.0, 0.0), CRANKUS)
beat(clock, 100.2)
check("born of its spawner: taken out of the world, said, the hook removed", stray.destroyed
      and f"remove {CRANKUS}_1 False" in fake.calls and notes("stray_removed")[-1] == {
          "event": "stray_removed", "companion": "Crankus", "spawner": "OakSpawner_1", "removed": "removed"}
      and IDENTIFIER not in state["hooks"])

other = game.companion(2, (300.0, 0.0, 0.0), CRANKUS)
clock.now = 200.0
strays.watch([("Abomination", "OakSpawner_2", 200.0), ("Nobody", "OakSpawner_3", 200.0)], clock, HOOK, IDENTIFIER)
beat(clock, 200.1)
check("another companion's character born of that spawner: not taken", not other.destroyed)
check("an unknown companion: given up at once, said", notes("stray_lost")[-1] == {
      "event": "stray_lost", "companion": "Nobody", "spawner": "OakSpawner_3", "why": "not_found"})
beat(clock, 260.0)
check("a minute without a beat (the window holding the pause, a map loading): not counted, still looked for",
      spawners() == ["OakSpawner_2"])
play(clock, 260.0 + respawn.FIND_S - 1.0)
check("never born: still looked for before FIND_S of play", spawners() == ["OakSpawner_2"])
play(clock, 260.0 + respawn.FIND_S + 1.0)
check("then given up, said, the hook removed", notes("stray_lost")[-1]["companion"] == "Abomination"
      and IDENTIFIER not in state["hooks"])

clock.now = 300.0
strays.watch([("Crankus", "OakSpawner_60", 300.0), ("Crankus", "OakSpawner_61", 300.0)], clock, HOOK, IDENTIFIER)
strays.forget("OakSpawner_60")
reused = game.companion(60, (300.0, 0.0, 0.0), CRANKUS)
beat(clock, 300.1)
check("a spawner a team asks again: watched no more, the companion it bears that team's", not reused.destroyed
      and spawners() == ["OakSpawner_61"])
strays.forget("OakSpawner_61")
beat(clock, 300.2)
check("none left to look for: the hook removed", IDENTIFIER not in state["hooks"])
strays.forget("OakSpawner_99")

clock.now = 400.0
strays.watch([("Crankus", f"OakSpawner_{index}", 400.0) for index in range(10, 30)], clock, HOOK, IDENTIFIER)
check("MOST at most, the oldest dropped", spawners() == [f"OakSpawner_{index}" for index in range(14, 30)])
strays.watch([("Crankus", "OakSpawner_40", 400.0)], clock, HOOK, IDENTIFIER)
check("a second team's stop: the same watch, one hook", len(spawners()) == strays.MOST
      and spawners()[-1] == "OakSpawner_40")
real_characters = strays.fight.characters


def broken(_pc: object) -> list:
    raise RuntimeError("no world")


strays.fight.characters = broken
beat(clock, 400.1)
beat(clock, 400.2)
check("the world not read: said once, nothing taken", sum("could not be looked for" in text
      for text in state["errors"]) == 1 and len(spawners()) == strays.MOST)
play(clock, 400.2 + respawn.FIND_S + 1.0)
check("those looked for still given up in time, the hook removed", spawners() == []
      and IDENTIFIER not in state["hooks"])
strays.fight.characters = real_characters

clock.now = 500.0
strays.watch([("Crankus", "OakSpawner_50", 500.0)], clock, HOOK, IDENTIFIER)
beat(clock, 500.1)
late = game.companion(50, (300.0, 0.0, 0.0), CRANKUS)
clock.now = 500.2
worker = threading.Thread(target=state["hooks"][IDENTIFIER].fn)
worker.start()
worker.join(5)
check("a beat on another thread than the game's: nothing taken", not late.destroyed)
beat(clock, 500.3)
check("the next beat on the game's thread: taken", late.destroyed)
strays.reset_for_tests()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
