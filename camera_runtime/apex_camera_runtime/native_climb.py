"""Temporarily select the game's climbing camera without changing movement or saved choices."""
from . import aiming, foot_preemption, native_climb_state
from .constants import CAMERA_BLEND, CAMERA_TELEPORT, CAMERA_TRANSITION, CLIMB_MODE, LADDER_MODE
from .foot_mode import CONFIRMATION_TIMEOUT_NS
from .transitions import VEHICLE_MODE


class NativeClimb:
    def __init__(self):
        self.reset()

    @property
    def busy(self):
        return self.phase != ""

    def reset(self):
        self.phase = ""
        self.requested_ns = 0
        self.confirmed = False
        self.refused = False
        self.read_failed = False

    def transition_mode(self, controller):
        if controller._in_vehicle:
            return controller._desired_mode
        actor, _manager = controller._lifetime.owned()
        try:
            state = native_climb_state.read(actor)
            if self.busy and (state is None or any(state)):
                return CLIMB_MODE
        except Exception:
            # Do not guess a new camera while the native traversal cannot be read.
            return CLIMB_MODE if self.busy else controller._desired_mode
        return controller._desired_mode

    def preserve_mode(self, controller, requested, effective):
        if not self.busy or requested.casefold() != LADDER_MODE or effective != CLIMB_MODE:
            return False
        actor, manager = controller._lifetime.owned()
        # A redundant replacement restarts the native blend; keep the confirmed view instead.
        try:
            return actor is not None and manager is not None and str(manager.GetActorCameraMode(actor)) == effective
        except Exception as error:
            if not self.read_failed:
                controller.log(f"native climb camera unreadable: {type(error).__name__}")
                self.read_failed = True
            return True

    def _refuse(self, controller, reason):
        if not self.refused:
            self.refused = True
            controller.log(f"native climb camera refused: {reason}")

    def _request(self, controller, pc, mode, now_ns):
        self.requested_ns = now_ns
        try:
            pc.ClientSetCameraMode(mode)
        except Exception as error:
            self._refuse(controller, type(error).__name__)

    def sync(self, controller, pc, actor, manager, now_ns):
        mode = str(manager.GetActorCameraMode(actor))
        if mode == VEHICLE_MODE or controller._in_vehicle:
            if self.busy:
                controller._suspend("vehicle", True)
                foot_preemption.end(controller.foot_mode, "climb")
            self.reset()
            controller._suspend("climb", False)
            return False
        try:
            state = native_climb_state.read(actor)
        except Exception as error:
            if not self.read_failed:
                controller.log(f"native climb state unreadable: {type(error).__name__}")
                self.read_failed = True
            return self.busy
        if state is None:
            return self.busy
        on_wall, scripted = state
        active = on_wall or scripted
        entering = scripted or (on_wall and mode.casefold() == LADDER_MODE)
        if self.phase == "return" and entering:
            self.reset()
        if not self.busy:
            if not entering:
                return False
            self.phase = "enter"
            self.requested_ns = now_ns
            controller._suspend("climb", True)
            controller.log("native climb camera entered")
        if active and self.phase == "enter":
            # ADS cleanup must complete before another presentation is selected.
            if controller.ads is not None and not controller.ads.stop():
                if now_ns - self.requested_ns > CONFIRMATION_TIMEOUT_NS:
                    self._refuse(controller, "aim cleanup pending")
                    controller.stop(now_ns=now_ns)
                return True
            if controller.framing is not None:
                controller.framing.stop()
            controller.zoom.release()
            foot_preemption.cancel(controller.foot_mode, controller, "climb", True)
            aiming.prepare_vehicle(controller, "ThirdPerson", controller._desired_mode,
                                   CAMERA_TRANSITION, CAMERA_BLEND, CAMERA_TELEPORT)
            self.phase = "hold"
            self._request(controller, pc, CLIMB_MODE, now_ns)
            return True
        if active:
            if not self.confirmed and not self.refused:
                if mode.casefold() == CLIMB_MODE.casefold():
                    self.confirmed = True
                elif now_ns - self.requested_ns > CONFIRMATION_TIMEOUT_NS:
                    self._refuse(controller, "confirmation timeout")
            return True
        target = controller._desired_mode
        if mode == target:
            foot_preemption.end(controller.foot_mode, "climb")
            self.reset()
            controller._suspend("climb", False)
            controller.log("native climb camera restored")
            return False
        if self.phase != "return":
            self.phase = "return"
            self.refused = False
            self._request(controller, pc, target, now_ns)
        elif now_ns - self.requested_ns > CONFIRMATION_TIMEOUT_NS:
            # Shutdown is retryable and owned by the existing cleanup policy.
            self._refuse(controller, "return timeout")
            controller.stop(now_ns=now_ns)
        return True
