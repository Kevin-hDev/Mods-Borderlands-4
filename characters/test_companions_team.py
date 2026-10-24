"""Tests the companions' team (companions/team.py), the game faked (companion_fixture.py):
a start calls each companion chosen, MOST at most, sets one hook and says so; none chosen, nothing; each called is
born one beat after another, found by its spawner and followed, rank by rank; a join refused when the team is full,
without a hunter, while the one born is not there yet, followed already, or without a zone; a dead one comes back
after the wait its mod gives, born again and followed again; the stop ends every follow, forgets those on their way,
removes the hook and says so. Companions are asked by their name, an unknown one left out; a hunter is Lemmy dressed
at his birth, and dressed again when he comes back as himself; an ally is never dressed. Each follows with what its
mod gives it, checked, the same when it comes back, said at the start; the starting values, said, when the mod's
reading fails. The main menu read once a MENU_EVERY_S, its owner asked to stop it there; a beat on another thread
does nothing. Another mod leading the team (owners.py): it does not start; another coming to lead: its owner
asked to stop it. Its beat on the package's one hook on the animation update; before its parts' earliest due time
a call does nothing, a tenth of a second at most, and every 30 s a line says what it costs (audit of 24 October
2026, C1). Its owner in It Follows: test_session_team.py there."""

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
from characters import animation_hook  # noqa: E402
from characters.companions import owners, team as team_module, tuning, wardrobe  # noqa: E402

fails: list[str] = []
ABOMINATION, CRANKUS = "Char_NPC_Abomination", "Char_GunToter_SiblingRivalry_Crankus"
LEMMY = "Char_GunToter_Shatter2_Lemmy"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    found = [json.loads(text.removeprefix("[Characters] ")) for text in state["info"]
             if text.startswith("[Characters] {")]
    return [line for line in found if line["event"] == event]


def beat(team: team_module.Team, clock: fake.Clock, moment: float) -> None:
    clock.now = moment
    animation_hook.beats()[team_module.IDENTIFIER]()


def camera() -> None:
    """The camera's update, where the wardrobe dresses (decision 65)."""
    state["hooks"][wardrobe.IDENTIFIER].fn()


check("eight at most, its own hook on the animation update", team_module.MOST == 8
      and team_module.IDENTIFIER == "characters:companions"
      and animation_hook.HOOK == "/Script/Engine.AnimInstance:BlueprintUpdateAnimation")
check("ranks shifted by an eighth of a second each", team_module.offset(0, 1.0) == 0.0
      and team_module.offset(3, 1.0) == 0.375)
game = fake.Game(state)
clock = fake.Clock()
births = fake.Births(game)
team = team_module.Team(clock, births)
check("none chosen: nothing called, no hook", team.start([]) == "empty" and not team.respawns.pending()
      and team_module.IDENTIFIER not in animation_hook.beats())
