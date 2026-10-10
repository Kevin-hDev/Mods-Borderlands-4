"""Publish bounded settings to the one native camera writer; ownership stays unchanged."""
from .ads_category import address
from .framing_catalog import GROUPS
from .framing_layout import make_context
from .framing_status import PARTIAL_REASONS, confirmation
from .framing_diagnostics import Diagnostics

# The game places the shoulder with the framing's spacing and height now (shoulder_offset.py, 2026-10-08): the native
# framing keeps the aim zoom only, or it would move the camera again after the game's collision.
NATIVE_SHARE = tuple(1 if group.key == "zoom" else 0 for group in GROUPS)


def confirm_settings(runtime, owner, settings, restoring=False):
    """Dormant choices may be stored; live changes need the elected renderer's acknowledgement."""
    client = runtime.arbiter.active()
    if client is None or client.owner != owner:
        return restoring
    if not settings.third_person_enabled():
        return True
    controller = runtime.third_person
    if controller is None or not controller._bridge_started:
        return True
    if (getattr(getattr(controller, "climb", None), "busy", False)
            or controller._in_vehicle or controller._aiming or controller._aim_returning
            or controller._desired_mode != "ThirdPerson"):
        return True
    framing = controller.framing
    # Optional rendering refusal makes the choice dormant, not an unsavable setting.
    if framing is None or framing.unavailable:
        return True
    return framing.confirm(settings.framing_values())


class FramingSession:
    def __init__(self, bridge, native, reader, log, clock=None):
        self.bridge, self.native, self.reader = bridge, native, reader
        self._key = None
        self.reason = None
        self.unavailable = False
        self.diagnostics = Diagnostics(log, clock)
        self._confirmed_values = None

    def _report(self, reason):
        self.reason = reason
        self.diagnostics.report(reason)

    def stop(self):
        if self._key is not None:
            self.bridge.publish(None)
        self._key = None
        self.reason = None

    def confirm(self, snapshot):
        """Only a rendered frame of these values permits the menu to persist them."""
        values = tuple(row[0] for row in snapshot)
        if self._key is None or self._key[1] != values:
            return None
        status = self.bridge.status()
        accepted = confirmation(status, values, self._confirmed_values)
        if accepted is True:
            self._confirmed_values = values
        return accepted

    def sync(self, controller, pc, actor, manager, settings):
        read = getattr(settings, "framing_values", None)
        if (not callable(read) or not controller._bridge_started or controller._in_vehicle
                or controller._aiming or controller._aim_returning
                or getattr(controller, 'presentation_mode', lambda: controller._desired_mode)() != "ThirdPerson"
                or controller.foot_mode.pending
                or controller.cleanup_retry.pending or controller._suspensions):
            self.stop()
            return
        try:
            if str(manager.GetActorCameraMode(actor)) != "ThirdPerson":
                self.stop()
                return
            ready = self.native.prepare()
            self.unavailable = ready is False
            if ready is not True:
                self.stop()
                self._report("unavailable" if ready is False else None)
                return
            root = actor.RootComponent
            if (address(pc.OakCharacter) != address(actor) or address(pc.PlayerCameraManager) != address(manager)
                    or address(root) != address(actor.CapsuleComponent)
                    or address(root.Outer) != address(actor) or root.AttachParent is not None):
                raise ValueError("Camera body unavailable")
            captured = tuple(self.reader.capture(item) for item in (pc, actor, manager, root))
            snapshot = read()
            if (type(snapshot) is not tuple or len(snapshot) != len(GROUPS)
                    or any(type(row) is not tuple or len(row) != 2 or not group.valid(row[0])
                           or type(row[1]) is not bool for group, row in zip(GROUPS, snapshot))):
                raise ValueError("Camera framing choice unavailable")
            values = tuple(row[0] for row in snapshot)
            identities = tuple(identity for _, identity in captured)
            key = tuple((ref.address, ref.index, ref.serial) for ref in identities), values
            if key != self._key:
                context = make_context(actor, root, identities,
                                       tuple(value * kept for value, kept in zip(values, NATIVE_SHARE)))
                if any(ref() is None or address(ref()) != identity.address for ref, identity in captured):
                    raise ValueError("Camera body expired")
                self.bridge.publish(context)
                self._key = key
            status = self.bridge.status()
            if confirmation(status, values, self._confirmed_values) is True:
                self._confirmed_values = values
            self._report(PARTIAL_REASONS.get(status, "unavailable" if status > 1 else None))
        except Exception:
            # A failed optional publication cannot keep the preceding owner's values.
            self.stop()
            self._report("unavailable")
