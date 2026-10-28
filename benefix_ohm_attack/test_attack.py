"""Tests the attack frame by frame: the key held raises the hand, lights the beam and hits on its beat, anything else
puts the beam out and lowers the hand."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
import benefix_ohm_attack  # noqa: E402
from benefix_ohm_attack import attack, keys, settings  # noqa: E402

fails: list[str] = []
PRESSED, RELEASED = "EInputEvent.IE_Pressed", "EInputEvent.IE_Released"
PALM = (10.0, -20.0, 40.0)
WINDOW = "benefix_ohm_attack.control_window"
now = 0.0


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def run(seconds: float, step: float = 0.05) -> None:
    """Runs the game for that long, a frame every step."""
    global now
    for _ in range(round(seconds / step)):
        now += step
        attack.on_frame(now)


def frame_after(seconds: float) -> None:
    """One frame, that long after the last one."""
    global now
    now += seconds
    attack.on_frame(now)


def press() -> None:
    keys.keyboard_bind.callback(PRESSED)


def let_go() -> None:
    keys.keyboard_bind.callback(RELEASED)
    run(0.1)


def last_on() -> str:
    """The log's line for the last shot begun."""
    return next(line for line in reversed(state["log"]) if "] beam on, " in line)


def fresh(energy: float = 100.0) -> None:
    """A clean start between two scenarios: nothing held, nothing owed in hits, that much energy."""
    attack.stop()
    run(0.05)
    attack.energy.left, attack.energy.shut = energy, False


mod = state["mods"][0]
check("the attack loads without the window: a window that cannot load must not take the beam down", WINDOW not in sys.modules)
pc, character = sdk_stubs.player(state, level=1)
enemy = sdk_stubs.aim_at(state, "Char_Psycho_7", distance=500.0)
run(1.0)
arms = state["arms_animation"]
check("without the key nothing is lit, nothing is hit and the hand stays down",
      state["spawns"] == [] and state["hits"] == [] and arms.played == [])

press()
run(0.15)
check("the key held lights one beam from the left hand at once", len(state["spawns"]) == 1 and state["spawns"][0][2] == PALM)
check("its first hit waits for a fifth of a second of beam", state["hits"] == [])
run(0.05)
check("and comes then", len(state["hits"]) == 1)
run(0.8)
check("the hand is raised once, before the beam is lit",
      len(arms.played) == 1 and state["events"].index("HAND UP") < state["events"].index("LIT"))
check("the body seen from outside takes its pose at the same shot", len(state["body_animation"].played) == 1)
check("the log says what the game said of the enemy the first time it was asked, then the element, the level, what "
      "raised the hand and the view, who was hit first and how far, and who was locked",
      state["log"][-5:] == ["[Benefix Ohm Attack] first attitude asked, towards Char_Psycho",
                            "[Benefix Ohm Attack] the game answered <ETeamAttitude.hostile: 2>",
                            "[Benefix Ohm Attack] beam on, Fire, level 1, hand raised on arms and body, first person",
                            "[Benefix Ohm Attack] hit Char_Psycho at 5 m",
                            "[Benefix Ohm Attack] lock on Char_Psycho at 5 m"])
check("the ray looks a kilometre ahead: the beam has no range setting",
      max(end.X for end in state["traced"]) == settings.REACH == 100000.0
      and all(option.identifier != "range" for option in settings.ALL))
check("the first hit is said once per shot", sum("] hit " in line for line in state["log"]) == 1)
check("it follows the aim at every frame", len(state["beams"][0].poses) == 20)
check("it hits five times a second of beam", len(state["hits"]) == 5)
check("each hit is a fifth of the damage per second, on the enemy, as fire",
      abs(state["hits"][0]["DamageOverride"] - 15.0) < 1e-6 and state["hits"][0]["DamageTarget"] is enemy
      and state["hits"][0]["DamageTypeOverride"][2] == "Fire")
check("firing drains the beam's own energy", abs(attack.energy.left - 80.0) < 1e-6)

sdk_stubs.aim_at(state, "StaticMeshActor_3", distance=900.0)
run(1.0)
check("on a wall the beam stays on and hits nothing", len(state["hits"]) == 5 and state["events"].count("OFF") == 0)

keys.keyboard_bind.callback(RELEASED)
run(0.5)
check("letting go puts the beam out, removes it and lowers the hand", state["events"][-3:] == ["OFF", "REMOVED", "HAND DOWN"])
check("the log says the energy left and what the game said of the effect, read before it was removed",
      state["log"][-2] == "[Benefix Ohm Attack] beam off, energy 60, effect active True, radius 2500")
