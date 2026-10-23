"""Tests the companions' team (companions/team.py) and its owner (session.py), the game faked (companion_fixture.py):
a start calls each companion chosen, MOST at most, sets one hook and says so; none chosen, nothing; each called is
born one beat after another, found by its spawner and followed, rank by rank; a join refused when the team is full,
without a hunter, while the one born is not there yet, followed already, or without a zone; a dead one comes back
AFTER_S later, born again and followed again; the stop ends every follow, forgets those on their way, removes the hook
and says so. Companions are asked by their name, an unknown one left out; a hunter is Lemmy dressed at his birth,
and dressed again when he comes back as himself; an ally is never dressed. Each follows with its card's choice, the
default for one not given, the same when it comes back, said at the start. session.py starts one team at a time,
says it, stops it, and the mod stops it when switched off."""

import json
import pathlib
import sys
import threading
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import companion_fixture as fake  # noqa: E402
import it_follows  # noqa: E402
from it_follows import session  # noqa: E402
from it_follows.companions import choices, respawn, team as team_module, wardrobe  # noqa: E402

fails: list[str] = []
ABOMINATION, CRANKUS = "Char_NPC_Abomination", "Char_GunToter_SiblingRivalry_Crankus"
LEMMY = "Char_GunToter_Shatter2_Lemmy"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    found = [json.loads(text.removeprefix("[It Follows] ")) for text in state["info"]
             if text.startswith("[It Follows] {")]
    return [line for line in found if line["event"] == event]


def beat(team: team_module.Team, clock: fake.Clock, moment: float) -> None:
    clock.now = moment
    state["hooks"][team_module.IDENTIFIER].fn()


def camera() -> None:
    """The camera's update, where the wardrobe dresses (decision 65)."""
    state["hooks"][wardrobe.IDENTIFIER].fn()


check("eight at most, its own hook on the animation update", team_module.MOST == 8
      and team_module.IDENTIFIER == "it_follows:companions"
      and team_module.HOOK == "/Script/Engine.AnimInstance:BlueprintUpdateAnimation")
check("ranks shifted by an eighth of a second each", team_module.offset(0, 1.0) == 0.0
      and team_module.offset(3, 1.0) == 0.375)
game = fake.Game(state)
clock = fake.Clock()
births = fake.Births(game)
team = team_module.Team(clock, births)
check("none chosen: nothing called, no hook", team.start([]) == "empty" and not team.respawns.pending()
      and team_module.IDENTIFIER not in state["hooks"])
check("started: each called, the hook set, said", team.start(["Abomination", "Nobody", "Crankus"]) == "started"
      and [line["companion"] for line in notes("companion_called")] == ["Abomination", "Crankus"]
      and state["hooks"][team_module.IDENTIFIER].enabled
      and notes("team_start")[-1]["companions"] == ["Abomination", "Crankus"]
      and notes("team_start")[-1]["unknown"] == 1)
beat(team, clock, 100.0)
check("the first born at the first beat, alone", births.asked == [ABOMINATION])
beat(team, clock, 101.0)
check("then found and followed, the second born", [one.definition for one in team.active()] == [ABOMINATION]
      and births.asked == [ABOMINATION, CRANKUS] and notes("companion_start")[-1]["rank"] == 0
      and notes("companion_start")[-1]["companion"] == "Abomination" and "dressed" not in notes("companion_start")[-1])
beat(team, clock, 102.0)
check("both followed, rank by rank", [(one.definition, one.rank) for one in team.active()] == [
      (ABOMINATION, 0), (CRANKUS, 1)] and not team.respawns.pending())
first = team.active()[0]
first.actor().HealthState.bCurrentlyDead = True
beat(team, clock, 103.0)
check("one dead: out of the team, coming back", [one.definition for one in team.active()] == [CRANKUS]
      and team.respawns.pending() and notes("companion_dead")[-1]["back_in_s"] == respawn.AFTER_S)
beat(team, clock, 147.0)
check("not born again before AFTER_S", births.asked == [ABOMINATION, CRANKUS])
beat(team, clock, 148.0)
beat(team, clock, 149.0)
check("born again AFTER_S later, followed again, its rank free again", births.asked[-1] == ABOMINATION
      and {(one.definition, one.rank) for one in team.active()} == {(ABOMINATION, 0), (CRANKUS, 1)}
      and team.active()[-1].on_death is not None)

