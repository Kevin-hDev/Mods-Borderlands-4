"""Tests whole runs of It Follows in a fake game (game_fixture.py), every piece of the mod as it is, none replaced by a
fake (trial 8c lost a run to a fake piece that hid its frontier): a start refused with no character, from a vehicle, in
coop, or with a run already going; a start that raises, what it took given back and said, even when the giving back
raises too; the killed coming back as a kind of the place, and the status line's copies, room, kinds, where the horde
stood and how many floated (decisions 56, 57, 68 and 72); a run started with Kevin's settings read as the window reads
them: the
enemies around read, the camp whose zone is lent made, a copy of each enemy near born of a camp of the mod, the game
camps placed on the hunter, the zone put on him and widened, each enemy lent it, the hunter imposed, the far ones
walked, made faster and put in one team, the bar shown; each second the bar written; the copies drawn at the census; a
kill of the horde counted, born again of a camp of the mod and drawn again; a kill of an enemy never drawn counted by
the census; the hunter's death counted, the run going on; the hunter in a vehicle, the bar still kept; a jump written
down; at Stop everything given back, the run on top of the history, its result waiting for the window; a time limit,
its result waiting too; the player leaving the game, kept in the history with no result; a run without the bar; a
zone the game keeps moving away; a run with Buff+, the enemies drawn holding more health and the hunter taking more
damage, both given back at the stop (decision 79); the Horde's Hardcore, from 0 % at each start, a step at 100 kills
raising the enemies that join next and the hunter's damage taken on top of the Buff, said in the bar, the status
line and the stop (decision 109); the mod disabled; the camps kept for the next run."""

import json
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import game_fixture  # noqa: E402
import health_fixture  # noqa: E402

game = game_fixture.Game(state)

import it_follows  # noqa: E402
from it_follows import census, copies, frame, game_camps, options, recruit, report  # noqa: E402
from it_follows.characters import animation_hook, brain_walk, camps  # noqa: E402
from it_follows import ending, kept, levels, texts  # noqa: E402
from it_follows import run as run_module  # noqa: E402
from it_follows import session  # noqa: E402

clock = [1000.0]
ticking = types.SimpleNamespace(monotonic=lambda: clock[0])
frame.time = camps.time = copies.time = census.time = recruit.time = ticking
brain_walk.process_event = lambda: game.process_event
camps.FGbxDefPtr = game_fixture.DefPtr
# The engine's image count, 60 images each second of play.
drawn_images = [500]
state["classes"]["KismetSystemLibrary"].ClassDefaultObject.GetFrameCount = lambda: drawn_images[0]
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def lines() -> list[dict]:
    prefix = report.PREFIX + " {"
    return [json.loads(line[len(report.PREFIX) + 1:]) for line in state["info"] if line.startswith(prefix)]


def last(event: str) -> dict:
    found = [line for line in lines() if line["event"] == event]
    return found[-1] if found else {}


def second(steps: int = 1, paused: bool = False) -> None:
    """steps seconds of play: the clocks move on, the world's own unless paused, the animation update calls the run's
    beat each second, and the images after it run the work it put off (frame.Beat.defer), the clock set back to the
    second after them."""
    for _ in range(steps):
        clock[0] += 1.0
        drawn_images[0] += 60
        game.world_clock[0] += 0.0 if paused else 1.0
        at = clock[0]
        for image in range(4):
            clock[0] = at + image * (frame.LATER_MOST_S + 0.001)
            hooked = animation_hook.beats().get(frame.IDENTIFIER)
            if hooked is not None:
                hooked(None, None, None, None)
        clock[0] = at


def words() -> str:
    shown = game.screen.shown()
    return shown[-1].WidgetTree.RootWidget.slots[0].child.content.text if shown else ""


def settings(**changed: object) -> options.Settings:
    chosen = {"level": 40, "speed": 1.2, "duration_s": None, "respawn": True, "language": texts.FRENCH, "bar": True,
              "bar_points": 19.0}
    chosen.update(changed)
    return options.Settings(**chosen)


hunter = game.hunter
camp_a, camp_b, camp_c = (game.zone(3000.0, "OakSpawner_Camp_A"), game.zone(6500.0, "OakSpawner_Camp_B"),
                          game.zone(12500.0, "OakSpawner_Camp_C"))