check("then what the shot did: how long the aim was on an enemy, how long the lock held and how far the aim "
      "strayed, among how many foes and with which settings",
      state["log"][-1] == "[Benefix Ohm Attack] shot 2.00 s: on an enemy 1.00 s under the aim and 0.00 s caught "
                          "beside it; locked 0.80 s, the aim up to 0 degrees away; 0 foes known; catch 200 cm, lock "
                          "after 0.20 s broken at 30 degrees, bounce on")
check("and the body's arm with it", state["body_animation"].stopped == [(0.25, "a body montage")])
left = attack.energy.left
run(1.4)
check("the energy waits for its delay", attack.energy.left == left)
run(1.0)
check("then comes back", attack.energy.left > left)

sdk_stubs.aim_at(state, "Char_Psycho_7", distance=500.0)
settings.damage.value, settings.element.value = 100, "Shock"
pc.PlayerState.ExperienceState[1].ExperienceLevel = 3
hits = len(state["hits"])
press()
run(0.3)
check("the element and the level of the moment decide the hit",
      state["hits"][hits]["DamageTypeOverride"][2] == "Shock" and abs(state["hits"][hits]["DamageOverride"] - 23.762) < 1e-3
      and state["spawns"][-1][1] == "a loaded beam")
let_go()

# A name the menu no longer offers, however it got into the option: the default element is fired.
for menu_name, said, damage_type in (("Kinetic", "Kinetic", "Normal"), ("KineticB", "Fire", "Fire"),
                                     ("Plasma", "Fire", "Fire")):
    settings.element.value = menu_name
    hits = len(state["hits"])
    press()
    run(0.3)
    check(f"the menu's {menu_name}: the log names the element fired, {said}, and the hit is {damage_type} damage",
          f"] beam on, {said}, level " in last_on() and state["hits"][hits]["DamageTypeOverride"][2] == damage_type)
    let_go()
settings.element.value = "Shock"

fresh()
hits, spawns = len(state["hits"]), len(state["spawns"])
for _ in range(20):
    press()
    run(0.05)
    keys.keyboard_bind.callback(RELEASED)
    run(0.05)
check("a key tapped earns its hits as it pays its energy: twenty taps of one frame hit as one second of beam does",
      len(state["spawns"]) == spawns + 20 and len(state["hits"]) == hits + 5 and abs(attack.energy.left - 80.0) < 1e-6)

fresh()
settings.drain.value = 0
hits = len(state["hits"])
press()
run(9.0, step=0.03)
check("the beat keeps what a frame leaves over: forty-five hits in nine seconds, in frames no number of which makes "
      "a beat", len(state["hits"]) == hits + 45)
let_go()
settings.drain.value = 20

fresh(5.0)
spawns = len(state["spawns"])
press()
run(0.5)
check("an emptied reserve puts the beam out and lowers the hand", attack.energy.left == 0.0
      and len(state["spawns"]) == spawns + 1 and state["events"][-2:] == ["REMOVED", "HAND DOWN"])
run(4.5)
check("and the held key does not relight it, however much energy has come back",
      attack.energy.left > 20.0 and len(state["spawns"]) == spawns + 1)
let_go()
press()
run(0.1)
check("a new press does", len(state["spawns"]) == spawns + 2)
let_go()

fresh(3.0)
spawns = len(state["spawns"])
press()
run(0.2)
check("a press on a reserve that cannot pay for one hit lights nothing", len(state["spawns"]) == spawns)
attack.energy.left = 50.0
run(0.2)
check("and the key still held does not light the beam when the energy is there: a shot begins at a press",
      len(state["spawns"]) == spawns)
let_go()
press()
run(0.1)
check("the next press does", len(state["spawns"]) == spawns + 1)

state["pc"].OakCharacter = None
run(0.1)
check("no character on foot puts the beam out, lowers the hand and forgets the key",
      state["events"][-2:] == ["REMOVED", "HAND DOWN"] and not keys.held())
state["pc"].OakCharacter = character

fresh()
press()
run(0.1)
state["beams"][-1].refuses_target = True
hits, removed = len(state["hits"]), state["events"].count("REMOVED")
run(0.9)
check("a beam that fails goes out, and the hits go on without it",
      state["events"].count("REMOVED") == removed + 1 and len(state["hits"]) > hits)
spawns = len(state["spawns"])
run(0.5)
check("a failed beam is not asked for again at every frame", len(state["spawns"]) == spawns)
let_go()