check("a spawner unknown: not found yet", team.join("Abomination", "OakSpawner_999", None) == {"done": "not_found"})
followed = team.active()[0]
spawner = followed.actor().zone.owner
named = {ABOMINATION: "Abomination", CRANKUS: "Crankus"}[followed.definition]
check("the same character again: refused", team.join(named, spawner, None) == {"done": "followed_already"})
bare = game.companion(50)
object.__setattr__(bare, "zone", None)
check("a companion without a zone is never found by its spawner", team.join("Abomination", "OakSpawner_50", None) == {
      "done": "not_found"})
pc = state["pc"]
state["pc"] = None
check("no hunter: refused", team.join("Abomination", "OakSpawner_1", None) == {"done": "no_character"})
state["pc"] = pc
for number in range(2, 8):
    game.companion(number)
    team.join("Abomination", f"OakSpawner_{number}", None)
game.companion(8)
check("eight followed: the ninth refused", len(team.active()) == 8
      and team.join("Abomination", "OakSpawner_8", None) == {"done": "team_full"}
      and team.join("Nobody", "OakSpawner_8", None) == {"done": "unknown"})
team.respawns.died("Crankus", None)
check("the stop: every follow ended, the waiting forgotten, the hook removed, said", team.stop("stopped") == 8
      and team.active() == [] and not team.respawns.pending() and team_module.IDENTIFIER not in state["hooks"]
      and notes("team_stop")[-1] == {"event": "team_stop", "run": 0, "why": "stopped", "following": 8,
                                     "on_their_way": 1, "failed": 0, "off_thread": 0}
      and team.ended == "stopped"
      and [line["why"] for line in notes("companion_end")[-8:]] == ["stopped"] * 8)
failing = team_module.Team(clock, births)
for number in (20, 21):
    game.companion(number)
    failing.join("Abomination", f"OakSpawner_{number}", None)
failing.follows[0].finish = lambda _why: (_ for _ in ()).throw(RuntimeError("finish"))
check("one follow's end raising: the other ended all the same, the failure counted",
      failing.stop("stopped") == 2 and failing.follows == [] and notes("team_stop")[-1]["failed"] == 1
      and notes("companion_end")[-1]["why"] == "stopped")
many = team_module.Team(clock, births)
refused = len(notes("companion_refused"))
many.start(["Abomination"] * 10)
check("ten chosen: eight called, none refused", len(many.respawns.waiting) == 8
      and len(notes("companion_refused")) == refused)
many.stop("stopped")

class Dressing:
    """dress.Dressing as the team drives it: start() answers START(); step() waits STEPS calls, then answers worn, or
    raises when STEP_FAILS; give_up() noted."""
    made: list = []
    START = staticmethod(lambda name: {"done": "swapped", "hunter": name})
    STEPS, STEP_FAILS = 2, False

    def __init__(self, actor: object, name: str, clock: object, own: object = "unset") -> None:
        self.character, self.name, self.steps, self.gave_up, self.started = str(actor().Name), name, 0, False, 0
        self.own = own
        Dressing.made.append(self)

    def start(self) -> dict:
        self.started += 1
        return Dressing.START(self.name)

    def step(self) -> dict | None:
        self.steps += 1
        if Dressing.STEP_FAILS:
            raise RuntimeError("broken")
        return None if self.steps < Dressing.STEPS else {"done": "worn", "hunter": self.name}

    def give_up(self) -> None:
        self.gave_up = True


team_module.dress = types.SimpleNamespace(Dressing=Dressing)
hunters = team_module.Team(clock, births)
hunters.start(["Rafa", "Crankus"])
for moment in (200.0, 201.0):
    beat(hunters, clock, moment)
rafa = hunters.active()[0]
check("a hunter: Lemmy born, handed to the wardrobe as he is found, said; nothing changed from the beat",
      births.asked[-2:] == [LEMMY, CRANKUS]
      and [(one.character, one.name) for one in Dressing.made] == [(rafa.name, "Rafa")] and rafa.definition == LEMMY
      and notes("companion_start")[-1]["companion"] == "Rafa" and notes("companion_start")[-1]["dressed"] == "queued"
      and len(hunters.wardrobe.waiting) == 1 and Dressing.made[0].started == 0)
