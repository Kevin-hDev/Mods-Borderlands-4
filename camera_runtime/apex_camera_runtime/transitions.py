"""Keep only the local player's on-foot camera in ThirdPerson."""

REQUESTS = {
    "/Script/OakGame.OakPlayerController:CameraTransition":
        ("NewMode", "Transition", "BlendTimeOverride", "bTeleport", "bForceResetMode"),
    "/Script/OakGame.OakPlayerController:ServerCameraTransition":
        ("NewMode", "Transition", "BlendTimeOverride", "bTeleport", "bForceResetMode"),
    "/Script/Engine.PlayerController:ClientSetCameraMode": ("NewCamMode",),
}
THIRD_PERSON = "ThirdPerson"
VEHICLE_MODE = "ThirdPersonVehicle"
ON_FOOT_MODES = frozenset(("Default", "Slide"))


def _same_object(first, second):
    if first is second:
        return True
    try:
        return int(first._get_address()) == int(second._get_address())
    except (AttributeError, TypeError, ValueError):
        return first == second


class TransitionHooks:
    def __init__(self, hooks, identifier, controller, log, on_effective) -> None:
        self.hooks = hooks
        self.identifier = identifier
        self.controller = controller
        self.log = log
        self.on_effective = on_effective
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

    def _callback(self, names):
        def on_request(obj, args, _ret, func):
            if not _same_object(obj, self.controller):
                return None
            values = [getattr(args, name) for name in names]
            requested = str(values[0])
            effective = (THIRD_PERSON if requested in ON_FOOT_MODES
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
