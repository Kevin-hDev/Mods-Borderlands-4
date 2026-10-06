"""A single deferred Orbit entry borrows the next live first-person frame."""
from .aiming import wants_to_aim
from .constants import CAMERA_TRANSITION, ORBIT_MODE
from .lifetime import CameraLifetime
from .native_climb_state import read as climb_state
from .orbit_retirement import OrbitRetirement


def context_identity(pc, modes=(CAMERA_TRANSITION,)):
    try:
        actor, manager = pc.OakCharacter, pc.PlayerCameraManager
        state = climb_state(actor)
        if (actor is None or manager is None or wants_to_aim(actor)
                or state is None or any(state)
                or str(manager.GetActorCameraMode(actor)) not in modes):
            return None
        return tuple(CameraLifetime.address(item) for item in (pc, actor, manager))
    except Exception:
        return None


class OrbitEntry:
    def __init__(self):
        self.context = None
        self.pending = None
        self.retirement = OrbitRetirement()

    def observe(self, client, pc):
        identity = context_identity(pc)
        self.context = (client.owner, identity) if client is not None and identity is not None else None

    def base_view_locked(self, runtime, owner):
        client, state = runtime.arbiter.active(), getattr(runtime.third_person, 'foot_mode', None)
        return bool(client is not None and client.owner == owner and
                    (getattr(client.settings, 'orbit_enabled', lambda: False)()
                     or self.pending is not None or getattr(state, 'pending', False)))

    def ready(self, runtime, client):
        controller = runtime.third_person
        return (self.pending is None and self.context is not None
                and self.context[0] == client.owner
                and not client.settings.third_person_enabled()
                and not client.settings.orbit_enabled()
                and (controller is None or not controller.cleanup_pending))

    def request(self, runtime, client, enabled):
        if enabled is not True or not self.ready(runtime, client):
            return False
        # Keep identifiers, not strong SDK references, and revalidate on consumption.
        self.pending = self.context
        self.retirement.reset()
        return True

    def retire(self, client, controller):
        self.retirement.retire(controller)

    def cancel(self, client):
        if self.pending is None or self.pending[0] != client.owner:
            return False
        self.pending = None
        client.settings.reject_orbit()
        return True

    def sync(self, runtime, client, pc, now_ns):
        controller = runtime.third_person
        if self.pending is None:
            if controller is not None and hasattr(controller, 'foot_mode'):
                state = controller.foot_mode
                before = state.transaction
                if (before is not None or state.pending_rollback):
                    self.retire(client, controller)
                controller.sync(client.owner, pc, client.settings, now_ns)
            elif controller is not None:
                controller.sync(client.owner, pc, client.settings, now_ns)
            self.retirement.sync(client, pc, now_ns)
            return
        expected = self.pending
        self.pending = None
        if self.context != expected or controller is None:
            client.settings.reject_orbit()
            return
        controller.entry_requested = True
        try:
            controller.sync(client.owner, pc, client.settings, now_ns)
            if not controller.set_orbit(client.settings, True, now_ns):
                client.settings.reject_orbit()
        except Exception:
            client.settings.reject_orbit()
            raise
        finally:
            controller.entry_requested = False

    def reset(self):
        # Retired scalar identifiers survive handoff; only a matching live context can consume them.
        self.context = self.pending = None
