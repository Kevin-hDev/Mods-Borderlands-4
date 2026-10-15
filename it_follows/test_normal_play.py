"""Tests one game played at the level (normal/play.py): at its start the damage taken raised and said, the dodges'
look hooked, the camps grown at once, the census the second after, never in the camps' second; each second what is
due only, the camps and the census every 5 s a second apart, the watched enemies following the census; the damage
taken kept, each change said once; a second that holds the game said; a status line every 30 s; the player gone,
nothing done; the end gives everything back in one line, the zones with it; the long chase at every level, Predator's
at 600 m. The Hardcore: the dead counted, a step said, its factor given at once to the enemies and the damage taken
on top of the level's, once only, again when it is switched off; its state in the status line, its kills written at
the end, its factor at the start. The pieces it drives are set by the test after it is made; test_normal_mode.py runs
it whole."""

import json
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import frame, report  # noqa: E402
from it_follows.normal import dodge_speed, hardcore, levels, options, play as play_module  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes() -> list[dict]:
    lines = [json.loads(text.split(" ", 2)[2]) for text in state["info"] if text.startswith(report.PREFIX + " {")]
    state["info"].clear()
    return lines


class Due:
    """A piece done every period: when it was done, and what it answers."""

    def __init__(self, period: float, answer: dict) -> None:
        self.period, self.answer, self.at = period, answer, -1e9
        self.done: list[float] = []

    def due(self, now: float) -> bool:
        return now - self.at >= self.period

    def _do(self, now: float) -> dict:
        self.at = now
        self.done.append(now)
        return dict(self.answer)


class Camps(Due):
    held = {"OakSpawner_A": (None, {"NumTotalActors": ("04", "06")}), "OakSpawner_B": (None, None)}

    def grow(self, here: tuple | None, now: float) -> dict:
        return self._do(now)

    def put_back(self) -> dict:
        return {"given": 1}


class Enemies(Due):
    met = {"Char_A": None}

    def look(self, player: object, now: float) -> dict:
        return self._do(now)

    def nearest(self, here: tuple | None) -> dict:
        return {"Char_A": lambda: None}

    def harden(self, hard: float) -> dict:
        self.hardened.append(hard)
        return {"reached": 1}

    def end(self) -> dict:
        return {"enemies": 1}


class Taken:
    def __init__(self) -> None:
        self.answers: list = []
        self.changes: list = []

    def start(self, player: object) -> dict:
        return {"base": [1.0, 1.1]}

    def keep(self, player: object) -> dict | None:
        return self.answers.pop(0) if self.answers else None

    def put_back(self, player: object) -> str:
        return "restored" if player is not None else "unavailable"

    def change(self, player: object, factor: float) -> dict:
        self.changes.append(round(factor, 4))
        return {"base": [1.0, round(factor, 4)]}


clock = {"now": 100.0}
frame.now = lambda: clock["now"]