check("started: each called, the hook set, said", team.start(["Abomination", "Nobody", "Crankus"]) == "started"
      and [line["companion"] for line in notes("companion_called")] == ["Abomination", "Crankus"]
      and team_module.IDENTIFIER in animation_hook.beats()
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
check("one dead: out of the team, coming back after the starting wait, no mod's given", [
      one.definition for one in team.active()] == [CRANKUS] and team.respawns.pending()
      and notes("companion_dead")[-1]["back_in_s"] == tuning.STARTING.back_after_s == 45.0)
beat(team, clock, 147.0)
check("not born again before 45 s", births.asked == [ABOMINATION, CRANKUS])
beat(team, clock, 148.0)
beat(team, clock, 149.0)
check("born again 45 s later, followed again, its rank free again", births.asked[-1] == ABOMINATION
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
      and team.active() == [] and not team.respawns.pending() and team_module.IDENTIFIER not in animation_hook.beats()
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
    hunters._dress(lemmy, "Rafa", "Rafa", "own")
late = team_module.Team(clock, births)
late.start(["Crankus"])
late._dress(game.companion(90, definition=LEMMY), "Rafa", "Rafa", "own")
clock.now += wardrobe.START_WAIT_S + 1.0
late.beat()
check("the team's beat forgets a hunter the camera's update never came for, said", late.wardrobe.waiting == []
      and notes("companion_dressing")[-1]["done"] == "camera_never_came")
late.stop("stopped")
check("the hunters waiting to be dressed: MOST at most, the latest kept", [
      held[0] for held in hunters.wardrobe.waiting] == [str(lemmy.Name) for lemmy in many_lemmys[-team_module.MOST:]])


picked = team_module.Team(clock, births)
GOD = fake.LEVELS["God"]
given = {"Crankus": GOD._replace(shield=0.0, speed=1.3, back_after_s=20.0)}
picked.start(["Crankus", "Abomination"], lambda name: given.get(name, GOD))
check("each given what its mod gives, said at the start with what chose it", notes("team_start")[-1]["tuning"] == {
      "Crankus": [12.0, 0.0, 45.0, 1.3, 20.0, "own", "God", "normal"],
      "Abomination": [12.0, 0.3, 45.0, 1.2, 45.0, "own", "God", "normal"]})
beat(picked, clock, 400.0)
beat(picked, clock, 401.0)
crankus = picked.active()[0]
check("its follow given it", crankus.tuned == given["Crankus"] and crankus.pace.factor == 1.3)
crankus.actor().HealthState.bCurrentlyDead = True
beat(picked, clock, 402.0)
check("dead: back after the wait its mod gives it, 20 s", notes("companion_dead")[-1]["back_in_s"] == 20.0)
for moment in range(422, 426):
    beat(picked, clock, float(moment))
check("back 20 s after its death, with the same", [one.tuned for one in picked.active()
                                                   if one.definition == CRANKUS] == [given["Crankus"]])
picked.stop("stopped")
check("what a mod gives out of its bounds: brought within them", picked.tuning_of("Crankus") == given["Crankus"]
      and (setattr(picked, "tuned", lambda name: GOD._replace(times=99.0)), picked.tuning_of("Vex").times)[1] == 20.0)
picked.tuned = lambda name: 1 / 0
check("a mod whose reading fails: the starting values, said", picked.tuning_of("Vex") is tuning.STARTING
      and notes("companion_tuning_failed")[-1] == {"event": "companion_tuning_failed", "run": 0, "companion": "Vex",
                                                    "error": "ZeroDivisionError"})
painted = team_module.Team(clock, births)
painted._dress(types.SimpleNamespace(Name="Char_GunToter_Shatter2_Lemmy_9"), "Vex", "Vex", "player")
check("the player's colours given: dressed with them", Dressing.made[-1].own is team_module._player_own)
painted._dress(types.SimpleNamespace(Name="Char_GunToter_Shatter2_Lemmy_8"), "Vex", "Vex", "own")
check("his own outfit given: dressed without them", Dressing.made[-1].own is None)
real_paint = team_module.player_paint
team_module.player_paint = types.SimpleNamespace(of=lambda pc: {"of": pc})
check("the player's colours and head read from the player's controller", team_module._player_own() == {
      "of": team_module.get_pc()})
team_module.player_paint = real_paint

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

menu["shown"] = False
elsewhere = team_module.Team(clock, births, end=ends.append, menu=menu_read)
elsewhere.start(["Crankus"])
asked_before, reads_before, ends_before = len(births.asked), menu["reads"], list(ends)
clock.now = 800.0
worker = threading.Thread(target=lambda: (animation_hook.beats()[team_module.IDENTIFIER](),
                                          animation_hook.beats()[team_module.IDENTIFIER]()))
worker.start()
worker.join(5)
check("a beat on another thread than the game's: nothing asked, nothing read, said once (trial 206)",
      len(births.asked) == asked_before and menu["reads"] == reads_before and ends == ends_before
      and notes("hook_off_thread")[-1]["what"] == "team" and len(notes("hook_off_thread")) == 1)
beat(elsewhere, clock, 801.0)
check("the next beat on the game's thread: the companion asked", len(births.asked) == asked_before + 1)
elsewhere.stop("stopped")
check("the beats on another thread counted at the stop", notes("team_stop")[-1]["off_thread"] == 2)

owners.reset_for_tests()
owners.join("other_mod", first=True)
led = team_module.Team(clock, births, end=ends.append, menu=menu_read)
check("another mod leading: not started, nothing called, no hook, said", led.start(["Crankus"]) == "elsewhere"
      and not led.respawns.pending() and led.hook is None
      and (notes("team_elsewhere")[-1]["leads"], notes("team_elsewhere")[-1]["at"]) == ("other_mod", "start"))
owners.reset_for_tests()
owners.join(team_module.OWNER)
check("this mod leading: started", led.start(["Crankus"]) == "started")
beat(led, clock, 900.0)
ends_before, reads_before = list(ends), menu["reads"]
owners.join("other_mod", first=True)
beat(led, clock, 900.5)
check("another coming to lead: nothing asked before MENU_EVERY_S", ends == ends_before)
beat(led, clock, 901.0)
check("then its owner asked to stop it, the menu not read, said", ends == [*ends_before, "elsewhere"]
      and menu["reads"] == reads_before and notes("team_elsewhere")[-1]["at"] == "beat")
led.stop("elsewhere")
owners.reset_for_tests()
nobody = team_module.Team(clock, births, end=ends.append, menu=menu_read)
check("no mod joined at all: started, as before the owners existed", nobody.start(["Crankus"]) == "started")
nobody.stop("stopped")

owners.reset_for_tests()
other_stops: list = []
owners.claim("other_mod", lambda: other_stops.append("stopped"))
first = team_module.Team(clock, births, end=ends.append, menu=menu_read)
check("another mod's team still running when this one starts: stopped first, said (review of 23 October 2026)",
      first.start(["Crankus"]) == "started" and other_stops == ["stopped"]
      and notes("team_start")[-1]["stopped"] == ["other_mod"])
ends_before = list(ends)
check("this one running, another mod's team starting: this one stopped at once, its owner asked, its hook removed",
      owners.claim("other_mod", lambda: None) == [team_module.OWNER] and ends == [*ends_before, "elsewhere"]
      and first.ended == "elsewhere" and first.hook is None
      and notes("team_elsewhere")[-1]["at"] == "claim")
owners.reset_for_tests()
second = team_module.Team(clock, births, end=ends.append, menu=menu_read)
second.start(["Crankus"])
second.stop("stopped")
check("a team stopped: its claim released, nothing left to stop", owners.claim("other_mod", lambda: None) == [])
owners.reset_for_tests()

strays_module = team_module.strays
strays_module.reset_for_tests()
asking = team_module.Team(clock, births, end=ends.append, menu=menu_read)
asking.start(["Crankus", "Abomination"])
beat(asking, clock, 1000.0)
check("one asked of its spawner, not found yet", len(asking.respawns.asked()) == 1)
asking.stop("stopped")
check("the stop hands it to the strays' watch, its own hook named after the mod", team_module.STRAYS_IDENTIFIER
      == "characters:companions_strays" and team_module.STRAYS_IDENTIFIER in animation_hook.beats()
      and [one["companion"] for one in strays_module._watch["strays"].looked] == ["Crankus"])
forgotten: list = []
real_forget = strays_module.forget
strays_module.forget = forgotten.append
again = team_module.Team(clock, births, end=ends.append, menu=menu_read)
again.start(["Crankus"])
beat(again, clock, 1050.0)
strays_module.forget = real_forget
check("each spawner a team asks: watched no more as a stray's, what it bears being this team's",
      forgotten == [f"OakSpawner_{births.number}"])
again.stop("stopped")
strays_module.reset_for_tests()
at_menu = team_module.Team(clock, births, end=ends.append, menu=menu_read)
at_menu.start(["Crankus"])
beat(at_menu, clock, 1100.0)
at_menu.stop("main_menu")
check("at the main menu: none looked for, the world goes with them", team_module.STRAYS_IDENTIFIER
      not in animation_hook.beats() and strays_module._watch["strays"] is None)

rested = team_module.Team(clock, births, end=ends.append, menu=menu_read)
rested.start(["Crankus"])
beat(rested, clock, 2000.0)
check("after a beat with work: due at its parts' earliest time, REST_MOST_S at most",
      2000.0 < rested.due <= 2000.0 + team_module.REST_MOST_S
      and rested.due == min(rested._next_due(), 2000.0 + team_module.REST_MOST_S))
idle = rested.gauge.calls.idle_calls
asked_before = list(births.asked)
beat(rested, clock, rested.due - 0.001)
check("before it, a call does nothing, counted as such", rested.gauge.calls.idle_calls == idle + 1
      and births.asked == asked_before)
state["info"].clear()
for moment in range(1, 32):
    beat(rested, clock, 2000.0 + moment)
said = notes("team_status")
check("every 30 s, what its beat costs", len(said) == 1 and said[0]["following"] == 1
      and {"hook_calls_s", "hook_idle_us", "worked_s", "busy_ms_s", "longest_ms", "fps", "fps_low"} <= set(said[0]))
parts = said[0].get("parts_ms_s", {})
check("each of its parts apart, a second's time and the longest (trial 221)",
      set(parts) == set(said[0].get("parts_longest_ms", {}))
      and {"follow_sample", "sample_read", "sample_fight", "sample_catch", "sample_walk", "wardrobe",
           "respawns"} <= set(parts)
      and all(value >= 0.0 for value in parts.values())
      and sum(parts.values()) <= said[0]["busy_ms_s"] + 0.01)
rested.stop("stopped")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
