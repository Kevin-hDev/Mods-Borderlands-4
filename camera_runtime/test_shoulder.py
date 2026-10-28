"""Shoulder changes are signed, persisted once and rolled back visibly on failure."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.shoulder import ShoulderState, signed_right  # noqa: E402
from apex_camera_runtime.constants import THIRD_PERSON_RIGHT as RIGHT  # noqa: E402
from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bridge, Hooks, Manager, Settings  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class ShoulderSettings:
    def __init__(self, left=False, fail=False):
        self.left = left
        self.fail = fail
        self.saves = 0

    def shoulder_left(self):
        return self.left

    def set_shoulder_left(self, value):
        self.saves += 1
        if self.fail:
            raise RuntimeError("save failed")
        self.left = value


class ShoulderBridge:
    def __init__(self, accepted=True):
        self.accepted = accepted
        self.values = []

    def set_right(self, value):
        self.values.append(value)
        return self.accepted


class RollbackRefusingBridge(ShoulderBridge):
    def set_right(self, value):
        self.values.append(value)
        return len(self.values) == 1


class ControllerRollbackBridge(Bridge):
    def set_right(self, value):
        self.rights.append(value)
        return len(self.rights) <= 2


class ControllerFailingSettings(Settings):
    def set_shoulder_left(self, _value):
        raise RuntimeError("save failed")


check("the default shoulder is the positive right side", signed_right(False) == RIGHT)
check("the left shoulder uses the negative offset", signed_right(True) == -RIGHT)
state = ShoulderState()
saved_left, applying = ShoulderSettings(True), ShoulderBridge()
check("the saved side can be applied", state.apply_saved(applying, saved_left))
check("the saved left side reaches the bridge", applying.values == [-RIGHT])

settings, bridge = ShoulderSettings(), ShoulderBridge()
check("a successful side change is saved", state.set(bridge, settings, True))
check("success writes left once and saves once",
      bridge.values == [-RIGHT] and settings.left and settings.saves == 1)

refused_settings, refused_bridge = ShoulderSettings(), ShoulderBridge(False)
check("a native refusal does not save", not state.set(refused_bridge, refused_settings, True))
check("the refused setting stays right", not refused_settings.left and refused_settings.saves == 0)

failing_settings, rollback_bridge = ShoulderSettings(fail=True), ShoulderBridge()
check("a save failure reports failure", not state.set(rollback_bridge, failing_settings, True))
check("a save failure restores the visible right side",
      rollback_bridge.values == [-RIGHT, RIGHT] and not failing_settings.left)

unsafe_settings, unsafe_bridge = ShoulderSettings(fail=True), RollbackRefusingBridge()
try:
    state.set(unsafe_bridge, unsafe_settings, True)
except RuntimeError:
    rollback_refused = True
else:
    rollback_refused = False
check("a refused visible rollback is a fatal camera transaction",
      rollback_refused and unsafe_bridge.values == [-RIGHT, RIGHT]
      and not unsafe_settings.left)

manager, native, hooks = Manager(), Bridge(), Hooks()
actor = object()
pc = types.SimpleNamespace(_get_address=lambda: 10, OakCharacter=actor,
                           PlayerCameraManager=manager)
controller_settings = Settings()
controller_settings.left = True
controller = ThirdPersonController(hooks, native, "camera")
controller.sync("apex", pc, controller_settings, 0)
check("controller startup passes the persisted signed side", native.start_rights == [-RIGHT])
controller.stop()

unsafe_native, unsafe_manager = ControllerRollbackBridge(), Manager()
unsafe_pc = types.SimpleNamespace(_get_address=lambda: 11, OakCharacter=object(),
                                  PlayerCameraManager=unsafe_manager)
unsafe_controller = ThirdPersonController(Hooks(), unsafe_native, "unsafe_camera")
unsafe_controller.sync("apex", unsafe_pc, ControllerFailingSettings(), 1)
try:
    unsafe_controller.set_shoulder(ControllerFailingSettings(), True)
except RuntimeError:
    controller_refused = True
else:
    controller_refused = False
check("a refused rollback stops the inconsistent camera unit",
      controller_refused and not unsafe_controller.cleanup_pending
      and unsafe_native.stops == 1 and unsafe_manager.pushes == unsafe_manager.pops == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