press()
run(0.1)
state["trace"] = None
errors, removed = len(state["errors"]), state["events"].count("REMOVED")
run(0.2)
check("an error in a frame ends the shot, says so once, lowers the hand and forgets the key",
      len(state["errors"]) == errors + 1 and not keys.held() and state["events"].count("REMOVED") == removed + 1
      and state["events"][-1] == "HAND DOWN")
sdk_stubs.aim_at(state, "Char_Psycho_7")

fresh()
sockets = dict(state["sockets"])
state["sockets"].clear()
press()
run(0.1)
check("a hand that cannot be read: the beam leaves from beside the camera", state["spawns"][-1][2] != PALM)
let_go()
state["sockets"].update(sockets)
press()
run(0.1)
check("each new shot looks for the hand again", state["spawns"][-1][2] == PALM)
let_go()

fresh()
state["hit_raises"] = RuntimeError("the game refuses")
errors, calls, lines = len(state["errors"]), len(state["hits"]), len(state["log"])
press()
run(0.5)
let_go()
check("a hit the game refuses is said once as an error, and never as a hit: a line of the log is a proof",
      len(state["errors"]) == errors + 1 and len(state["hits"]) == calls + 1
      and not any("] hit " in line for line in state["log"][lines:]))
press()
run(0.5)
check("it is not tried again, and each shot's line says the beam deals no damage",
      len(state["hits"]) == calls + 1 and last_on().endswith("first person, no damage: the game refused a hit"))
let_go()
state["hit_raises"] = None
benefix_ohm_attack.damage.forget()

fresh()
press()
run(0.1)
left, removed = attack.energy.left, state["events"].count("REMOVED")
frame_after(0.4)
check("a frame of four tenths of a second is a hitch: it drains as a quarter second, and the shot goes on",
      abs(left - attack.energy.left - 5.0) < 1e-6 and keys.held() and state["events"].count("REMOVED") == removed)
frame_after(60.0)
check("no frame for a minute is a pause or a loading: the shot ends, the hand comes down and the key is forgotten",
      not keys.held() and state["events"][-2:] == ["REMOVED", "HAND DOWN"])
check("and the log says why, before the beam's last lines",
      state["log"][-3] == "[Benefix Ohm Attack] no frame for 60.0 s: the shot ends and the key is forgotten"
      and "] beam off, " in state["log"][-2] and "] shot " in state["log"][-1])
hits, spawns = len(state["hits"]), len(state["spawns"])
run(1.0)
check("nothing fires by itself afterwards", len(state["hits"]) == hits and len(state["spawns"]) == spawns)
attack.energy.shut = True
press()
lines = len(state["log"])
frame_after(60.0)
check("a key held with no beam lit is forgotten the same way", not keys.held() and "] no frame for " in state["log"][lines])

fresh()
press()
run(0.1)
mod.on_disable()
check("switching the mod off puts the beam out, lowers the hand and forgets the key",
      state["events"][-2:] == ["REMOVED", "HAND DOWN"] and not keys.held())
check("the hand went up as many times as it came down", state["events"].count("HAND UP") == state["events"].count("HAND DOWN"))

fresh()
arms.refuses = True
errors, spawns, hits = len(state["errors"]), len(state["spawns"]), len(state["hits"])
press()
run(0.5)
check("arms that refuse the pose: the beam fires all the same, said once, and the log says only the body raised it",
      len(state["spawns"]) == spawns + 1 and len(state["hits"]) > hits and len(state["errors"]) == errors + 1
      and last_on().endswith("hand raised on body, first person"))
let_go()

state["body_animation"].refuses = True
press()
run(0.1)
check("arms and body both refusing: the log says the hand is down", last_on().endswith("hand down, first person"))
let_go()
arms.refuses = state["body_animation"].refuses = False

state["camera_mode"] = "ThirdPerson"
fresh()
press()
run(0.1)
check("in third person the beam leaves the body's left hand, and the log says the view",
      state["spawns"][-1][2] == (30.0, -15.0, 120.0)
      and last_on().endswith("hand raised on arms and body, third person"))
let_go()
state["camera_mode"] = "Default"

fresh()
window = types.SimpleNamespace(active=lambda: False)
sys.modules[WINDOW] = window
press()
run(0.1)
removed = state["events"].count("REMOVED")
window.active = lambda: True
run(0.05)
check("the mod's window opening ends the shot and forgets the key: it takes the keyboard, the release may never come",
      not keys.held() and state["events"].count("REMOVED") == removed + 1)
