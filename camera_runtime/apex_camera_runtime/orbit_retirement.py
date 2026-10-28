"""Observe a retired FP request until its late reply is safely corrected."""
from .cleanup_retry import CLEANUP_RETRY_FIRST_NS, MAX_CLEANUP_ATTEMPTS
from .constants import CAMERA_TRANSITION, CLIMB_MODE, LADDER_MODE, ORBIT_MODE
from .lifetime import CameraLifetime
from .transitions import VEHICLE_MODE

PRIORITIES = frozenset((VEHICLE_MODE, CLIMB_MODE, LADDER_MODE))


class OrbitRetirement:
    def __init__(self):
        self.reset()

    def reset(self):
        self.identity = None
        self.target = CAMERA_TRANSITION
        self.attempts = self.next_ns = 0
        self.confirmed = self.warned = False

    def retire(self, controller):
        state = getattr(controller, 'foot_mode', None)
        if getattr(state, 'return_mode', None) != CAMERA_TRANSITION:
            return
        identity = controller._lifetime.ids
        if self.identity != identity:
            self.reset()
            self.identity = identity
        actor, manager = controller._lifetime.owned()
        try:
            mode = str(manager.GetActorCameraMode(actor))
        except Exception:
            return  # No guessed native priority when the context cannot be read.
        if mode in PRIORITIES:
            self.target = mode

    def sync(self, client, pc, now_ns):
        if self.identity is None:
            return
        if client.settings.third_person_enabled() or client.settings.orbit_enabled():
            self.reset()
            return
        try:
            actor, manager = pc.OakCharacter, pc.PlayerCameraManager
            identity = tuple(CameraLifetime.address(item) for item in (pc, actor, manager))
            mode = str(manager.GetActorCameraMode(actor))
        except Exception:
            return
        if identity != self.identity:
            self.reset()
            return
        # A new owner may recover only the same current context, never the retired world's references.
        if mode != ORBIT_MODE:
            self.target = mode if mode in PRIORITIES else CAMERA_TRANSITION
            self.confirmed = self.attempts > 0
            return
        if self.confirmed or now_ns < self.next_ns:
            return
        if self.attempts >= MAX_CLEANUP_ATTEMPTS:
            if not self.warned:
                self.warned = True
                client.settings.note('Orbit Camera return unavailable. Please retry.')
            return
        self.attempts += 1
        self.next_ns = now_ns + CLEANUP_RETRY_FIRST_NS
        try:
            pc.ClientSetCameraMode(self.target)
        except Exception:
            # The next live observation confirms success or spends one bounded retry.
            return