try:
    failures: list[str] = []
    hunter = types.SimpleNamespace(freed=False, K2_GetActorLocation=lambda: sdk_stubs.vector(0.0, 0.0))
    dodges = types.SimpleNamespace(files={"DodgeData_Human": None})
    game = play_module.Play(options.Settings(levels.LEVELS["Bandit"], False), hunter, dodges, failures.append)
    game.camps = Camps(5.0, {"grown": 1, "refused": 0, "too_many": 0, "stopped": "complete"})
    game.enemies = Enemies(5.0, {"met": 2})
    game.enemies.hardened = []
    game.taken = Taken()
    notes()  # the mod's own lines at its import
    game.begin(100.0)
    check("its start: the damage taken raised and said, the camps grown at once, the census not in their second",
          [line["event"] for line in notes()] == ["normal_taken_raised", "normal_camps"]
          and game.camps.done == [100.0] and game.enemies.done == [])
    game.tick(101.0)
    check("the census the second after", [line["event"] for line in notes()] == ["normal_enemies"]
          and game.enemies.done == [101.0])
    check("the dodges looked at each image, following the census", dodge_speed.IDENTIFIER in state["hooks"]
          and list(game.watch.watched) == ["Char_A"])
    game.taken.answers = [{"taken": "again", "game_base": 1.0}, {"taken": "again", "game_base": 1.0}]
    game.tick(102.0)
    game.tick(103.0)
    check("each second only what is due; the damage taken kept, a change said once",
          game.camps.done == [100.0] and game.enemies.done == [101.0]
          and [line["event"] for line in notes()] == ["normal_taken_kept"])
    game.camps.answer = {"grown": 0, "refused": 0, "too_many": 0, "stopped": "time_limit"}
    game.enemies.answer = {}
    game.tick(105.0)
    game.tick(106.0)
    check("every 5 s the camps and the census, a second apart; nothing said when nothing changed",
          game.camps.done == [100.0, 105.0] and game.enemies.done == [101.0, 106.0] and notes() == [])

    def slow_keep(player: object) -> None:
        clock["now"] += 0.6

    game.taken.keep = slow_keep
    game.tick(107.0)
    check("a second that holds the game said", [line["event"] for line in notes()] == ["normal_slow_second"])
    game.tick(130.0)
    status = [line for line in notes() if line["event"] == "normal_status"]
    check("a status line every 30 s", len(status) == 1 and status[0]["camps_grown"] == 1
          and status[0]["camps_held"] == 2 and status[0]["camps_stopped"] == "time_limit"
          and status[0]["families"] == 1 and status[0]["zones"] == 0 and status[0]["enemies"] == 1)
    game.tick(131.0)
    check("the next status 30 s later", [line for line in notes() if line["event"] == "normal_status"] == [])
    check("the Hardcore off: its state in the status line, no factor", status[0]["hardcore"] == "off"
          and status[0]["percent"] == 0 and game.hard == 1.0 and game.enemies.hardened == [])

    game.taken.keep = lambda player: None
    game.tick(135.0)
    check("the census due in the camps' second waits for the next", game.camps.done[-1] == 135.0
          and game.enemies.done[-1] == 131.0)
    notes()
    options.hardcore.value = True
    game.enemies.answer = {"met": 0, "lost": {"dead": 7}, "kills": 100}
    game.tick(136.0)
    lines = notes()
    check("the dead counted, a step said and written, the factor given at once",
          [line["event"] for line in lines] == ["normal_enemies", "hardcore_saved", "normal_hardcore_step",
                                                 "normal_hardcore"]
          and lines[2]["percent"] == 1 and lines[2]["kills"] == 100)
    check("on top of the level's: the enemies' factor, the damage taken 1.1 x 1.01",
          lines[3] == {"event": "normal_hardcore", "run": 0, "state": "on", "percent": 1, "factor": 1.01,
                       "enemies": {"reached": 1}, "taken": {"base": [1.0, 1.111]}}
          and game.enemies.hardened == [1.01] and game.taken.changes == [1.111])
    game.enemies.answer = {}
    game.tick(137.0)
    check("given once only", notes() == [] and game.enemies.hardened == [1.01])
    options.hardcore.value = False
    game.tick(138.0)
    lines = notes()
    check("switched off: the level's again, the kills kept", [line["event"] for line in lines] == ["normal_hardcore"]
          and lines[0]["state"] == "off" and lines[0]["factor"] == 1.0 and lines[0]["percent"] == 1
          and game.enemies.hardened == [1.01, 1.0] and game.taken.changes == [1.111, 1.1])
    options.hardcore.value = True
    started = play_module.Play(options.Settings(levels.LEVELS["Bandit"], False), hunter, dodges, failures.append)
    check("a game played with the Hardcore on starts with its factor", started.hard == 1.01
          and started.enemies.toughness.factor == 1.45 * 1.01 and started.taken.factor == 1.1 * 1.01)
    options.hardcore.value = False

    options.hardcore.value = True
    hardcore.count(30)
    game.taken.answers = []
    game.tick(160.0)
    check("the kills counted since the last write written with the status line", [
        line for line in notes() if line["event"] == "hardcore_saved"] == [
        {"event": "hardcore_saved", "run": 0, "why": "status", "kills": 130, "percent": 1}])
    hardcore.count(5)
    options.hardcore.value = False
    hunter.freed = True
    game.tick(140.0)
    check("the player gone: nothing done", game.camps.done == [100.0, 105.0, 130.0, 135.0, 160.0] and notes() == [])
    game.end("left_game")
    ended = notes()
    check("the Hardcore's kills counted since the last step written at the end, first",
          ended[0] == {"event": "hardcore_saved", "run": 0, "why": "end", "kills": 135, "percent": 1})
    ended = ended[1:]
    check("the end gives everything back in one line", [line["event"] for line in ended] == ["normal_given_back"]
          and ended[0]["reason"] == "left_game" and ended[0]["enemies"] == {"enemies": 1}
          and ended[0]["camps"] == {"given": 1} and ended[0]["zones"] == {} and ended[0]["taken"] == "unavailable"
          and ended[0]["hook"] == "removed" and dodge_speed.IDENTIFIER not in state["hooks"]
          and ended[0]["hardcore_saved"] is True and hardcore.option.value == {"version": 1, "kills": 135})
    hunter.freed = False
    check("the long chase at every level, 600 m at Predator", play_module.Play(
        options.Settings(levels.LEVELS["Predator"], False), hunter, dodges, failures.append).chase.target_cm
        == 60000.0)
    off = play_module.Play(options.Settings(levels.LEVELS["Bandit"], False, False), hunter, dodges, failures.append)
    off.camps = Camps(5.0, {"grown": 0, "refused": 0, "too_many": 0, "stopped": "complete"})
    off.enemies = Enemies(5.0, {})
    off.taken = Taken()
    off.begin(200.0)
    hooked = dodge_speed.IDENTIFIER in state["hooks"]
    off.end("stopped")
    check("the faster dodges switched off: no dodge looked at, nothing to give back",
          not hooked and [line for line in notes() if line["event"] == "normal_given_back"][-1]["hook"] == "inactive")
    check("nothing failed", failures == [])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
