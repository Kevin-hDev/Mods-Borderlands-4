"""The desired foot mode has one bounded request and confirms before persistence."""

import pathlib
import sys
from types import SimpleNamespace as NS

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.foot_mode import (  # noqa: E402
    CONFIRMATION_TIMEOUT_NS, ORBIT_MODE, RESTORE_EXPECTED_NS,
    THIRD_PERSON_MODE, FootModeState,
)

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Settings:
    def __init__(self, orbit=False):
        self.orbit = orbit

    def orbit_enabled(self):
        return self.orbit


class PC:
    def __init__(self):
        self.calls = []

    def ClientSetCameraMode(self, mode):
        self.calls.append(mode)


check("measured delays are exact", RESTORE_EXPECTED_NS == 300_000_000
      and CONFIRMATION_TIMEOUT_NS == 800_000_000)
state, pc = FootModeState(), PC()
check("normal third person is desired by default", state.desired(Settings()) == THIRD_PERSON_MODE)
check("the saved Orbit option selects the measured mode", state.desired(Settings(True)) == ORBIT_MODE)
check("one request is issued", state.request(pc, ORBIT_MODE, 10) and pc.calls == [ORBIT_MODE])
check("a second request cannot replace the pending one",
      not state.request(pc, THIRD_PERSON_MODE, 20) and pc.calls == [ORBIT_MODE])
check("a different observation does not confirm", not state.observe("Default", 30) and state.pending)
check("the requested mode confirms and clears pending",
      state.observe(ORBIT_MODE, 40) and not state.pending and state.confirmations == 1)
state.request(pc, ORBIT_MODE, 100)
check("the measured timeout refuses an unconfirmed request",
      not state.observe("Default", 100 + CONFIRMATION_TIMEOUT_NS + 1)
      and not state.pending and state.timed_out and state.refusals == 2)
state.reset()
check("reset clears transient state but keeps scalar statistics",
      not state.pending and not state.timed_out and state.requests == 2)

# Cancellation revokes the save authority even when the pawn disappeared mid-request.
from apex_camera_runtime.foot_preemption import cancel_choice
state.begin(ORBIT_MODE, 200, True, False)
controller = NS(_lifetime=NS(pc_ref=lambda: None, owned=lambda: (None, None)))
cancel_choice(state, controller, 210)
check("missing context cannot leave a late save authority", state.transaction is None)
late_saves = []
settings = NS(set_orbit=late_saves.append)
state.settle(controller, settings, ORBIT_MODE, 220)
check("late Orbit confirmation after cancellation cannot save", late_saves == [])

from apex_camera_runtime.lifetime import CameraLifetime
old_actor, old_manager = NS(), NS()
live_pc = NS(OakCharacter=old_actor, PlayerCameraManager=old_manager)
life = CameraLifetime(lambda value: lambda: value)
life.bind(live_pc, old_actor, old_manager)
native_writes = []
controller = NS(_lifetime=life, _mode_pushes=0,
                set_desired_mode=lambda *_args, **_kw: native_writes.append("mode"))
state.begin(ORBIT_MODE, 300, True, False)
live_pc.OakCharacter = NS()
try:
    cancel_choice(state, controller, 310)
except Exception as error:
    native_writes.append(type(error).__name__)
check("changed pawn cannot receive rollback writes", native_writes == [])
check("changed pawn still revokes persistence", state.transaction is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
