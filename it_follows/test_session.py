"""Tests the session (session.py) with a fake run: a start refused with a run going, without a character, from a
vehicle, a pawn that cannot be read being no vehicle, and in a game of several players, each said as it is; a start of
an unknown number of players written down; the run made with the settings, the controller, the character and the camps
kept from one run to the next; a start the run refuses leaves no run; a start that raises gives back what it took and
says so, or says to quit to the main menu when the giving back raises too; a stop without a run; a stop puts the
run on top of the history, with the moment it began, and what the window shows of the run in progress. One mode at a
time (decision 80): the normal mode refused during a Horde run and in a game of several players, a Horde run refused
while the normal mode is on; the normal mode made with its settings and the session's stop, shown to the window with
its level and whether it plays, refused a second time, turned off with its reason, stopped by an error written off;
a start of it that raises ends it; the mod enabled turns it on again when its settings say so, the mod disabled turns
it off and keeps that choice."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import ending, kept, session  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class FakeRun:
    """A run as the session sees it: made with what start gives, began as told, ended and recorded."""

    made: list = []
    outcome, raises, end_raises = "started", None, None

    def __init__(self, settings: object, pc: object, player: object, pool: object, end: object) -> None:
        self.given, self.ended = (settings, pc, player, pool, end), []
        self.settings = types.SimpleNamespace(duration_s=600.0)
        self.level = types.SimpleNamespace(target=40)
        self.clock, self.stats = types.SimpleNamespace(played=61.7), types.SimpleNamespace(kills=12, deaths=1)
        FakeRun.made.append(self)

    def begin(self, now: float) -> str:
        if FakeRun.raises is not None:
            raise FakeRun.raises
        return FakeRun.outcome

    def end(self, reason: str) -> None:
        self.ended.append(reason)
        if FakeRun.end_raises is not None:
            raise FakeRun.end_raises


def players(count: int | None) -> None:
    """The game holds count players; None: the number cannot be read."""
    world = types.SimpleNamespace(GameState=types.SimpleNamespace(PlayerArray=[object()] * count)) if count else None
    sys.modules["mods_base"].ENGINE = types.SimpleNamespace(GameViewport=types.SimpleNamespace(World=world))


class FakeMode:
    """The normal mode as the session sees it: made with its settings and stop, begun, playing or waiting, ended."""

    made: list = []
    raises = None

    def __init__(self, settings: object, fail: object) -> None:
        self.given, self.ended, self.playing_now = (settings, fail), [], True
        self.settings = settings
        FakeMode.made.append(self)

    def begin(self, now: float) -> str:
        if FakeMode.raises is not None:
            raise FakeMode.raises
        return "playing"

    def playing(self) -> bool:
        return self.playing_now

    def end(self, reason: str) -> None:
        self.ended.append(reason)


normal = types.SimpleNamespace(level=types.SimpleNamespace(name="Senior"), allies=False)


def said() -> str:
    return state["info"][-1]


session.Run = FakeRun
pc, hunter = types.SimpleNamespace(OakCharacter=None), object()
state["pc"] = pc
players(1)

try:
    pc.OakCharacter = None
    check("no character, no pawn: refused, said to load a game", session.start("settings") == "no_character"
          and said() == "[It Follows] No run: load a game first." and FakeRun.made == [])
    pc.Pawn = types.SimpleNamespace(Class=types.SimpleNamespace(Name="BPVeh_OakVehicle_C"))
    check("no character, a vehicle's pawn: refused, said to get out of it", session.start("settings") == "in_vehicle"
          and said() == "[It Follows] No run from a vehicle: get out of it, then press Start." and FakeRun.made == [])
    pc.Pawn = types.SimpleNamespace(Class=types.SimpleNamespace(Name="OakCharacter_Menu"))
    check("a pawn that is no vehicle: no game to run in", session.start("settings") == "no_character")
    pc.Pawn = types.SimpleNamespace()
    check("a pawn whose class cannot be read is no vehicle", session.start("settings") == "no_character")
    del pc.Pawn
    pc.OakCharacter = hunter

    players(2)
    check("two players: refused, said, nothing made", session.start("settings") == "coop"
          and said().endswith("only works in solo games for now. Your game is not changed.") and FakeRun.made == [])
    players(None)
    check("players that cannot be counted: the run starts, written down",
          session.start("settings") == "started" and session.running() and "players_unknown" in state["info"][-1])
    first = FakeRun.made[-1]
    check("the run made with the settings, the controller, the character, the camps and the session's stop",
          first.given[:3] == ("settings", pc, hunter) and first.given[3] is session._state["pool"]
          and first.given[4] == session.stop)
    players(1)
    check("a run going: refused", session.start("settings") == "already_running" and len(FakeRun.made) == 1)
    check("the window shows the run in progress: its level, limit, time played and counts",
          session.live() == session.Live(40, 600.0, 61.7, 12, 1))
    began = session._state["began"]
    check("Stop ends it with its reason", session.stop("stopped") == "stopped" and first.ended == ["stopped"]
          and not session.running() and session.live() is None)
    check("the run stopped on top of the history, with the moment it began, its result waiting",
          kept.runs()[0] == ending.waiting() and kept.runs()[0].when == began > 0
          and (kept.runs()[0].level, kept.runs()[0].limit_s, kept.runs()[0].played_s, kept.runs()[0].kills,
               kept.runs()[0].deaths, kept.runs()[0].end) == (40, 600, 61, 12, 1, "stopped"))
    check("a stop without a run does nothing", session.stop() == "not_running")
    pool = session._state["pool"]
    session.start("settings")
    session.stop()
    check("the camps are kept from one run to the next", session._state["pool"] is pool)

    FakeRun.outcome = "no_camp"
    check("a start the run refuses leaves no run", session.start("settings") == "no_camp" and not session.running())
    FakeRun.outcome = "started"

    FakeRun.raises = RuntimeError("census")
    outcome = session.start("settings")
    check("a start that raises: what it took given back, written down, said, no run left",
          outcome == "start_failed" and not session.running() and FakeRun.made[-1].ended == ["start_failed"]
          and '"event":"start_failed"' in state["info"][-2] and '"error":"RuntimeError"' in state["info"][-2]
          and said() == "[It Follows] The run could not start. What it had changed was given back. The reason is in "
                        "unrealsdk.log.")
    FakeRun.end_raises = ValueError("end")
    outcome = session.start("settings")
    check("the giving back raising too: written down, said to quit to the main menu, no run left",
          outcome == "start_failed" and not session.running() and '"event":"stop_failed"' in state["info"][-2]
          and '"error":"ValueError"' in state["info"][-2]
          and said() == "[It Follows] The run could not start, and what it changed could not all be given back. "
                        "Quit to the main menu and load your game again. The reason is in unrealsdk.log.")
    FakeRun.raises = FakeRun.end_raises = None
    check("a start works again after", session.start("settings") == "started" and session.running())

    session.normal_mode.Mode = FakeMode
    check("a Horde run going: the normal mode refused, nothing made", session.start_normal(normal) == "horde_running"
          and FakeMode.made == [] and not session.normal_on())
    session.stop()
    runs_made = len(FakeRun.made)
    players(2)
    check("two players: the normal mode refused, said, nothing made", session.start_normal(normal) == "coop"
          and said().endswith("only works in solo games for now. Your game is not changed.") and FakeMode.made == [])
    players(1)
    check("turned on: the mode made with its settings and the session's stop, playing",
          session.start_normal(normal) == "playing" and session.normal_on()
          and FakeMode.made[-1].given == (normal, session.stop_normal))
    check("the window shows its level and whether it plays",
          session.normal_live() == session.NormalLive("Senior", True))
    FakeMode.made[-1].playing_now = False
    check("waiting for a game, said so to the window", session.normal_live() == session.NormalLive("Senior", False))
    check("on: a second start refused", session.start_normal(normal) == "already_on" and len(FakeMode.made) == 1)
    check("on: a Horde run refused, nothing made", session.start("settings") == "normal_on"
          and not session.running() and len(FakeRun.made) == runs_made)
    check("STOP turns it off with its reason", session.stop_normal("stopped") == "stopped"
          and FakeMode.made[-1].ended == ["stopped"] and not session.normal_on() and session.normal_live() is None)
    check("off: a stop does nothing", session.stop_normal() == "not_on")
    session.start_normal(normal)
    import it_follows  # noqa: E402
    from it_follows.normal import options as normal_options  # noqa: E402

    normal_options.on.value = True
    written: list = []
    saving, it_follows.mod.save_settings = it_follows.mod.save_settings, lambda: written.append(normal_options.on.value)
    state["info"].clear()
    check("stopped by an error: ended, its choice to be on written off and saved, then said to the player",
          session.stop_normal("dodge_error:TypeError") == "stopped"
          and FakeMode.made[-1].ended == ["dodge_error:TypeError"] and normal_options.on.value is False
          and written == [False] and len(state["info"]) == 2
          and '"event":"normal_off_written"' in state["info"][0] and '"saved":true' in state["info"][0]
          and "stopped after an error" in state["info"][1])
    session.start_normal(normal)
    normal_options.on.value = True
    check("STOP or the mod disabled never write it off: only an error does",
          session.stop_normal("mod_disabled") == "stopped" and normal_options.on.value is True)
    session.start_normal(normal)
    it_follows.mod.save_settings = lambda: (_ for _ in ()).throw(OSError("locked"))
    state["info"].clear()
    check("a write that fails is said with its reason, the mode stopped all the same",
          session.stop_normal("error:ValueError") == "stopped" and not session.normal_on()
          and '"saved":"failed:OSError"' in state["info"][0])
    it_follows.mod.save_settings = saving
    normal_options.on.value = False
    FakeMode.raises = RuntimeError("begin")
    check("a start that raises: written down, the mode ended, nothing left on",
          session.start_normal(normal) == "start_failed" and FakeMode.made[-1].ended == ["start_failed"]
          and not session.normal_on() and '"event":"normal_start_failed"' in state["info"][-1])
    FakeMode.raises = None
    check("off again: a Horde run starts", session.start("settings") == "started")
    session.stop()

    it_follows._on_enable()
    check("the mod enabled with the normal mode off: nothing turned on", not session.normal_on())
    normal_options.on.value = True
    it_follows._on_enable()
    check("the mod enabled with the normal mode on in its settings: turned on again, written down",
          session.normal_on() and FakeMode.made[-1].settings.level.name == "Bandit"
          and '"event":"normal_resumed"' in state["info"][-1] and '"outcome":"playing"' in state["info"][-1])
    it_follows._on_disable()
    check("the mod disabled: the mode off, its choice to be on kept for the next enabling",
          not session.normal_on() and FakeMode.made[-1].ended == ["mod_disabled"] and normal_options.on.value is True)
    FakeMode.raises = RuntimeError("begin")
    it_follows._on_enable()
    FakeMode.raises = None
    check("review: turned on again at the enabling, its start raising: the choice to be on off, saved by mods_base "
          "after on_enable, not tried again at the next launch",
          not session.normal_on() and '"outcome":"start_failed"' in state["info"][-1]
          and normal_options.on.value is False)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
