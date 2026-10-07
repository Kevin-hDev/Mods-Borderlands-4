"""The shoulder state shows the side the automatic shoulder picks from room and view, and the key undoes a swap."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.shoulder import ShoulderState  # noqa: E402
from apex_camera_runtime.shoulder_auto import RETURN_S, SWAP_S, Values  # noqa: E402
from apex_camera_runtime.shoulder_clearance import Reading  # noqa: E402

fails = []
FRAME_NS = 16_666_667


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


SHOWN, OTHER = (0.0, 50.0, 0.0), (0.0, -50.0, 0.0)


class Clearance:
    def __init__(self):
        self.reading = None
        self.wanted = False

    def set(self, room, other_room):
        self.reading = Reading(room, other_room, SHOWN, None if other_room is None else OTHER)

    def take(self):
        return self.reading


class Sight:
    """Free view ahead by camera; a wall in front of the shown camera is a low share there."""
    def __init__(self, shown=1.0, other=1.0, fail=False):
        self.views = {SHOWN: shown, OTHER: other}
        self.fail = fail
        self.calls = 0

    def share(self, _actor, start, yaw):
        self.calls += 1
        if self.fail:
            raise ValueError("invalid sight result")
        return self.views[start]


class Bridge:
    def __init__(self):
        self.rights = []
        self.durations = []
        self.accepted = True
        self.collision = types.SimpleNamespace(clearance=Clearance())

    def set_right(self, value):
        self.rights.append(value)
        return self.accepted

    def transition_duration(self, seconds):
        self.durations.append(seconds)


class Settings:
    def __init__(self, left=False):
        self.left = left
        self.saves = 0
        self.automatic = True
        self.delays = (SWAP_S, RETURN_S)

    def shoulder_auto(self):
        return Values(self.automatic, *self.delays)

    def shoulder_left(self):
        return self.left

    def set_shoulder_left(self, value):
        self.saves += 1
        self.left = value

    @staticmethod
    def shoulder_transition():
        return 0.2


def controller():
    manager = types.SimpleNamespace(GetActorCameraMode=lambda _actor: "ThirdPerson",
                                    GetCameraRotation=lambda: types.SimpleNamespace(Yaw=0.0, Pitch=0.0))
    lifetime = types.SimpleNamespace(owned=lambda: (object(), manager))
    owner = types.SimpleNamespace(
        bridge=Bridge(), climb=types.SimpleNamespace(busy=False), ads=None, _bridge_started=True,
        _hooks_installed=True, _mode_pushes=1, _aiming=False, _in_vehicle=False,
        foot_mode=types.SimpleNamespace(pending=False), _lifetime=lifetime, lines=[])
    owner.log = owner.lines.append
    return owner


def frames(state, owner, settings, seconds, start_ns):
    now = start_ns
    for _ in range(round(seconds * 1e9 / FRAME_NS)):
        now += FRAME_NS
        state.follow(owner, settings, now)
    return now


def start(sight=None):
    owner, settings, state = controller(), Settings(), ShoulderState()
    state.sight = sight or Sight()
    state.apply_saved(owner.bridge, settings)
    return owner, settings, state, owner.bridge.collision.clearance


owner, settings, state, clearance = start()
check("the saved side is shown first", state.shown_left is False)
clearance.set(0.1, 1.0)
now = frames(state, owner, settings, SWAP_S + 0.05, 0)
check("a wall at the right camera shows the left shoulder", owner.bridge.rights[-1] == -48.4
      and state.shown_left is True)
check("the swap uses the shoulder transition", owner.bridge.durations[-1] == 0.2)
check("the saved shoulder is not changed by a swap", settings.left is False and settings.saves == 0)
check("the swap is written once", owner.bridge.rights.count(-48.4) == 1)
check("the swap is logged with its reading", owner.lines[-1] == "automatic shoulder: left shown (free 0.10, other 1.00)")
check("during a swap the chosen side is measured", clearance.wanted)

owner._aiming = True
clearance.set(1.0, 1.0)
sight_calls = state.sight.calls
now = frames(state, owner, settings, RETURN_S + 0.5, now)
check("aiming never brings the shoulder back", state.shown_left is True and owner.bridge.rights[-1] == -48.4)
check("aiming stops the second sweep and the view checks", not clearance.wanted and state.sight.calls == sight_calls)
owner._aiming = False
now = frames(state, owner, settings, RETURN_S + 0.05, now)
check("once clear for the return delay the chosen right shoulder is back",
      owner.bridge.rights[-1] == 48.4 and state.shown_left is False)
check("the return is logged", owner.lines[-1].startswith("automatic shoulder: right shown"))
check("a clear shoulder asks for no second sweep", not clearance.wanted)

clearance.set(0.1, 1.0)
now = frames(state, owner, settings, SWAP_S + 0.05, now)
check("the shoulder key during a swap is taken", state.player_switch(owner, settings))
check("the key shows the chosen shoulder, the saved one unchanged",
      owner.bridge.rights[-1] == 48.4 and state.shown_left is False and settings.saves == 0)
now = frames(state, owner, settings, 1.0, now)
check("after the key the wall does not swap again", owner.bridge.rights[-1] == 48.4)
check("the key with no swap is left to the normal shoulder change", not state.player_switch(owner, settings))

clearance.reading = None
before = list(owner.bridge.rights)
frames(state, owner, settings, 1.0, now)
check("no reading changes nothing", owner.bridge.rights == before and not clearance.wanted)

owner, settings, state, clearance = start(Sight(shown=0.3))
clearance.set(1.0, None)
now = frames(state, owner, settings, 0.05, 0)
check("a wall ahead of a roomy camera asks for the other side", clearance.wanted and state.shown_left is False)
clearance.set(1.0, 1.0)
frames(state, owner, settings, SWAP_S + 0.05, now)
check("a wall ahead of the right camera shows the left shoulder", state.shown_left is True
      and owner.lines[-1] == "automatic shoulder: left shown (free 0.30, other 1.00)")

owner, settings, state, clearance = start(Sight(shown=0.3, other=0.4))
clearance.set(1.0, 1.0)
frames(state, owner, settings, 1.0, 0)
check("a wall ahead of both cameras swaps nothing", state.shown_left is False and owner.bridge.rights == [48.4])

owner, settings, state, clearance = start(Sight(fail=True))
clearance.set(0.1, 1.0)
frames(state, owner, settings, SWAP_S + 0.05, 0)
check("a failed view check is logged once", owner.lines.count(
    "automatic shoulder: view ahead unavailable (ValueError), room only") == 1)
check("without the view check the room still swaps", state.shown_left is True and state.sight.calls == 1)

owner, settings, state, clearance = start()
clearance.set(0.1, 1.0)
frames(state, owner, settings, SWAP_S, 0)
check("a menu change during a swap is saved and shown", state.set(owner.bridge, settings, True)
      and settings.left is True and state.shown_left is True and state.auto.override is None)

owner, settings, state, clearance = start()
settings.delays = (0.5, 0.05)
clearance.set(0.1, 1.0)
now = frames(state, owner, settings, 0.4, 0)
check("the player's longer switch delay is waited", state.shown_left is False)
now = frames(state, owner, settings, 0.15, now)
check("the switch comes once the player's delay has passed", state.shown_left is True)
clearance.set(1.0, 1.0)
frames(state, owner, settings, 0.1, now)
check("the player's shorter return delay brings the shoulder back sooner", state.shown_left is False)

owner, settings, state, clearance = start()
settings.automatic = False
clearance.set(0.1, 1.0)
frames(state, owner, settings, 1.0, 0)
check("switched off, a wall swaps nothing", state.shown_left is False and owner.bridge.rights == [48.4])
check("switched off, nothing is measured", not clearance.wanted and state.sight.calls == 0)

owner, settings, state, clearance = start()
clearance.set(0.1, 1.0)
now = frames(state, owner, settings, SWAP_S + 0.05, 0)
settings.automatic = False
frames(state, owner, settings, 0.05, now)
check("switching off during a swap shows the chosen shoulder at once",
      state.shown_left is False and owner.bridge.rights[-1] == 48.4 and state.auto.override is None)
check("switching off is logged", owner.lines[-1] == "automatic shoulder: switched off, right shown")

owner, settings, state, clearance = start()
del settings.automatic
settings.shoulder_auto = None
clearance.set(0.1, 1.0)
frames(state, owner, settings, 1.0, 0)
check("a mod without the switch keeps the shoulder still", state.shown_left is False)

owner, settings, state, clearance = start()
owner._aiming = True
settings.left = True
clearance.set(1.0, None)
frames(state, owner, settings, 0.5, 0)
check("a side saved elsewhere is never written while the shoulder is unavailable", owner.bridge.rights == [48.4])

owner, settings, state, clearance = start()
clearance.set(0.1, 1.0)
owner.bridge.accepted = False
try:
    frames(state, owner, settings, SWAP_S + 0.05, 0)
except RuntimeError:
    refused = True
else:
    refused = False
check("a refused swap reaches the camera's stop path", refused)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