check("the wardrobe's own hook on the camera's modifiers' update", wardrobe.IDENTIFIER in state["hooks"]
      and wardrobe.HOOK == "/Script/Engine.CameraModifier:BlueprintModifyCamera")
camera()
check("started at the camera's update, said, kept to be finished", Dressing.made[0].started == 1
      and notes("companion_dressing")[-1] == {"event": "companion_dressing", "run": 0, "character": rafa.name,
                                              "companion": "Rafa", "done": "swapped", "hunter": "Rafa"}
      and len(hunters.wardrobe.dressing) == 1 and hunters.wardrobe.waiting == [])
beat(hunters, clock, 202.0)
beat(hunters, clock, 202.5)
check("the beat never takes a dressing further", Dressing.made[0].steps == 0)
camera()
camera()
check("his own outfit chosen: dressed without the player's colours", Dressing.made[0].own is None)
check("the ally beside him not dressed", notes("companion_start")[-1]["companion"] == "Crankus"
      and "dressed" not in notes("companion_start")[-1] and len(Dressing.made) == 1)
check("finished at a later camera's update: said, forgotten", Dressing.made[0].steps == 2
      and hunters.wardrobe.dressing == []
      and notes("companion_dressed")[-1] == {"event": "companion_dressed", "run": 0, "character": rafa.name,
                                             "companion": "Rafa", "done": "worn", "hunter": "Rafa"})
rafa.actor().HealthState.bCurrentlyDead = True
beat(hunters, clock, 203.0)
check("the hunter dead: Rafa coming back, not any Lemmy", notes("companion_dead")[-1]["companion"] == "Rafa")
for moment in (248.0, 249.0, 250.0):
    beat(hunters, clock, moment)
back = [one for one in hunters.active() if one.definition == LEMMY]
camera()
check("born again as Lemmy himself, dressed again as Rafa", births.asked[-1] == LEMMY and len(back) == 1
      and back[0] is not rafa and [(one.character, one.name) for one in Dressing.made[1:]] == [(back[0].name, "Rafa")]
      and Dressing.made[1].started == 1)
game.companion(60, (300.0, 0.0, 0.0), LEMMY)
hunters.join("Amon", "OakSpawner_60", 3.0)
amon = hunters.active()[-1]
amon.actor().HealthState.bCurrentlyDead = True
beat(hunters, clock, 260.0)
check("a hunter dead: back as himself with the same health", hunters.respawns.waiting[-1]["companion"] == "Amon"
      and hunters.respawns.waiting[-1]["times"] == 3.0)
hunters.stop("stopped")

Dressing.START = staticmethod(lambda name: {"done": "not_loaded", "parts": ["X"]})
hunters = team_module.Team(clock, births)
hunters.start(["Vex"])
for moment in (300.0, 301.0):
    beat(hunters, clock, moment)
camera()
check("a dressing not started: said, not kept, the hunter followed all the same", len(hunters.active()) == 1
      and hunters.wardrobe.dressing == [] and hunters.wardrobe.waiting == []
      and notes("companion_dressing")[-1]["done"] == "not_loaded" and notes("companion_dressing")[-1]["parts"] == ["X"])
hunters.stop("stopped")
Dressing.START = staticmethod(lambda name: 1 / 0)
hunters = team_module.Team(clock, births)
hunters.start(["Vex"])
for moment in (310.0, 311.0):
    beat(hunters, clock, moment)
camera()
check("a dressing that fails to start: said, the hunter followed all the same", len(hunters.active()) == 1
      and hunters.wardrobe.dressing == [] and notes("companion_dressing")[-1]["done"].startswith(
          "failed:ZeroDivisionError"))
hunters.stop("stopped")

Dressing.START = staticmethod(lambda name: {"done": "swapped", "hunter": name})
Dressing.STEP_FAILS = True
hunters = team_module.Team(clock, births)
hunters.start(["Vex"])
for moment in (320.0, 321.0, 322.0):
    beat(hunters, clock, moment)
camera()
camera()
failing = Dressing.made[-1]
check("a step that fails: given up (shown again), said, forgotten", failing.gave_up and hunters.wardrobe.dressing == []
      and notes("companion_dressed")[-1]["done"].startswith("failed:RuntimeError"))
