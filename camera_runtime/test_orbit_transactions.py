"""Explicit Orbit changes wait for the visible mode before saving their choice."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.foot_mode import CONFIRMATION_TIMEOUT_NS, ORBIT_MODE  # noqa: E402
from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bridge, Hooks, Manager, Settings  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class DelayedPC:
    def __init__(self, actor, manager):
        self.OakCharacter = actor
        self.PlayerCameraManager = manager
        self.client_modes = []

    def _get_address(self):
        return 801

    def ClientSetCameraMode(self, mode):
        self.client_modes.append(mode)


class DeferredPushManager(Manager):
    def __init__(self):
        super().__init__()
        self.defer = False

    def PushActorCameraMode(self, _actor, mode, *_args):
        self.pushes += 1
        if not self.defer:
            self.mode = mode


actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
manager, settings = Manager(), Settings()
pc = DelayedPC(actor, manager)
controller = ThirdPersonController(Hooks(), Bridge(), "orbit_transaction")
controller.sync("apex", pc, settings, 0)

check("entering Orbit accepts one asynchronous request",
      controller.toggle_orbit(settings, 10) and pc.client_modes == [ORBIT_MODE])
check("F7 is ignored while the requested mode is still pending",
      not controller.toggle_orbit(settings, 11) and pc.client_modes == [ORBIT_MODE])
check("the Orbit choice is not saved before the visible mode confirms",
      not settings.orbit and controller.foot_mode.pending)
controller.sync("apex", pc, settings, 20)
check("an unrelated frame keeps the transaction pending",
      not settings.orbit and controller.foot_mode.pending)
manager.mode = ORBIT_MODE
controller.sync("apex", pc, settings, 30)
check("visible Orbit confirms and saves exactly once",
      settings.orbit and settings.orbit_saves == 1 and not controller.foot_mode.pending)

check("leaving Orbit starts without saving first", controller.toggle_orbit(settings, 40))
check("the saved Orbit choice remains until ThirdPerson is observed",
      settings.orbit and controller.foot_mode.pending)
controller.sync("apex", pc, settings, 50)
check("visible ThirdPerson confirms the exit and saves once",
      not settings.orbit and settings.orbit_saves == 2 and not controller.foot_mode.pending)
controller.stop()

blocked_manager, blocked_settings = Manager(), Settings()
blocked_pc = DelayedPC(actor, blocked_manager)
blocked = ThirdPersonController(Hooks(), Bridge(), "orbit_unstable")
blocked.sync("apex", blocked_pc, blocked_settings, 60)
blocked_manager.mode = "Slide"
check("F7 is ignored while Slide is visible",
      not blocked.toggle_orbit(blocked_settings, 61) and blocked_pc.client_modes == [])
blocked_manager.mode = "Default"
check("F7 is ignored while Default is visible",
      not blocked.toggle_orbit(blocked_settings, 62) and blocked_pc.client_modes == [])
blocked.stop()

timeout_manager, timeout_settings = Manager(), Settings()
timeout_pc = DelayedPC(actor, timeout_manager)
timeout = ThirdPersonController(Hooks(), Bridge(), "orbit_transaction_timeout")
timeout.sync("apex", timeout_pc, timeout_settings, 0)
check("a delayed Orbit request is initially accepted",
      timeout.toggle_orbit(timeout_settings, 1))
timeout.sync("apex", timeout_pc, timeout_settings, CONFIRMATION_TIMEOUT_NS + 2)
check("a timed-out entry restores ThirdPerson without saving Orbit",
      timeout_manager.mode == "ThirdPerson" and timeout._mode_pushes == 1
      and not timeout_settings.orbit and timeout_settings.orbit_saves == 0
      and timeout_settings.orbit_rejections == 1 and timeout.foot_mode.timed_out)
timeout.stop()

exit_manager, exit_settings = Manager(), Settings()
exit_settings.orbit = True
exit_pc = DelayedPC(actor, exit_manager)
exit = ThirdPersonController(Hooks(), Bridge(), "orbit_exit_timeout")
exit.sync("apex", exit_pc, exit_settings, 0)
exit_manager.mode = ORBIT_MODE
exit.sync("apex", exit_pc, exit_settings, 1)
exit.toggle_orbit(exit_settings, 2)
exit_manager.mode = ORBIT_MODE
exit.sync("apex", exit_pc, exit_settings, CONFIRMATION_TIMEOUT_NS + 3)
check("a timed-out exit restores the saved Orbit choice through one tracked request",
      exit_settings.orbit and exit.foot_mode.pending
      and exit_pc.client_modes[-1] == ORBIT_MODE)
exit_manager.mode = ORBIT_MODE
exit.sync("apex", exit_pc, exit_settings, CONFIRMATION_TIMEOUT_NS + 4)
check("the restored Orbit mode consumes the old timeout without falling back again",
      not exit.foot_mode.pending and not exit.foot_mode.timed_out
      and exit._desired_mode == ORBIT_MODE and exit._mode_pushes == 0
      and exit._orbit_blocked_identity is None and exit_manager.mode == ORBIT_MODE)
exit.stop()

late_entry_manager, late_entry_settings = Manager(), Settings()
late_entry_pc = DelayedPC(actor, late_entry_manager)
late_entry = ThirdPersonController(Hooks(), Bridge(), "orbit_late_entry")
late_entry.sync("apex", late_entry_pc, late_entry_settings, 0)
late_entry.toggle_orbit(late_entry_settings, 1)
late_entry.sync("apex", late_entry_pc, late_entry_settings, CONFIRMATION_TIMEOUT_NS + 2)
late_entry.sync("apex", late_entry_pc, late_entry_settings, CONFIRMATION_TIMEOUT_NS + 3)
late_entry_manager.mode = ORBIT_MODE
late_entry.sync("apex", late_entry_pc, late_entry_settings, CONFIRMATION_TIMEOUT_NS + 4)
check("a very late Orbit entry starts one tracked ThirdPerson recovery",
      late_entry.foot_mode.pending and late_entry._desired_mode == "ThirdPerson"
      and late_entry._mode_pushes == 1)
late_entry_manager.mode = "ThirdPerson"
late_entry.sync("apex", late_entry_pc, late_entry_settings, CONFIRMATION_TIMEOUT_NS + 5)
check("the late entry recovery confirms the saved ThirdPerson choice",
      not late_entry.foot_mode.pending and not late_entry_settings.orbit
      and late_entry_manager.mode == "ThirdPerson")
late_entry.stop()

stuck_late_manager, stuck_late_settings = DeferredPushManager(), Settings()
stuck_late_pc = DelayedPC(actor, stuck_late_manager)
stuck_late = ThirdPersonController(Hooks(), Bridge(), "orbit_late_entry_timeout")
stuck_late.sync("apex", stuck_late_pc, stuck_late_settings, 0)
stuck_late.toggle_orbit(stuck_late_settings, 1)
stuck_late.sync("apex", stuck_late_pc, stuck_late_settings, CONFIRMATION_TIMEOUT_NS + 2)
stuck_late.sync("apex", stuck_late_pc, stuck_late_settings, CONFIRMATION_TIMEOUT_NS + 3)
stuck_late_manager.defer = True
stuck_late_manager.mode = ORBIT_MODE
stuck_late.sync("apex", stuck_late_pc, stuck_late_settings, CONFIRMATION_TIMEOUT_NS + 4)
stuck_late.sync("apex", stuck_late_pc, stuck_late_settings,
                2 * CONFIRMATION_TIMEOUT_NS + 5)
check("an unconfirmed late ThirdPerson recovery releases its authority",
      not stuck_late.cleanup_pending)
check("an unconfirmed late ThirdPerson recovery requests Default",
      stuck_late_pc.client_modes[-1] == "Default")

late_exit_manager, late_exit_settings = Manager(), Settings()
late_exit_settings.orbit = True
late_exit_pc = DelayedPC(actor, late_exit_manager)
late_exit = ThirdPersonController(Hooks(), Bridge(), "orbit_late_exit")
late_exit.sync("apex", late_exit_pc, late_exit_settings, 0)
late_exit_manager.mode = ORBIT_MODE
late_exit.sync("apex", late_exit_pc, late_exit_settings, 1)
late_exit.toggle_orbit(late_exit_settings, 2)
late_exit_manager.mode = ORBIT_MODE
late_exit.sync("apex", late_exit_pc, late_exit_settings, CONFIRMATION_TIMEOUT_NS + 3)
late_exit_manager.mode = ORBIT_MODE
late_exit.sync("apex", late_exit_pc, late_exit_settings, CONFIRMATION_TIMEOUT_NS + 4)
late_exit_manager.mode = "ThirdPerson"
late_exit.sync("apex", late_exit_pc, late_exit_settings, CONFIRMATION_TIMEOUT_NS + 5)
check("a very late ThirdPerson exit starts one tracked Orbit recovery",
      late_exit.foot_mode.pending and late_exit._desired_mode == ORBIT_MODE
      and late_exit_pc.client_modes[-1] == ORBIT_MODE)
late_exit_manager.mode = ORBIT_MODE
late_exit.sync("apex", late_exit_pc, late_exit_settings, CONFIRMATION_TIMEOUT_NS + 6)
check("the late exit recovery confirms the saved Orbit choice",
      not late_exit.foot_mode.pending and late_exit_settings.orbit
      and late_exit_manager.mode == ORBIT_MODE)
late_exit.stop()

cancel_manager, cancel_settings = Manager(), Settings()
cancel_pc = DelayedPC(actor, cancel_manager)
cancel = ThirdPersonController(Hooks(), Bridge(), "orbit_menu_cancel")
cancel.sync("apex", cancel_pc, cancel_settings, 0)
check("the menu cancellation case starts one delayed Orbit request",
      cancel.toggle_orbit(cancel_settings, 1) and cancel.foot_mode.pending)
check("closing the menu replaces that request with the saved mode",
      cancel.cancel_orbit(cancel_settings, 2) and cancel.foot_mode.pending
      and cancel.foot_mode.pending_mode == "ThirdPerson")
cancel_manager.mode = ORBIT_MODE
cancel.sync("apex", cancel_pc, cancel_settings, 3)
check("the original late Orbit answer cannot commit after menu cancellation",
      cancel.foot_mode.pending and not cancel_settings.orbit
      and cancel_settings.orbit_saves == 0)
cancel_manager.mode = "ThirdPerson"
cancel.sync("apex", cancel_pc, cancel_settings, 4)
check("the saved mode confirms and completes the menu cancellation",
      not cancel.foot_mode.pending and not cancel_settings.orbit
      and cancel._desired_mode == "ThirdPerson")
cancel.stop()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
