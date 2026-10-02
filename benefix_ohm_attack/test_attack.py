"""Tests the attack frame by frame: the key held raises the hand, lights the beam and hits on its beat, anything else
puts the beam out and lowers the hand."""

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
check("the log says the element, the level, what raised the hand and the view, then who was hit first and how far",
      state["log"][-2:] == ["[Benefix Ohm Attack] beam on, Fire, level 1, hand raised on arms and body, first person",
                            "[Benefix Ohm Attack] hit Char_Psycho at 5 m"])
check("the ray looks a kilometre ahead: the beam has no range setting", state["traced"][-1].X == settings.REACH == 100000.0
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
      state["log"][-1] == "[Benefix Ohm Attack] beam off, energy 60, effect active True, radius 2500")
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
check("and the log says why, before the beam's last line",
      state["log"][-2] == "[Benefix Ohm Attack] no frame for 60.0 s: the shot ends and the key is forgotten"
      and "] beam off, " in state["log"][-1])
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

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