hunters.stop("stopped")
Dressing.STEP_FAILS, Dressing.STEPS = False, 1000
hunters = team_module.Team(clock, births)
hunters.start(["Harlowe"])
for moment in (330.0, 331.0):
    beat(hunters, clock, moment)
camera()
pending = Dressing.made[-1]
hunters.stop("stopped")
check("the team stopping while one is being dressed: given up, shown again, forgotten, the wardrobe unhooked",
      pending.gave_up and hunters.wardrobe.dressing == [] and wardrobe.IDENTIFIER not in state["hooks"])
many_lemmys = [game.companion(70 + number, definition=LEMMY) for number in range(10)]
for lemmy in many_lemmys:
    hunters._dress(lemmy, "Rafa", "Rafa")
late = team_module.Team(clock, births)
late.start(["Crankus"])
late._dress(game.companion(90, definition=LEMMY), "Rafa", "Rafa")
clock.now += wardrobe.START_WAIT_S + 1.0
late.beat()
check("the team's beat forgets a hunter the camera's update never came for, said", late.wardrobe.waiting == []
      and notes("companion_dressing")[-1]["done"] == "camera_never_came")
late.stop("stopped")
check("the hunters waiting to be dressed: MOST at most, the latest kept", [
      held[0] for held in hunters.wardrobe.waiting] == [str(lemmy.Name) for lemmy in many_lemmys[-team_module.MOST:]])


picked = team_module.Team(clock, births)
picks = {"Crankus": choices.Choice(False, "+30%")}
picked.start(["Crankus", "Abomination"], picks)
check("each started with its card's choice, the default for one not given, said", picked.picks == {
      "Crankus": choices.Choice(False, "+30%"), "Abomination": choices.Choice()}
      and notes("team_start")[-1]["choices"] == {"Crankus": [False, "+30%", "own"],
                                                 "Abomination": [True, "+20%", "own"]})
beat(picked, clock, 400.0)
beat(picked, clock, 401.0)
crankus = picked.active()[0]
check("its follow given its choice", crankus.picked == choices.Choice(False, "+30%") and crankus.pace.factor == 1.3)
crankus.actor().HealthState.bCurrentlyDead = True
beat(picked, clock, 402.0)
for moment in range(447, 451):
    beat(picked, clock, float(moment))
check("back after its death with the same choice", [one.picked for one in picked.active()
                                                    if one.definition == CRANKUS] == [choices.Choice(False, "+30%")])
picked.stop("stopped")
painted = team_module.Team(clock, births)
painted.picks = {"Vex": choices.Choice(outfit="player")}
painted._dress(types.SimpleNamespace(Name="Char_GunToter_Shatter2_Lemmy_9"), "Vex", "Vex")
check("the player's colours chosen: dressed with them", Dressing.made[-1].own is team_module._player_own)
real_paint = team_module.player_paint
team_module.player_paint = types.SimpleNamespace(of=lambda pc: {"of": pc})
check("the player's colours and head read from the player's controller", team_module._player_own() == {
      "of": team_module.get_pc()})
team_module.player_paint = real_paint

check("session: nothing on", session.team_live() is None and session.stop_team() == "not_on")
check("session: none chosen, nothing on", session.start_team([]) == "empty" and session.team_live() is None
      and session.start_team(["Nobody"]) == "empty")
check("session: the team started, on, with the choices given", session.start_team(
      ["Crankus"], {"Crankus": choices.Choice(True, "Off")}) == "started"
      and session.team_live() == session.TeamLive(0, 1)
      and notes("team_start")[-1]["choices"] == {"Crankus": [True, "Off", "own"]})
check("session: one team at a time", session.start_team(["Abomination"]) == "already_on")
check("session: stopped, off, the hook removed", session.stop_team() == "stopped" and session.team_live() is None
      and team_module.IDENTIFIER not in state["hooks"] and notes("team_stop")[-1]["why"] == "stopped")
first_births = session._state["companion_births"]
session.start_team(["Crankus"])
check("one set of camps for every team of the game session, as the Horde's (decision 59)",
      first_births is not None and session._state["team"].births is first_births)
fake.at_level(None)
real_stop_normal = session.stop_normal
session.stop_normal = lambda _reason: (_ for _ in ()).throw(RuntimeError("normal"))
it_follows._on_disable()
session.stop_normal = real_stop_normal
check("the mod switched off, the normal mode's stop raising: the team stopped all the same, said",
      session.team_live() is None and notes("team_stop")[-1]["why"] == "mod_disabled"
      and notes("disabled")[-1]["failed"] == ["normal:RuntimeError"])