spawns = len(state["spawns"])
press()
run(0.1)
check("and no key fires while it is open", len(state["spawns"]) == spawns and not keys.held())
window.active = lambda: False
press()
run(0.1)
check("once it is closed a press fires again", len(state["spawns"]) == spawns + 1)
let_go()
del sys.modules[WINDOW]

fresh()
press()
run(0.1)
removed = state["events"].count("REMOVED")
frame_after(0.45)
check("just under half a second without a frame is still a hitch: the shot goes on",
      keys.held() and state["events"].count("REMOVED") == removed)
frame_after(0.55)
check("just over it ends the shot and forgets the key", not keys.held() and state["events"].count("REMOVED") == removed + 1)
lines = len(state["log"])
frame_after(60.0)
check("a gap with no beam lit and no key held is nothing to say", len(state["log"]) == lines)

fresh()
hits = len(state["hits"])
press()
for _ in range(8):
    frame_after(0.4)
check("a frame longer than the beat hits once, not twice", len(state["hits"]) == hits + 8)
hits = len(state["hits"])
run(0.2)
check("and what such frames leave over is kept up to one beat, no more", len(state["hits"]) == hits + 2)
let_go()

fresh()
sdk_stubs.aim_at(state, "StaticMeshActor_3", distance=900.0)
press()
run(0.2)
sdk_stubs.aim_at(state, "Char_Psycho_7")
hits = len(state["hits"])
run(0.05)
check("the beat goes on while the beam is on a wall: no hit is saved up for the enemy that comes next",
      len(state["hits"]) == hits)
let_go()

settings.drain.value = 100
fresh(19.0)
spawns = len(state["spawns"])
press()
run(0.1)
check("a shot's price is one hit at the spending of the moment: at 100 a second, 19 of energy light nothing",
      len(state["spawns"]) == spawns)
let_go()
fresh(21.0)
press()
run(0.05)
check("and 21 do", len(state["spawns"]) == spawns + 1)
let_go()

# The SDK's own console menu writes whatever number the player types into a slider.
settings.drain.value = 500
fresh()
press()
run(0.5)
check("a slider is read within its bounds whatever wrote it: 500 a second spends as the slider's 100",
      abs(attack.energy.left - 50.0) < 1e-6)
let_go()
settings.drain.value = 20
settings.regen.value, settings.regen_delay.value = 0, float("nan")
fresh(50.0)
run(3.0)
check("a recharge of nothing and a delay that is no number, written the same way, still give the energy back",
      attack.energy.left > 50.0)
settings.regen.value, settings.regen_delay.value = 25, 2.0
settings.damage.value = float("inf")
fresh()
hits = len(state["hits"])
press()
run(0.25)
check("and an endless damage hits as the slider's highest", len(state["hits"]) == hits + 1
      and state["hits"][-1]["DamageOverride"] == benefix_ohm_attack.strength.per_hit(2000.0, 3, 5.0))
let_go()
settings.damage.value = 100

# The lock, the catch and the bounce (2026-10-02), in a world that holds several things at once.
psycho = sdk_stubs.Actor("Char_Psycho_4", (1000.0, 0.0, 50.0))
brute = sdk_stubs.Actor("Char_Brute_9", (1000.0, 500.0, 50.0))
ON_PSYCHO = (960.0, 0.0, 50.0)


def lock_lines(since: int) -> list[str]:
    return [line.removeprefix("[Benefix Ohm Attack] ") for line in state["log"][since:]
            if "] lock " in line or "] bounce " in line]


def beam_end(which: int = -1) -> tuple:
    return state["beams"][which].targets[-1][1]


# A catch of 20 cm, the weapon's own: these scenes move the aim a few degrees off an enemy 10 m away, which the
# default catch of 2 m would bring back onto him.
settings.drain.value, settings.bounce.value, settings.width.value = 0, False, 20
sdk_stubs.world(state, (psycho, 40.0))
state["all"]["OakCharacter"] = [character, psycho]
fresh()
lines, spawns = len(state["log"]), len(state["spawns"])
press()
run(0.3)
check("the beam held on an enemy locks on it after its two tenths of a second, said in the log",
      lock_lines(lines) == ["lock on Char_Psycho at 10 m"] and beam_end() == ON_PSYCHO)
