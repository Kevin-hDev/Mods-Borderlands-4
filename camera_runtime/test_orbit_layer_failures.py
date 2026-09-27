"""Native layer failures stop the partial Orbit transaction and clean to Default."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.constants import ORBIT_MODE  # noqa: E402
from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bound, Bridge, Hooks, Manager, Settings, args  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class OnceFailingManager(Manager):
    def __init__(self):
        super().__init__()
        self.fail_push = self.fail_pop = False

    def PushActorCameraMode(self, actor, mode, *values):
        if self.fail_push:
            self.fail_push = False
            raise RuntimeError("push refused")
        return super().PushActorCameraMode(actor, mode, *values)

    def PopActorCameraMode(self, actor, *values):
        if self.fail_pop:
            self.fail_pop = False
            raise RuntimeError("pop refused")
        return super().PopActorCameraMode(actor, *values)


class PC:
    def __init__(self, address, actor, manager):
        self.address = address
        self.OakCharacter = actor
        self.PlayerCameraManager = manager
        self.client_modes = []

    def _get_address(self):
        return self.address

    def ClientSetCameraMode(self, mode):
        self.client_modes.append(mode)
        self.PlayerCameraManager.mode = mode


class RejectExitSettings(Settings):
    def set_orbit(self, value):
        if value is False:
            raise RuntimeError("save refused")
        super().set_orbit(value)


actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
rollback_manager, rollback_settings = OnceFailingManager(), RejectExitSettings()
rollback_settings.orbit = True
rollback_pc = PC(910, actor, rollback_manager)
rollback = ThirdPersonController(Hooks(), Bridge(), "orbit_rollback_pop")
rollback.sync("apex", rollback_pc, rollback_settings, 0)
rollback.toggle_orbit(rollback_settings, 1)
rollback_manager.fail_pop = True
rollback.sync("apex", rollback_pc, rollback_settings, 2)
check("a refused Pop during Orbit rollback stops cleanly in Default",
      rollback_manager.mode == "Default" and not rollback.cleanup_pending
      and not rollback.foot_mode.pending and rollback_settings.orbit)

push_manager, push_settings, push_hooks = OnceFailingManager(), Settings(), Hooks()
push_pc = PC(911, actor, push_manager)
push = ThirdPersonController(push_hooks, Bridge(), "orbit_preempt_push")
push.sync("apex", push_pc, push_settings, 10)
push.toggle_orbit(push_settings, 11)
push_manager.fail_push = True
path = next(path for path in push._transitions.paths if path.endswith(":CameraTransition"))
result = push_hooks.items[(path, "PRE", "orbit_preempt_push")](
    push_pc, args("ThirdPersonVehicle"), None, Bound())
check("a refused Push during vehicle preemption blocks and cleans the unit",
      result is push_hooks.Block and push_manager.mode == "Default"
      and not push.cleanup_pending and not push.foot_mode.pending)

pop_manager, pop_settings, pop_hooks = OnceFailingManager(), Settings(), Hooks()
pop_settings.orbit = True
pop_pc = PC(912, actor, pop_manager)
pop = ThirdPersonController(pop_hooks, Bridge(), "orbit_preempt_pop")
pop.sync("apex", pop_pc, pop_settings, 20)
pop.toggle_orbit(pop_settings, 21)
pop_manager.fail_pop = True
path = next(path for path in pop._transitions.paths if path.endswith(":CameraTransition"))
result = pop_hooks.items[(path, "PRE", "orbit_preempt_pop")](
    pop_pc, args("ThirdPersonVehicle"), None, Bound())
check("a refused Pop during vehicle preemption blocks and cleans the unit",
      result is pop_hooks.Block and pop_manager.mode == "Default"
      and not pop.cleanup_pending and not pop.foot_mode.pending and pop_settings.orbit)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
