"""Speed FOV (Kevin, 2026-10-06): walking changes nothing; a sprint or a slide adds the gain; the air and the game's
own moves after them keep it, whatever their speed; walking or aiming ends it; the gain follows the player down as he
slows, read ahead along the braking; the view starts with no jolt, never turns back abruptly, settles without a bump;
one log line per change."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import speed_fov as sf  # noqa: E402
from apex_camera_runtime import player_sample as sample_module  # noqa: E402
from apex_camera_runtime.player_sample import Sample
from apex_camera_runtime.speed_fov import SpeedFov, why  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def state(speed, sprinting=False, sliding=False, in_air=False, driven=False, aiming=False):
    return Sample(sprinting, sliding, in_air, driven or sliding, speed, aiming)


ON = (True, 10.0, 0.4)
FRAME = 16_666_667
WALK = state(540.0)
SPRINT = state(1269.0, sprinting=True)
SLIDE = state(1130.0, sliding=True)
AIR = state(1300.0, in_air=True)
DASH = state(1500.0, driven=True)
AIM = state(300.0, aiming=True)


def run(speed, sample, seconds, values=ON, start=0, trace=None):
    now = start
    for _ in range(round(seconds * 60)):
        now += FRAME
        gain = speed.update(values, sample, now)
        if trace is not None:
            trace.append(gain)
    return now


def steps(trace):
    return [b - a for a, b in zip(trace, trace[1:])]


def full(speed):
    return abs(speed.gain - 10.0) < 1e-9


speed = SpeedFov()
now = run(speed, WALK, 2)
check("walking never widens the view", speed.gain == 0.0 and not speed.running and not speed.moved)
start = []
now = run(speed, SPRINT, 0.4, start=now, trace=start)
check("the sprint's start reaches 95 % of the gain in the setting's seconds", 9.4 < start[-1] < 9.7)
check("it starts with no jolt: the first frame moves it by about a hundredth of the gain, then more each frame",
      start[0] < 0.2 and start[1] - start[0] > start[0] and start[2] - start[1] > start[1] - start[0])
now = run(speed, SPRINT, 1, start=now)
check("then it settles exactly on the setting", full(speed) and not speed.moved)
now = run(speed, SLIDE, 1, start=now)
check("a slide slower than the sprint keeps it all: Kevin's slide (1130) against his sprint (1269)", full(speed))
now = run(speed, AIR, 1, start=now)
check("a jump or the grapple keeps it", full(speed))
now = run(speed, state(2000.0, sprinting=True, in_air=True), 0.3, start=now)
landing = []
now = run(speed, SPRINT, 0.5, start=now, trace=landing)
check("landing after a fast fall never narrows it: the air's speed is not the sprint's", min(landing) > 9.99)
now = run(speed, DASH, 0.5, start=now)
check("a dash keeps it", full(speed))
now = run(speed, state(1200.0), 0.2, start=now)
check("a few frames on the ground keep it: the game's slide starts a frame or two after the sprint ends",
      speed.running and full(speed))
now = run(speed, state(1200.0), 0.3, start=now)
check("on the ground, out of any run for a quarter second, the run is over at any speed", not speed.running)
now = run(speed, WALK, 1.5, start=now)
check("the view comes back and settles at exactly nothing", speed.gain == 0.0)
now = run(speed, AIR, 1, start=now)
check("a jump that did not start from a sprint or a slide changes nothing", speed.gain == 0.0)
now = run(speed, DASH, 1, start=now)
check("a dash from walking changes nothing", speed.gain == 0.0)

speed = SpeedFov()
now = run(speed, SLIDE, 1.5)
check("a slide without a sprint widens the view too (Kevin, after the second test)", speed.running and full(speed))

speed = SpeedFov()
now = run(speed, SPRINT, 1.5)
braking = []
for frame in range(20):
    now = run(speed, state(1269.0 * (1 - (frame + 1) / 20), sprinting=True), 1 / 60, start=now, trace=braking)
after = []
now = run(speed, state(0.0, sprinting=True), 0.2, start=now, trace=after)
check("braking to a stop in a third of a second leaves under a quarter of the gain when the player stands still",
      braking[-1] < 2.5)
check("then it settles softly, within a fifth of a second", after[-1] < 0.5)
check("no bump: the view only ever narrows while the player brakes and stands",
      all(step <= 1e-12 for step in steps(braking + after)))
check("and it slows down as it lands: its last steps shrink", abs(steps(after)[-1]) < abs(steps(after)[0]))
now = run(speed, state(1269.0, sprinting=True), 1.5, start=now)
check("speeding up again widens it again", speed.gain > 9.9)

speed = SpeedFov()
now = run(speed, SPRINT, 1.5)
hammered = []
for press in range(8):
    sample = SPRINT if press % 2 else state(0.0)
    now = run(speed, sample, 0.15, start=now, trace=hammered)
moves = steps(hammered)
check("hammering the key never turns the view back abruptly: no frame's change differs from the last by much",
      max(abs(b - a) for a, b in zip(moves, moves[1:])) < 0.25)

speed = SpeedFov()
now = run(speed, SPRINT, 1.5)
wall = []
now = run(speed, state(0.0, sprinting=True), 2 / 60, start=now, trace=wall)
check("a wall's sudden stop never snaps the view in one frame", wall[0] > 9.0)

speed = SpeedFov()
now = run(speed, state(10.0, sprinting=True), 0.1)
check("a sprint from a standstill starts with the whole gain ahead", speed.follow > 0.99)

speed = SpeedFov()
now = run(speed, SPRINT, 1.5)
now = run(speed, AIM, 1.5, start=now)
check("aiming takes the gain away", speed.gain == 0.0 and not speed.running)

speed = SpeedFov()
now = run(speed, SPRINT, 1.5)
now = run(speed, SPRINT, 0.2, values=(False, 10.0, 0.4), start=now)
check("switching it off brings the view back smoothly, not in one jump", 1.0 < speed.gain < 9.0 and not speed.running)
check("the ceiling stays the gain's setting while it comes back", speed.ceiling == 10.0)
now = run(speed, SPRINT, 3, values=(True, 20.0, 1.0), start=now)
check("the gain and the seconds are the player's", abs(speed.gain - 20.0) < 1e-9)

speed = SpeedFov()
speed.update(ON, SPRINT, 0)
speed.update(ON, SPRINT, 10_000_000_000)
check("a long frame (loading) moves the view at most half way", 0.0 < speed.gain < 5.0)
check("the log names the state", why(AIR) == "air at 1300" and why(SLIDE) == "slide at 1130"
      and why(DASH) == "game move at 1500" and why(AIM) == "aiming at 300" and why(WALK) == "ground at 540")
speed.reset()
check("reset forgets the run and the gain", speed.gain == 0.0 and not speed.running)


class Settings:
    def __init__(self, values=None):
        self.notes = []
        if values is not None:
            self.speed_fov = lambda: values

    def note(self, message):
        self.notes.append(message)


class Pc:
    pass


samples = []
original_read = sample_module.read
sample_module.read = lambda pc: samples.append(pc) or SPRINT
try:
    speed, settings = SpeedFov(), Settings(ON)
    for frame in range(30):
        sf.step(speed, settings, Pc(), frame * FRAME)
    check("one line when the view starts widening, none per frame",
          settings.notes == ["speed FOV widening: sprint at 1269"])
    samples.clear()
    old = Settings()
    check("a mod without the option never widens and reads nothing",
          sf.step(SpeedFov(), old, Pc(), 0) == 0.0 and not samples and old.notes == [])
    sf.step(SpeedFov(), Settings((False, 10.0, 0.4)), Pc(), 0)
    check("switched off and at rest, the player is not read", not samples)
    sample_module.read = lambda pc: None
    speed, settings = SpeedFov(), Settings(ON)
    speed.running = True
    sf.step(speed, settings, None, 0)
    check("no player (loading, title screen) ends the run", settings.notes == ["speed FOV back: no player"])
finally:
    sample_module.read = original_read

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