psycho = game.enemy("Char_PsychoBasic_Male_1", 2000.0, "Char_PsychoBasic_Male", camp_a)
cat = game.enemy("Char_CatAdult_2", 6000.0, "Char_CatAdult", camp_b)
bat = game.enemy("Char_BatBasic_3", 12000.0, "Char_BatBasic", camp_c)
cat.team = game_fixture.ORDER
far_camp = game.zone(200000.0, "OakSpawner_Camp_Far").Outer
late_camps: list = []


class AllCamps:
    """The spawners the game holds, as find_all reads them: its own camps and those the mod made."""

    def __iter__(self):
        return iter([camp_a.Outer, camp_b.Outer, camp_c.Outer, far_camp, *late_camps, *game.spawners_made])


state["all"][game_camps.SPAWNER_CLASS] = AllCamps()

try:
    pc = state["pc"]
    pc.OakCharacter = None
    check("no character: the run is refused, said", session.start(settings()) == "no_character"
          and state["info"][-1] == "[It Follows] No run: load a game first." and not session.running())
    pc.Pawn = types.SimpleNamespace(Class=types.SimpleNamespace(Name="OakVehicle"))
    check("no character, the pawn a vehicle: refused with the true reason, nothing changed",
          session.start(settings()) == "in_vehicle"
          and state["info"][-1] == "[It Follows] No run from a vehicle: get out of it, then press Start."
          and not session.running() and not game.spawners_made)
    pc.Pawn = types.SimpleNamespace(Class=None)
    check("a pawn whose class cannot be read is no vehicle", session.start(settings()) == "no_character")
    del pc.Pawn
    pc.OakCharacter = hunter
    game.players.append(object())
    check("a game of two players: refused, said, nothing changed", session.start(settings()) == "coop"
          and state["info"][-1].endswith("only works in solo games for now. Your game is not changed.")
          and not game.spawners_made)
    game.players.pop()

    options.level.value, options.speed.value = "40", "+20%"
    check("the settings read as the window reads them start a run",
          session.start(options.read(texts.FRENCH)) == "started" and session.running())
    check("a second start while it runs is refused", session.start(settings()) == "already_running")
    started = last("started")
    check("the start reads the three enemies around and draws them", started["crowd"] == 3 and started["drawn"] == 3)
    made = last("copies")
    host_spawner = game.spawners_made[0]
    host_zone = next(zone for zone in game.zones if zone.Outer is host_spawner)
    check("the camp whose zone is lent made by the mod, and a copy of each enemy near born of a camp of the mod",
          made["made"] == "done" and made["near"] == 3 and made["handed"] == 3 and len(game.spawners_made) == 4
          and sum(spawner.SpawnerComponent.births for spawner in game.spawners_made) == 3)
    check("the lent zone put on the hunter and widened to 600 m", (host_zone.x, host_zone.y) == (0.0, 0.0)
          and host_zone.settings.CombatTerritory.Radius == 60000.0)
    check("each enemy lent the zone, the hunter imposed on it",
          all(pawn.zone is host_zone for pawn in (psycho, cat, bat))
          and all(game.imposed.get(pawn._get_address()) is hunter for pawn in (psycho, cat, bat)))
    check("the far walker walked, the near one and the flyer not", [call for call in game.calls if call[0] == "walk"]
          == [("walk", "Char_CatAdult_2")])
    check("all made 20 % faster, put in the bandits' team", all(
        pawn.CharacterMovement.MaxGroundSpeedScale.Value == 1.2 for pawn in (psycho, cat, bat))
        and cat.team is game_fixture.BANDITS)
    check("the game camps of the enemies made movable and placed on the hunter",
          all((zone.Outer.x, zone.Outer.y) == (0.0, 0.0) for zone in (camp_a, camp_b, camp_c)))
    check("the game's limit of enemies lifted for the copies", game.world_settings.bDisableSpawnBudget is True)
    check("the bar shown, in French, with the horde drawn and the Hardcore at 0 %",
          words() == "TUÉS 0   MORTS 0   HORDE 3   HARDCORE 0 %   00:00")
    woken = last("game_camps")
    check("decision 64: the game's camps near made critical at the start, the mod's own and the far one left alone",
          woken["made"] == 3 and woken["ours"] == 4 and woken["far"] == 1
          and all(zone.Outer.SpawnerComponent.SpawnDetails.bCritical for zone in (camp_a, camp_b, camp_c))
          and not far_camp.SpawnerComponent.SpawnDetails.bCritical)
    started = session._state["run"]
    check("decision 66: the births and the catch-up spread by the level's spread, each taking its own turns",
          started.wave.copies.spread.shares == started.level.spread == levels.SPREAD
          and started.parts.catch.spread.shares == levels.SPREAD
          and started.wave.copies.spread is not started.parts.catch.spread)

    second()
    check("each second the bar says the time played", words() == "TUÉS 0   MORTS 0   HORDE 3   HARDCORE 0 %   00:01")
    check("each second the wave told how many enemies follow, for Kevin's rule", started.wave.following == 3)
    second(4)
    joined = last("recruit")
    check("at the census, the copies born join the horde, in the image after the second's", joined.get("joined") == 3
          and len(session._state["run"].horde.drawn()) == 6)

    game.kill(psycho)
    second()
    lost = last("lost")
    check("a kill of the horde is counted and shown, and waits to come back; the bar counts the horde joined",
          lost["on"] == psycho.Name and lost["reason"] == "mover_dead" and lost["respawn"] == "waiting"
          and words().startswith("TUÉS 1   MORTS 0") and "HORDE 5" in words())
    second()
    born = last("born_again")
    check("it is born again of a camp of the mod behind the hunter", born.get("handed") == 1
          and born.get("of") == [psycho.Name])
    late_camps.append(game.zone(80000.0, "OakSpawner_Camp_Late").Outer)
    second(int(game_camps.EVERY_S))
    check("decision 64: a game camp come within reach is made critical at the next pass, EVERY_S later",
          late_camps[0].SpawnerComponent.SpawnDetails.bCritical and last("game_camps")["made"] == 1)
    second(4)
    newest = game.enemies[-1]
    check("and drawn again at the next census", newest.Name.startswith("Char_PsychoBasic_Male_OakSpawner_ItFollows")
          and newest.Name in session._state["run"].horde.names())
    check("the game camp no enemy of the horde comes from any more is put back where it stood, the others kept",
          (camp_a.Outer.x, camp_a.Outer.y) == camp_a.Outer.home[:2] and (camp_b.Outer.x, camp_b.Outer.y) == (0.0, 0.0))

    guard = game.enemy("Char_GunToterPistol_Male_9", 2500.0, "Char_GunToterPistol_Male", camp_a)
    game.imposed[guard._get_address()] = types.SimpleNamespace(_get_address=lambda: 999)
    second(5)
    check("an enemy another script holds is seen at the census but never drawn",
          guard.Name not in session._state["run"].horde.names())
    game.kill(guard)
    second(5)
    check("killed, the census counts it: a kill of an enemy never drawn", words().startswith("TUÉS 2   MORTS 0"))

    hunter.HealthState.bCurrentlyDead = True
    second()
    check("the hunter's death is counted and shown, the run going on", last("hunter_died") == {
        "event": "hunter_died", "run": 1, "deaths": 1} and words().startswith("TUÉS 2   MORTS 1")
        and session.running())
    hunter.HealthState.bCurrentlyDead = False
    second()
    check("alive again, still one death", words().startswith("TUÉS 2   MORTS 1"))

    before = words()
    pc.OakCharacter = None
    second(2)
    check("in a vehicle the controller holds no character: the run goes on and the bar keeps the time",
          session.running() and words() != before and words().startswith("TUÉS 2   MORTS 1"))
    pc.OakCharacter = hunter

    hunter.location = sdk_stubs.vector(100000.0, 0.0, 0.0)
    second()
    check("a jump of the hunter's place is written down", last("hunter_jumped").get("m") == 1000.0)
    second(3)
    check("the lent zone follows him there", (host_zone.x, host_zone.y) == (100000.0, 0.0))

    check("STOP stops the run", session.stop("stopped") == "stopped")
    stopped = last("stopped")
    check("the run stopped, written down with its counts", not session.running()
          and stopped["reason"] == "stopped" and stopped["kills"] == 2 and stopped["deaths"] == 1
          and stopped["level"] == 40 and stopped["played_s"] > 20.0)
    check("the game's camps given back their own flags at the stop",
          stopped["game_camps"] == {"restored": 4, "gone": 0, "failed": 0}
          and not any(camp.SpawnerComponent.SpawnDetails.bCritical
                      for camp in (camp_a.Outer, camp_b.Outer, camp_c.Outer, late_camps[0])))
    check("each enemy still drawn given its own zone back, the dead never called",
          cat.zone is camp_b and bat.zone is camp_c and psycho.zone is host_zone)
    check("its own team and its speed given back", cat.team is game_fixture.ORDER
          and all(pawn.CharacterMovement.MaxGroundSpeedScale.Value == 1.0 for pawn in (cat, bat)))
    check("the game camps put back where they stood", all(
        (zone.Outer.x, zone.Outer.y) == (zone.Outer.home[0], zone.Outer.home[1]) for zone in (camp_b, camp_c)))
    check("the lent zone put back and narrowed", (host_zone.x, host_zone.settings.CombatTerritory.Radius)
          == (host_spawner.x, 3000.0))
    check("the game's limit given back", game.world_settings.bDisableSpawnBudget is False)
    check("the bar taken off the screen", game.screen.shown() == [] and stopped["bar"] == "removed")
    check("a second stop does nothing", session.stop() == "not_running")
    first = kept.runs()[0] if kept.runs() else None
    check("the run stopped on top of the history, with its level, limit and counts; its result waiting",
          first is not None and (first.level, first.limit_s, first.end) == (40, None, "stopped")
          and first.kills == stopped["kills"] and first.deaths == stopped["deaths"] and ending.waiting() == first)
    ending.shown()

    pool = session._state["pool"]
    made_before = len(game.spawners_made)
    # Where no enemy of the first run stands: the fake enemies never walk, so those the catch-up last put near the
    # first start, at the spread's distances, would stand there still and be copied again.
    hunter.location = sdk_stubs.vector(0.0, 300000.0, 0.0)
    check("a run with a time limit starts", session.start(settings(duration_s=10.0)) == "started")
    check("the camps of the mod are kept for it: only its lent zone's camp is made anew",
          session._state["pool"] is pool and len(game.spawners_made) == made_before + 1)
    second(9)
    check("under its limit it goes on", session.running())
    second(30, paused=True)
    timed = session._state["run"].clock
    check("decision 92: the game paused, its world's time standing still, nothing is played",
          session.running() and 8.0 < timed.played < 10.0 and timed.fallbacks == 0)
    second(2)
    check("at its limit of time played it stops", not session.running() and last("stopped")["reason"] == "time_up")
    check("its result waiting for the window, the history holding its limit",
          ending.waiting() is kept.runs()[0] and (kept.runs()[0].end, kept.runs()[0].limit_s) == ("time_up", 10)
          and last("result_window_failed") == {} and last("history_added")["end"] == "time_up")
    ending.shown()

    check("a run starts again", session.start(settings()) == "started")
    hunter.freed = True
    second()
    check("the player left the game: the run stops, kept in the history, no result waiting", not session.running()
          and last("stopped")["reason"] == "left_game" and kept.runs()[0].end == "left_game"
          and ending.waiting() is None)
    hunter.freed = False

    check("a run without the bar: none shown, none kept each second",
          session.start(settings(bar=False)) == "started" and game.screen.shown() == [] and second() is None
          and game.screen.shown() == [] and session.stop() == "stopped" and last("stopped")["bar"] == "none")
    ending.shown()
    asked: list[tuple] = []
    real_everyone = census.everyone
    census.everyone = lambda found, here, limit, within_m=None: (
        asked.append((limit, within_m)), real_everyone(found, here, limit, within_m))[1]
    check("decisions 96 and 97: a run with the player's most and the far enemies let go starts, said, each piece "
          "told, the crowd at its start no more than the most and within the catch-up's distance",
          session.start(settings(crowd_max=30, manage_far=False)) == "started"
          and asked == [(30, levels.level(40).far_m)]
          and (last("starting")["crowd_max"], last("starting")["manage_far"]) == (30, False)
          and session._state["run"].wave.most == 30
          and (session._state["run"].parts.crowd_max, session._state["run"].parts.manage_far) == (30, False)
          and session.stop() == "stopped")
    ending.shown()
    asked.clear()
    session.start(settings())
    check("the far enemies managed: the crowd at the start read at any distance", asked == [(120, None)]
          and session.stop() == "stopped")
    census.everyone = real_everyone
    ending.shown()
    check("one more run", session.start(settings()) == "started")
    lent = session._state["run"].zone.shift.zone()
    lent.K2_SetWorldLocation = lambda **fields: (True, None)
    lent.x = 50000.0
    second(3)
    check("a zone the game moves away and that will not come back stops the run",
          not session.running() and last("stopped")["reason"] == "zone_lost"
          and last("zone_replaced")["outcome"] == "not_moved")

    hunter.location = sdk_stubs.vector(0.0, 0.0, 0.0)
    game.refuse_spawn = True
    check("the game refusing the mod's camp: the run does not start, said", session.start(settings()) == "no_camp"
          and not session.running() and last("refused")["why"] == "no_camp" and game.screen.shown() == []
          and last("stopped")["reason"] == "no_camp")
    game.refuse_spawn = False
    game.zones_stuck = True
    for zone in (camp_b, camp_c):
        zone.Outer.x, zone.Outer.y = zone.Outer.home[:2]
    check("the lent zone refusing to move onto the hunter: the run does not start, everything given back",
          session.start(settings()) == "zone_not_moved" and not session.running()
          and last("refused")["why"] == "zone_not_moved" and game.world_settings.bDisableSpawnBudget is False
          and all((zone.Outer.x, zone.Outer.y) == zone.Outer.home[:2] for zone in (camp_b, camp_c)))
    game.zones_stuck = False

    keep_census = census.seen_around

    def broken(*_args: object, **_fields: object) -> None:
        raise RuntimeError("census")

    census.seen_around = broken
    check("a start that raises: refused, written down, what it took given back and said, no run left behind",
          session.start(settings()) == "start_failed" and not session.running()
          and last("start_failed") == {"event": "start_failed", "run": 10, "error": "RuntimeError"}
          and last("stopped")["reason"] == "start_failed"
          and state["info"][-1] == "[It Follows] The run could not start. What it had changed was given back. The "
                                   "reason is in unrealsdk.log.")
    keep_end = run_module.Run.end

    def end_broken(_run: object, _reason: str) -> None:
        raise RuntimeError("end")

    run_module.Run.end = end_broken
    check("the giving back raising too: said to quit to the main menu, written down, no run left behind",
          session.start(settings()) == "start_failed" and not session.running()
          and last("stop_failed") == {"event": "stop_failed", "run": 11, "error": "RuntimeError"}
          and "Quit to the main menu and load your game again." in state["info"][-1])
    run_module.Run.end, census.seen_around = keep_end, keep_census

    hunter.location = sdk_stubs.vector(0.0, 0.0, 0.0)
    check("a run starts after a failed start", session.start(settings()) == "started")
    check("the enemies of the game around at the start are the place's first kinds",
          session._state["run"].wave.kinds.met != {})
    victim = game.enemy("Char_PsychoBasic_Male_21", 1200.0, "Char_PsychoBasic_Male", camp_a)
    second(5)
    stranger = game.enemy("Char_GunToterPistol_Male_20", 1500.0, "Char_GunToterPistol_Male", camp_a)
    second(5)
    drawn = session._state["run"].horde.names()
    met = [kind for kind, _at in session._state["run"].wave.kinds.met.values()]
    check("the enemies of the game met join the horde, one census after the other; both are remembered among the "
          "place's kinds, met before they joined (decision 68)",
          victim.Name in drawn and stranger.Name in drawn
          and {"Char_GunToterPistol_Male", "Char_PsychoBasic_Male"} <= set(met))
    game.kill(victim)
    second(2)
    born = last("born_again")
    check("decision 56: a killed one comes back as a kind of the place",
          born.get("of") == [victim.Name] and len(born.get("kinds", [])) == 1 and born["kinds"][0] in met)
    second(30)
    status = last("status")
    check("a status line counts the copies in the horde and their camps, and says the kinds met, the game's camps and "
          "where the horde stood",
          {"copies", "kinds", "copy_camps", "game_camps", "horde_at"} <= set(status) and "horde_room" not in status
          and 0 < status["copies"] < status["horde"] and status["copy_camps"]["alive"] >= status["copies"]
          and status["kinds"] >= 1 and set(status["horde_at"]) == {"close", "on_way", "far", "unplaced"}
          and sum(status["horde_at"].values()) > 0)
    check("decision 72: the status line says how many enemies the float watch looked at and how many floated",
          set(status["floating"]) == {"looked", "floating", "on_body", "floaters"} and status["floating"]["looked"] > 0)
    check("audit: the status line says the catch-up's traces, the walks' blocks, the hook's calls a second, the "
          "longest second and each task put off",
          "traces" in status["catch_up"] and status["walk_blocks"] >= 1 and status["hook_calls_s"] > 0
          and set(status["tasks_ms"]) == {"sweep", "follow", "census", "game_camps"} and "slowest_ms" in status)
    check("decision 107: the second's pass over a horde of 60 made in two parts of 30, none cut short, the longest "
          "part timed", status["horde"] == 60 and status["sweep"]["parts"] == 2 and status["sweep"]["cut"] == 0
          and status["sweep"]["part_ms"] >= 0.0)
    check("decision 102: the status line says the images a second over its span and its lowest second, the engine's "
          "count announced once before it was first read",
          status["fps"] == 60.0 and status["fps_low"] == 60.0
          and [line for line in lines() if line.get("call") == "GetFrameCount"][-1]["run"] == status["run"])
    check("audit of 16 October: the status line says the walks given, the Execs read for them and their calls' time, "
          "and the bodies the last census read",
          set(status["walks"]) == {"walks", "exec_reads", "walk_ms"} and status["walks"]["walks"] >= 1
          and isinstance(status["bodies"], int) and status["bodies"] >= 1)
    check("audit of 16 October, A11: the status line says what a hook call with nothing to do took in the beat",
          isinstance(status["hook_idle_us"], float) and status["hook_idle_us"] > 0.0)
    held = session._state["run"].wave.copies.held()
    check("audit of 16 October: the copies are told the camps of the enemies the horde holds",
          held and held == {session._state["run"].parts.camp_map.of.get(name)
                            for name in session._state["run"].horde.names()})
    recruited = last("recruit")
    check("audit of 16 October: the recruit line says the census's search apart, and how long the recruits took",
          recruited["scan_ms"] >= 0.0 and recruited["join_ms"] >= 0.0)
    check("decision 105: the run's census, at the start and for its recruits, reads the characters of the "
          "hunter's world only",
          recruited["search"] == "actors"
          and [line for line in lines() if line["event"] == "started"][-1]["search"] == "actors")
    this_run = last("status")["run"]
    camps_said = [line for line in lines() if line["event"] == "game_camps" and line["run"] == this_run]
    check("decision 105: the game's camps searched in the hunter's world, at the start and at each pass",
          camps_said and all(line["search"] == "actors" for line in camps_said))
    statics = state["classes"]["GameplayStatics"].ClassDefaultObject
    statics.GetAllActorsOfClass = lambda **_fields: (_ for _ in ()).throw(RuntimeError("refused"))
    second(11)
    del statics.GetAllActorsOfClass
    check("a pass whose search of the world fails is written down, searched among every object instead",
          [line for line in lines() if line["event"] == "game_camps"][-1]["search"] == "find_all:RuntimeError")
    running = session._state["run"]
    written = len([line for line in lines() if line["event"] == "status"])
    running.gauge.next_status = clock[0]
    clock[0] += 1.0
    drawn_images[0] += 60
    game.world_clock[0] += 1.0
    animation_hook.beats()[frame.IDENTIFIER](None, None, None, None)
    check("the status line is not written in the second's own image, but put off to one of its own",
          len([line for line in lines() if line["event"] == "status"]) == written
          and "status" in running.beat.later)
    check("decision 107: the second's own image makes the first part of the pass, the next put off first, the "
          "enemies after the first part waiting for it",
          next(iter(running.beat.later)) == "sweep" and len(running.sweep.queue) == len(running.horde.drawn()) - 30)
    second(30)
    check("the status line takes an image of its own, measured in the next one", "status" in last("status")["tasks_ms"])
    check("decision 109: no Hardcore step under 100 kills, 0 % said in the status line and at the stop",
          last("status")["hardcore"] == 0 and stopped["hardcore"] == 0 and last("hardcore_step") == {})
    session.stop()

    health_fixture.install(state)
    taken = types.SimpleNamespace(BaseValue=1.0, Value=0.9)
    hunter.DamageState = types.SimpleNamespace(DamageTakenMultiplier=taken)
    tough = game.enemy("Char_PsychoBasic_Male_31", 1000.0, "Char_PsychoBasic_Male", camp_a)
    tough.pools = [health_fixture.Pool(1000.0, bonus=1.3), health_fixture.Pool(500.0), None]
    check("decision 79: a run with Buff+ starts, its two factors written down",
          session.start(settings(health=1.4, taken=1.2)) == "started"
          and (last("starting")["health"], last("starting")["taken"]) == (1.4, 1.2))
    raised = [line for line in lines() if line["event"] == "health_raised" and line["on"] == tough.Name]
    check("an enemy drawn holds 40 % more health and shield, still full, written down",
          abs(tough.pools[0].most - 1820.0) <= 18.2 and abs(tough.pools[0].left - tough.pools[0].most) <= 1e-6
          and abs(tough.pools[1].most - 700.0) <= 7.0 and len(raised) == 1 and raised[0]["pool_1"][0] == 1300)
    check("the hunter takes 20 % more damage", (taken.BaseValue, round(taken.Value, 3)) == (1.2, 1.08)
          and last("taken_raised") == {"event": "taken_raised", "run": last("starting")["run"], "base": [1.0, 1.2],
                                       "value": [0.9, 1.08]})
    second(5)
    check("each second the multiplier holds, nothing written", last("taken_kept") == {} and taken.BaseValue == 1.2)
    run = session._state["run"]
    toughness = run.parts.toughness
    run.stats.kills = 199
    second()
    step = last("hardcore_step")
    check("decision 109: at 199 kills the Hardcore reaches 1 %, the enemies joining next raised 1.4 x 1.01 and the "
          "hunter's damage taken 1.2 x 1.01, the Buff kept under it",
          (step.get("percent"), step.get("kills"), step.get("health")) == (1, 199, 1.414)
          and abs(toughness.factor - 1.414) <= 1e-9 and abs(taken.BaseValue - 1.212) <= 1e-9
          and abs(taken.Value - 0.9 * 1.212) <= 1e-9)
    check("the bar says the run's percent", "HARDCORE 1 %" in words())
    check("an enemy already in the horde keeps its maximum", abs(tough.pools[0].most - 1820.0) <= 18.2)
    run.stats.kills = 150
    second()
    check("no line again within the same step", last("hardcore_step") == step)
    run.stats.kills = 412
    second()
    check("several steps at once: 4 %", last("hardcore_step").get("percent") == 4
          and abs(taken.BaseValue - 1.2 * 1.04) <= 1e-9 and "HARDCORE 4 %" in words())
    tough.pools[0].left = tough.pools[0].most / 2
    session.stop()
    check("at the stop the enemy still drawn has the game's maximum back with its share, the hunter his multiplier, "
          "both written down",
          abs(tough.pools[0].most - 1300.0) <= 13.0 and abs(tough.pools[0].left - 650.0) <= 6.5
          and last("stopped")["taken"] == "restored" and (taken.BaseValue, round(taken.Value, 3)) == (1.0, 0.9)
          and last("stopped")["health"]["restored"] == 1 and last("stopped")["hardcore"] == 4)

    check("a run again, its Hardcore from 0 %, the enemies raised by nothing more",
          session.start(settings()) == "started" and session._state["run"].hardcore.percent == 0
          and session._state["run"].parts.toughness.factor == 1.0 and "HARDCORE 0 %" in words())
    it_follows.mod.on_disable()
    check("the mod disabled stops it", not session.running() and last("stopped")["reason"] == "mod_disabled")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")
    import traceback
    traceback.print_exc()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