session.start_team(["Crankus"])
broken = session._state["team"]
broken.respawns.clear = lambda: (_ for _ in ()).throw(RuntimeError("clear"))
try:
    session.stop_team()
    stop_raised = False
except RuntimeError:
    stop_raised = True
check("a stop failing midway: the hook removed all the same, no team left running unowned",
      stop_raised and broken.hook is None and team_module.IDENTIFIER not in state["hooks"]
      and session.team_live() is None)

menu = {"shown": None, "reads": 0}


def menu_read() -> bool | None:
    menu["reads"] += 1
    return menu["shown"]


ends: list = []
watched = team_module.Team(clock, births, end=ends.append, menu=menu_read)
watched.start(["Crankus"])
beat(watched, clock, 600.0)
check("the menu read at the first beat, unknown: the team goes on, said once",
      menu["reads"] == 1 and ends == [] and notes("main_menu_read")[-1]["shown"] is None)
said_reads = len(notes("main_menu_read"))
beat(watched, clock, 600.5)
check("read again only after MENU_EVERY_S", menu["reads"] == 1)
menu["shown"] = False
beat(watched, clock, 601.0)
beat(watched, clock, 602.0)
check("a game: the team goes on, the change said once", menu["reads"] == 3 and ends == []
      and len(notes("main_menu_read")) == said_reads + 1 and notes("main_menu_read")[-1]["shown"] is False)
menu["shown"] = True
watched.respawns.call("Abomination", None)
followed = len(watched.active())
asked_before = len(births.asked)
beat(watched, clock, 610.0)
check("the main menu: its owner asked to stop it (decision 61), nothing else done that beat, one due not asked",
      ends == ["main_menu"] and notes("main_menu_read")[-1]["shown"] is True
      and len(watched.active()) == followed and len(births.asked) == asked_before)
watched.stop("main_menu")
clock.now = 620.0
watched.beat()
check("stopped: never asked again, even by a last call of the hook", ends == ["main_menu"])
unowned = team_module.Team(clock, births, menu=menu_read)
reads_before = menu["reads"]
unowned.start(["Crankus"])
beat(unowned, clock, 700.0)
check("a team with no owner to ask never reads the menu", menu["reads"] == reads_before)
unowned.stop("stopped")

real_showing = session.main_menu.showing
session.main_menu.showing = lambda _pc: True
check("session: no team launched at the main menu (it would stop at once)",
      session.start_team(["Crankus"]) == "main_menu" and session.team_live() is None)
session.main_menu.showing = lambda _pc: None
check("session: the menu unread, the team launched as before", session.start_team(["Crankus"]) == "started")
owned = session._state["team"]
owned.end("main_menu")
check("session: the team asking at the main menu, stopped by its owner, said",
      session.team_live() is None and notes("team_stop")[-1]["why"] == "main_menu"
      and team_module.IDENTIFIER not in state["hooks"])
session.start_team(["Crankus"])
stops = len(notes("team_stop"))
owned.end("main_menu")
check("session: an old team asking leaves the new one on", session.team_on() and len(notes("team_stop")) == stops)
session.stop_team()
session.main_menu.showing = real_showing

menu["shown"] = False
elsewhere = team_module.Team(clock, births, end=ends.append, menu=menu_read)
elsewhere.start(["Crankus"])
asked_before, reads_before, ends_before = len(births.asked), menu["reads"], list(ends)
clock.now = 800.0
worker = threading.Thread(target=lambda: (state["hooks"][team_module.IDENTIFIER].fn(),
                                          state["hooks"][team_module.IDENTIFIER].fn()))
worker.start()
worker.join(5)
check("a beat on another thread than the game's: nothing asked, nothing read, said once (trial 206)",
      len(births.asked) == asked_before and menu["reads"] == reads_before and ends == ends_before
      and notes("hook_off_thread")[-1]["what"] == "team" and len(notes("hook_off_thread")) == 1)
beat(elsewhere, clock, 801.0)
check("the next beat on the game's thread: the companion asked", len(births.asked) == asked_before + 1)
elsewhere.stop("stopped")
check("the beats on another thread counted at the stop", notes("team_stop")[-1]["off_thread"] == 2)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