state["look"] = (0.0, 10.0)
hits = len(state["hits"])
run(1.0)
check("the aim strays ten degrees: the beam stays on him", beam_end() == ON_PSYCHO and len(state["spawns"]) == spawns + 1)
check("and the hits go on, on him, where the ray to him lands",
      len(state["hits"]) == hits + 5 and all(sent["DamageTarget"] is psycho for sent in state["hits"][hits:])
      and benefix_ohm_attack.aim.hit_actor(state["hits"][-1]["TargetedHitInfo"]) is psycho)
psycho.at = (1000.0, 200.0, 50.0)
run(0.05)
check("he moves: the beam's end moves with him", beam_end() == (960.0, 200.0, 50.0))
psycho.at = (1000.0, 0.0, 50.0)
state["look"] = (0.0, 31.0)
hits = len(state["hits"])
run(0.5)
check("past the angle the lock lets go: the beam ends where the aim does, the hits stop, and the log says why",
      beam_end() != ON_PSYCHO and len(state["hits"]) == hits
      and lock_lines(lines) == ["lock on Char_Psycho at 10 m", "lock lost: aim 31 degrees away"])
let_go()
check("the shot's line says how long the lock held and how far the aim strayed while it did (he was under the aim "
      "for the first 0.30 s, and again for a frame when he walked under it)",
      state["log"][-1] == "[Benefix Ohm Attack] shot 1.85 s: on an enemy 0.35 s under the aim and 0.00 s caught "
                          "beside it; locked 1.15 s, the aim up to 10 degrees away; 1 foes known; catch 20 cm, lock "
                          "after 0.20 s broken at 30 degrees, bounce off")
state["look"] = (0.0, 0.0)
lines = len(state["log"])
press()
run(0.1)
state["look"] = (0.0, 10.0)
run(0.1)
check("a new shot starts with nobody locked: a contact of a tenth of a second is no lock",
      lock_lines(lines) == [] and beam_end() != ON_PSYCHO)
let_go()

settings.lock_angle.value, settings.lock_delay.value = 5, 0.0
state["look"] = (0.0, 0.0)
press()
run(0.05)
state["look"] = (0.0, 4.0)
run(0.05)
held = beam_end() == ON_PSYCHO
state["look"] = (0.0, 6.0)
run(0.05)
check("the window's two numbers are the lock's: at once and 5 degrees, the beam holds at 4 and lets go at 6",
      held and beam_end() != ON_PSYCHO)
let_go()
settings.lock_angle.value, settings.lock_delay.value = 30, 0.2

settings.lock.value = False
state["look"] = (0.0, 0.0)
lines = len(state["log"])
press()
run(0.5)
state["look"] = (0.0, 10.0)
hits = len(state["hits"])
run(0.5)
check("with the lock switched off the beam leaves the enemy with the aim, as before the lock, and nothing is said",
      beam_end() != ON_PSYCHO and len(state["hits"]) == hits and lock_lines(lines) == [])
let_go()
state["look"] = (0.0, 1.5)
rays = len(state["rays"])
press()
run(0.1)
check("an enemy under the aim is hit where the aim meets him, off his middle: the catch is not asked, one ray a frame",
      abs(beam_end()[1] - 25.4) < 0.1 and len(state["rays"]) == rays + 2)
let_go()
settings.lock.value = True

# The catch: an enemy 45 cm beside the aim's line, whose body is 15 cm from it.
beside = sdk_stubs.Actor("Char_Psycho_31", (800.0, 45.0, 50.0))
TO_SKIN = 1.0 - 40.0 / math.hypot(800.0, 45.0)
ON_BESIDE = (800.0 * TO_SKIN, 45.0 * TO_SKIN, 50.0)


def near(found, wanted):
    return all(abs(a - b) < 1e-6 for a, b in zip(found, wanted))


SETTINGS = "1 foes known; catch 20 cm, lock after 0.20 s broken at 30 degrees, bounce off"
sdk_stubs.world(state, (beside, 40.0))
state["all"]["OakCharacter"] = [character, beside]
benefix_ohm_attack.foes.restart()
state["look"] = (0.0, 0.0)
hits = len(state["hits"])
press()
run(0.25)
check("the beam catches an enemy 20 cm from the aim by default: one the aim's ray misses is caught, the beam ends "
      "on him and hits him", near(beam_end(), ON_BESIDE) and len(state["hits"]) == hits + 1
      and state["hits"][-1]["DamageTarget"] is beside)
rays = len(state["rays"])
run(0.5)
check("once he is locked nobody is looked for beside the aim: the lock holds him, with its one ray a frame",
      near(beam_end(), ON_BESIDE) and len(state["rays"]) == rays + 2 * 10)
