"""Keep only the local player's selected on-foot camera mode."""

from .constants import FFYL_MODE, GROUND_SLAM_EXIT_MODE, ORBIT_MODE, THIRD_PERSON_MODE

REQUESTS = {
    "/Script/OakGame.OakPlayerController:CameraTransition":
        ("NewMode", "Transition", "BlendTimeOverride", "bTeleport", "bForceResetMode"),
    "/Script/OakGame.OakPlayerController:ServerCameraTransition":
        ("NewMode", "Transition", "BlendTimeOverride", "bTeleport", "bForceResetMode"),
    "/Script/Engine.PlayerController:ClientSetCameraMode": ("NewCamMode",),
}
THIRD_PERSON = THIRD_PERSON_MODE
VEHICLE_MODE = "ThirdPersonVehicle"
# FFYL accepts the selected third-person camera while downed; verified in game on 2026-09-27.
# The game lays GroundSlamExit over the selected camera for 1.4 s after a ground slam lands; measured on 2026-10-02.
ON_FOOT_MODES = frozenset(("Default", "Slide", FFYL_MODE, GROUND_SLAM_EXIT_MODE))
RECOVERABLE_MODES = ON_FOOT_MODES | frozenset((ORBIT_MODE, THIRD_PERSON_MODE))


def _same_object(first, second):
    if first is second:
        return True
    try:
        return int(first._get_address()) == int(second._get_address())
    except (AttributeError, TypeError, ValueError):
        return first == second


class TransitionHooks:
    def __init__(self, hooks, identifier, controller, log, on_effective,
                 desired_mode=lambda: THIRD_PERSON, request_mode=None) -> None:
        self.hooks = hooks
        self.identifier = identifier
        self.controller = controller
        self.log = log
        self.on_effective = on_effective
        self.desired_mode = desired_mode
        self.request_mode = request_mode or self._request_direct
        self.paths = tuple(REQUESTS)
        self._first_person_allowed = False

    def set_first_person_allowed(self, allowed: bool) -> None:
        self._first_person_allowed = bool(allowed)

    def _wants_first_person(self) -> bool:
        if self._first_person_allowed:
            return True
        try:
            actor = self.controller.OakCharacter
            return bool(actor.ZoomState.bWantsToZoom)
        except Exception:
            return False

    @staticmethod
    def _request_direct(mode, call):
        call(mode)
        return True

    def _callback(self, names):
        def on_request(obj, args, _ret, func):
            if not _same_object(obj, self.controller):
                return None
            values = [getattr(args, name) for name in names]
            requested = str(values[0])
            desired = self.desired_mode()
            effective = (desired if requested in ON_FOOT_MODES
                         and not self._wants_first_person()
                         else requested)
            values[0] = effective
            try:
                self.on_effective(requested, effective)
            except Exception as error:
                self.log(f"camera transition refused: {type(error).__name__}")
                return self.hooks.Block
            if requested == effective:
                return None
            if effective == ORBIT_MODE:
                call = (self.controller.ClientSetCameraMode
                        if names[0] != "NewCamMode" else func)
                self.request_mode(effective, call)
            else:
                func(*values)
            return self.hooks.Block
        return on_request

    def install(self) -> None:
        for path, names in REQUESTS.items():
            if not self.hooks.has_hook(path, self.hooks.Type.PRE, self.identifier):
                self.hooks.add_hook(path, self.hooks.Type.PRE, self.identifier, self._callback(names))

    def remove(self) -> None:
        for path in REQUESTS:
            if self.hooks.has_hook(path, self.hooks.Type.PRE, self.identifier):
                self.hooks.remove_hook(path, self.hooks.Type.PRE, self.identifier)
