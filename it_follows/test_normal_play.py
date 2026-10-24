"""Tests one game played at the level (normal/play.py): at its start the damage taken and the rewards raised and said,
the dodges' look hooked, the camps grown at once, the census the second after, never in the camps' second; each second
what is due only, the camps and the census every 5 s a second apart, the watched enemies following the census; the
damage taken kept, each change said once; a second that holds the game said; a status line every 30 s; the player gone,
nothing done; the end gives everything back in one line, the zones and the rewards with it; the long chase at every
level, Predator's at 600 m. The Hardcore: the dead counted, a step said, its factor given at once to the enemies and the
damage taken on top of the level's, once only, again when it is switched off; its state in the status line, its kills
written at the end, its factor at the start. Predator: the level's dodge and gesture factors, the armed bandits'
rest shortened at the census and said, given back at the end. What it costs in its status line, as a run's: the
images a second, its beat's calls, each task's longest, the looks at the dodges and where the player's kills lay; a
pass of the camps that stops at its time gives the rest to the next image, part by part, PARTS_MOST at most (audit
of 24 October 2026). The census in parts (trial 221): its kills counted and the guests told in its own image, its
line said once its parts are done; one whose parts the next census or the end cut said then, cut; a part left waiting
once the game played is over does nothing. The pieces it drives are set by the test after it is made;
test_normal_mode.py runs it whole."""

import json
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import frame, report  # noqa: E402
from it_follows.characters import animation_hook  # noqa: E402
from it_follows.normal import camps_grown, coop_guests, enemy_time, hardcore, levels, options  # noqa: E402
from it_follows.normal import play as play_module  # noqa: E402

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

    def grow(self, places: list, now: float, world: object = None) -> dict:
        self.places, self.world = places, world
        return self._do(now)

    def put_back(self) -> dict:
        return {"given": 1}


class Arrivals:
    """A census's parts (arrivals.py): done after one, or after left more parts each."""
    left = 0

    def __init__(self) -> None:
        self.parts = 0

    def pending(self) -> bool:
        return self.parts <= Arrivals.left

    def part(self) -> None:
        self.parts += 1


class Enemies(Due):
    met = {"Char_A": None}
    shields = types.SimpleNamespace(given={"Char_A": None})
    aim = types.SimpleNamespace(held={"Char_A.Gun": None, "Char_A.Pistol": None})
    kept: list[dict] = []
    scan_ms = 9.5
    reserve = types.SimpleNamespace(said=lambda: {"in_world": 2, "out_met": 0, "out_unmet": 1, "unread": 0})

    def keep_shields(self, now: float) -> dict:
        return self.kept.pop(0) if self.kept else {}

    def look(self, player: object, now: float) -> dict:
        self.arrivals = Arrivals()
        return self._do(now)

    def arrived(self, found: dict) -> dict:
        """What the census's image found, said as is: this one meets no one."""
        return dict(found)

    def nearest(self, places: list, within_m: float = 60.0, most: int = 48) -> dict:
        self.__dict__.setdefault("calls", []).append((places, within_m))
        self.places = places
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


class Guests:
    """One guest, found at the start, 5 m from the hunter."""
    held = {"Guest": None}

    def due(self, now: float) -> bool:
        return now == 100.0

    def look(self, player: object, now: float) -> dict:
        return {"raised": {"Guest": {"taken": {}}}, "gone": {}, "held": 1}

    def places(self) -> list:
        return [(500.0, 0.0, 0.0)]

    def keep(self) -> dict:
        return {}

    def heard(self, percents: list) -> dict:
        return {"Guest": {"percent": percents[0][1]}} if percents else {}

    def kills(self, by_others: dict) -> dict:
        return dict(by_others)

    def end(self) -> dict:
        return {"Guest": {"taken": "restored", "gains": "taken_back"}}


class Rewards:
    def start(self, player: object) -> dict:
        return {"shares": {"xp": 0.1}}

    def put_back(self, player: object) -> str:
        return "gone" if player is None else "taken_back"


clock = {"now": 100.0}
frame.now = lambda: clock["now"]


def beat() -> frame.Beat:
    """The mode's beat as play.py sees it: tasks put off, its calls counted; never hooked here."""
    return frame.Beat(lambda now: None, lambda reason: None, "test:normal")