let_go()
check("the shot's line says he was caught beside the aim",
      state["log"][-1] == "[Benefix Ohm Attack] shot 0.75 s: on an enemy 0.00 s under the aim and 0.25 s caught "
                          f"beside it; locked 0.55 s, the aim up to 3 degrees away; {SETTINGS}")
cover = sdk_stubs.Actor("StaticMeshActor_5", (400.0, 22.5, 50.0))
sdk_stubs.world(state, (beside, 40.0), (cover, 15.0))
hits = len(state["hits"])
press()
run(0.2)
let_go()
check("an enemy near the aim that a wall hides is not caught, and the shot's line says somebody was hidden",
      len(state["hits"]) == hits and state["log"][-1]
      == f"[Benefix Ohm Attack] shot 0.20 s: on no enemy; a foe beside the aim hidden 0.20 s; {SETTINGS}")
sdk_stubs.world(state, (beside, 40.0))
settings.width.value = 0
rays, hits = len(state["rays"]), len(state["hits"])
press()
run(0.5)
check("a catch of 0 is the aim alone, as before the catch: nobody looked for, he is missed",
      len(state["rays"]) == rays + 10 and len(state["hits"]) == hits)
let_go()
beside.at = (800.0, 400.0, 50.0)
settings.width.value = 300
hits = len(state["hits"])
press()
run(0.5)
missed = len(state["hits"]) == hits
let_go()
settings.width.value = 400
press()
run(0.5)
check("the catch reaches as far as its setting: an enemy 4 m beside the aim is missed at 300 cm and caught at 400",
      missed and len(state["hits"]) > hits and state["hits"][-1]["DamageTarget"] is beside)
let_go()
settings.width.value = 20

settings.bounce.value = True
benefix_ohm_attack.bounce.restart()
benefix_ohm_attack.foes.restart()
sdk_stubs.world(state, (psycho, 40.0), (brute, 40.0))
state["all"]["OakCharacter"] = [character, psycho, brute]
settings.element.value = "Shock"
lines, spawns, hits = len(state["log"]), len(state["spawns"]), len(state["hits"])
press()
run(1.0)
second_spot = beam_end()
check("with the bounce a second beam of the same element is lit, from the spot on the first enemy to the second",
      len(state["spawns"]) == spawns + 2 and state["spawns"][-1][2] == ON_PSYCHO
      and state["spawns"][-1][1] == state["spawns"][-2][1] and beam_end(-2) == ON_PSYCHO
      and abs(benefix_ohm_attack.bounce.math.dist(second_spot, brute.at) - 40.0) < 1e-6)
new = state["hits"][hits:]
check("each beat hits both: the same amount, the same element, each where its own ray landed",
      len(new) == 10 and [sent["DamageTarget"] for sent in new] == [psycho, brute] * 5
      and len({sent["DamageOverride"] for sent in new}) == 1
      and all(sent["DamageTypeOverride"][2] == "Shock" for sent in new)
      and benefix_ohm_attack.aim.hit_actor(new[1]["TargetedHitInfo"]) is brute)
check("the log says the lock and the bounce",
      lock_lines(lines) == ["bounce on Char_Brute, 5 m from the first", "lock on Char_Psycho at 10 m"])
removed = state["events"].count("REMOVED")
let_go()
check("letting go removes both beams", state["events"].count("REMOVED") == removed + 2)
check("the energy is the first beam's alone: the bounce costs nothing more", attack.energy.left == 100.0)

run(1.0)
settings.bounce.value = False
spawns, hits = len(state["spawns"]), len(state["hits"])
press()
run(1.0)
check("with the bounce switched off there is one beam and the first enemy alone is hit",
      len(state["spawns"]) == spawns + 1 and all(sent["DamageTarget"] is psycho for sent in state["hits"][hits:])
      and len(state["hits"]) == hits + 5)
let_go()
settings.bounce.value = True

run(1.0)
press()
run(0.5)
removed = state["events"].count("REMOVED")
mod.on_disable()
check("switching the mod off removes the bounce's beam with the shot's", state["events"].count("REMOVED") == removed + 2)
lines = len(state["log"])
mod.on_enable()
press()
run(0.5)
check("switched on anew, the mod starts over: nobody locked, the bounce looked for at once",
      lock_lines(lines) == ["bounce on Char_Brute, 5 m from the first", "lock on Char_Psycho at 10 m"])
let_go()
settings.drain.value, settings.element.value = 20, "Fire"
state["line"] = None

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