def parts(played: object, at: float, most: int = 10) -> int:
    """The census's parts the beat holds, run one an image as the beat does, most at most: how many ran."""
    ran = 0
    while "census" in played.beat.later and ran < most:
        played.beat.later.pop("census")(at + ran / 100.0)
        ran += 1
    return ran


try:
    failures: list[str] = []
    hunter = types.SimpleNamespace(freed=False, K2_GetActorLocation=lambda: sdk_stubs.vector(0.0, 0.0))
    dodges = types.SimpleNamespace(files={"DodgeData_Human": None})
    game = play_module.Play(options.Settings(levels.LEVELS["Bandit"], False), hunter, dodges, failures.append, beat())
    game.camps = Camps(5.0, {"grown": 1, "refused": 0, "too_many": 0, "stopped": "complete", "search": "actors"})
    game.enemies = Enemies(5.0, {"met": 2, "by_others": {"Guest": 2}})
    game.enemies.hardened = []
    game.enemies.calls = []
    game.taken = Taken()
    game.rewards = Rewards()
    game.guests = Guests()
    notes()  # the mod's own lines at its import
    game.begin(100.0)
    started = notes()
    check("its start: the damage taken and the rewards raised and said, the camps grown at once, the census not in "
          "their second", [line["event"] for line in started]
          == ["normal_taken_raised", "normal_rewards_raised", "normal_guests", "normal_camps"]
          and started[1]["shares"] == {"xp": 0.1}
          and game.camps.done == [100.0] and game.enemies.done == [] and started[3]["part"] == 0
          and game.camps.world is hunter)
    game.tick(101.0)
    check("the census the second after, each guest told its kills in its image, its line once its parts are done",
          [(line["event"], line.get("told")) for line in notes()] == [("normal_guest_kills", {"Guest": 2})]
          and game.enemies.done == [101.0] and list(game.beat.later) == ["census"])
    check("one part, then the census's line, with its parts", parts(game, 101.02) == 1
          and [(line["event"], line.get("parts"), line.get("met")) for line in notes()] == [("normal_enemies", 1, 2)])
    check("co-op: the camps grown and the gestures watched around each player, the guest's place after the hunter's",
          len(game.camps.places) == len(game.enemies.places) == 2 and game.camps.places[1] == (500.0, 0.0, 0.0)
          and game.enemies.places[1] == (500.0, 0.0, 0.0))
    game.link.pending = [(lambda: "GuestPC", 4)]
    game.tick(101.5)
    check("co-op: each guest's percent heard, given and said", [(line["event"], line.get("Guest"))
                                                                for line in notes()]
          == [("normal_guest_hardcore", {"percent": 4})] and game.link.pending == [])
    check("co-op: the enemies near a guest have their dodges left to the game",
          ([(500.0, 0.0, 0.0)], coop_guests.PLAIN_M) in game.enemies.calls and game.watch.plain == {"Char_A"})
    check("the dodges looked at each image, following the census", enemy_time.IDENTIFIER in animation_hook.beats()
          and list(game.watch.watched) == ["Char_A"])
    game.taken.answers = [{"taken": "again", "game_base": 1.0}, {"taken": "again", "game_base": 1.0}]
    game.tick(102.0)
    game.tick(103.0)
    check("each second only what is due; the damage taken kept, a change said once",
          game.camps.done == [100.0] and game.enemies.done == [101.0]
          and [line["event"] for line in notes()] == ["normal_taken_kept"])
    game.camps.answer = {"grown": 0, "refused": 0, "too_many": 0, "stopped": "time_limit", "search": "actors"}
    game.enemies.answer = {}
    game.tick(105.0)
    check("a camps' pass stopped at its time leaves the rest to the next image", list(game.beat.later) == ["camps"])
    game.beat.later.pop("camps")(105.02)
    check("the next part, searched again, and the rest left again", game.camps.done == [100.0, 105.0, 105.02]
          and list(game.beat.later) == ["camps"])
    for moment in range(camps_grown.PARTS_MOST):
        if "camps" in game.beat.later:
            game.beat.later.pop("camps")(105.04 + moment / 100.0)
    check("PARTS_MOST parts at most, the rest at the next pass", len(game.camps.done) == 1 + camps_grown.PARTS_MOST
          and game.beat.later == {})
    game.camps.done = [100.0, 105.0]
    game.camps.at = 105.0
    game.tick(106.0)
    parts(game, 106.02)
    check("every 5 s the camps and the census, a second apart; nothing said when nothing changed",
          game.camps.done == [100.0, 105.0] and game.enemies.done == [101.0, 106.0] and notes() == [])
    game.enemies.kept = [{"refilled": 1}]
    game.tick(106.5)
    check("each second Predator's shields kept, what happened said", [(line["event"], line.get("refilled"))
                                                                      for line in notes()]
          == [("normal_shields", 1)])

    def slow_keep(player: object) -> None:
        clock["now"] += 0.6

    game.taken.keep = slow_keep
    game.tick(107.0)
    check("a second that holds the game said", [line["event"] for line in notes()] == ["normal_slow_second"])
    game.tick(130.0)
    status = [line for line in notes() if line["event"] == "normal_status"]
    check("a status line every 30 s", len(status) == 1 and status[0]["camps_grown"] == 1
          and status[0]["camps_held"] == 2 and status[0]["camps_stopped"] == "time_limit"
          and status[0]["families"] == 1 and status[0]["zones"] == 0 and status[0]["enemies"] == 1
          and status[0]["shields"] == 1 and status[0]["aimed"] == 2)
    check("what it costs in the line, as a run's: images a second, its beat's calls, each task, the census's search,"
          " the looks at the dodges, where the player's kills lay",
          {"fps", "fps_low", "hook_calls_s", "hook_idle_us", "slowest_ms"} <= set(status[0])
          and set(status[0]["tasks_ms"]) == {"camps", "census", "census_search", "census_part", "melee_rest",
                                             "staggers"}
          and status[0]["tasks_ms"]["census_search"] == 9.5 and set(status[0]["watch"]) == {
              "looks_s", "look_us", "look_longest_ms", "dodge_reads_s", "dodge_read_us", "gesture_reads_s",
              "gesture_read_us"}
          and status[0]["kills_seen"]["out_unmet"] == 1 and status[0]["slowest_ms"] >= 600.0)
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
    check("the dead counted in the census's own image, before its parts: a step said and written, the factor given "
          "at once", [line["event"] for line in lines] == ["hardcore_saved", "normal_hardcore_step", "normal_hardcore"]
          and lines[1]["percent"] == 1 and lines[1]["kills"] == 100 and "census" in game.beat.later)
    check("on top of the level's: the enemies' factor, the damage taken 1.1 x 1.01",
          lines[2] == {"event": "normal_hardcore", "run": 0, "state": "on", "percent": 1, "factor": 1.01,
                       "enemies": {"reached": 1}, "taken": {"base": [1.0, 1.111]}}
          and game.enemies.hardened == [1.01] and game.taken.changes == [1.111])
    parts(game, 136.02)
    check("then the census's line, its kills with it", [(line["event"], line.get("kills")) for line in notes()]
          == [("normal_enemies", 100)])
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
    started = play_module.Play(options.Settings(levels.LEVELS["Bandit"], False), hunter, dodges, failures.append,
                               beat())
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
          and ended[0]["rewards"] == "gone" and ended[0]["guests"]["Guest"]["taken"] == "restored"
          and ended[0]["link"] == "removed"
          and ended[0]["hook"] == "removed" and enemy_time.IDENTIFIER not in animation_hook.beats()
          and ended[0]["hardcore_saved"] is True and hardcore.option.value == {"version": 1, "kills": 135})
    hunter.freed = False
    check("the long chase at every level, 600 m at Predator", play_module.Play(
        options.Settings(levels.LEVELS["Predator"], False), hunter, dodges, failures.append, beat()).chase.target_cm
        == 60000.0)
    off = play_module.Play(options.Settings(levels.LEVELS["Bandit"], False, False), hunter, dodges, failures.append,
                           beat())
    off.camps = Camps(5.0, {"grown": 0, "refused": 0, "too_many": 0, "stopped": "time_limit", "search": "actors"})
    off.enemies = Enemies(5.0, {})
    off.taken = Taken()
    off.rewards = Rewards()
    off.begin(200.0)
    hooked = enemy_time.IDENTIFIER in animation_hook.beats()
    off.end("stopped")
    waiting, grown_before = off.beat.later.pop("camps", None), list(off.camps.done)
    if waiting is not None:
        waiting(200.05)
    check("a camps' part left waiting once the game played is over grows nothing: its camps were given back",
          waiting is not None and off.camps.done == grown_before == [200.0])
    check("the faster dodges switched off: the gestures still looked at, at the level's factor, no dodge",
          hooked and off.watch.factors == {"dodge": None, "gesture": 1.1}
          and [line for line in notes() if line["event"] == "normal_given_back"][-1]["hook"] == "removed")

    class Melee:
        def keep(self) -> dict:
            return {"written": 7}

        def put_back(self) -> dict:
            return {"given_back": 7}

    class Staggers:
        def keep(self) -> dict:
            return {"written": ["HitReactionSettings"]}

        def put_back(self) -> dict:
            return {"HitReactionSettings": "given_back"}

    chosen = levels.LEVELS["Predator"]
    predator = play_module.Play(options.Settings(chosen, False), hunter, dodges, failures.append, beat())
    check("the faster dodges on: the level's dodge and gesture factors, its rest",
          predator.watch.factors == {"dodge": chosen.dodge_speed, "gesture": chosen.gestures}
          and predator.melee.rest == chosen.melee_rest and predator.staggers.factor == chosen.staggers)
    predator.camps = Camps(5.0, {"grown": 0, "refused": 0, "too_many": 0, "stopped": "complete",
                                 "search": "actors"})
    predator.enemies = Enemies(5.0, {})
    predator.taken = Taken()
    predator.rewards = Rewards()
    predator.melee = Melee()
    predator.staggers = Staggers()
    predator.begin(300.0)
    check("its start makes the staggers rarer, said", [line["event"] for line in notes()].count("normal_staggers")
          == 1)
    predator.tick(301.0)
    said = notes()
    check("the census shortens the armed bandits' rest, said", [line.get("written") for line in said
                                                                if line["event"] == "normal_melee_rest"] == [7])
    check("the census keeps the staggers rarer, said", [line.get("written") for line in said
                                                        if line["event"] == "normal_staggers"]
          == [["HitReactionSettings"]])
    predator.end("stopped")
    ended = [line for line in notes() if line["event"] == "normal_given_back"][-1]
    check("the end gives the rest and the staggers back", ended["melee_rest"] == {"given_back": 7}
          and ended["staggers"] == {"HitReactionSettings": "given_back"})

    slow = play_module.Play(options.Settings(levels.LEVELS["Bandit"], False), hunter, dodges, failures.append, beat())
    slow.camps = Camps(5.0, {"grown": 0, "refused": 0, "too_many": 0, "stopped": "complete", "search": "actors"})
    slow.enemies = Enemies(5.0, {"met": 1, "lost": {}})
    slow.taken, slow.rewards = Taken(), Rewards()
    Arrivals.left = 5
    slow.begin(400.0)
    slow.camps.period = 1e9
    slow.tick(401.0)
    ran = parts(slow, 401.02, most=2)
    notes()
    slow.tick(406.0)
    said = [(line.get("cut"), line.get("parts")) for line in notes() if line["event"] == "normal_enemies"]
    check("a census whose parts are not done when the next comes: its line said then, cut, with the parts it took",
          ran == 2 and said == [("census", 2)] and "census" in slow.beat.later)
    parts(slow, 406.02, most=1)
    slow.end("stopped")
    ended = [(line["event"], line.get("cut"), line.get("parts")) for line in notes()]
    check("the end says the census still in parts, cut, before giving everything back",
          ("normal_enemies", "end", 1) in ended and ended[-1][0] == "normal_given_back")
    waiting = slow.beat.later.pop("census", None)
    if waiting is not None:
        waiting(406.1)
    check("a part left waiting once the game played is over does nothing", waiting is not None
          and slow.enemies.arrivals.parts == 1 and notes() == [])
    Arrivals.left = 0
    check("nothing failed", failures == [])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
