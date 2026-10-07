"""Resolve the current rendered camera; retain the thunk until native stop."""
import ctypes
import math
import threading
import time

from . import collision_config as config
from .collision_path import CollisionPath
from .collision_path import point
from .collision_diagnostics import CollisionDiagnostics
from .collision_sweep import SphereSweep
from .collision_visibility import Visibility
from .generated_ads import CollisionQuery, MIN_POINTER
from .lifetime import CameraLifetime
from .shoulder_clearance import ShoulderClearance
from .constants import THIRD_PERSON_MODE

Callback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(CollisionQuery), ctypes.POINTER(ctypes.c_double))


class CollisionResolver:
    def __init__(self, kismet, sdk, weak_ref, note):
        self.sweep = SphereSweep(kismet, sdk)
        self.visibility = Visibility(kismet, sdk)
        self.path = CollisionPath()
        self.clearance = ShoulderClearance()
        self.lifetime = CameraLifetime(weak_ref)
        self.callback = None
        self.thread = None
        self.busy = False
        self.release_pending = False
        self.reference_clear = False
        self.margin_blocked = False
        self.offset_permission = None
        self.diagnostics = CollisionDiagnostics(note)

    @property
    def note(self):
        return self.diagnostics.note

    @note.setter
    def note(self, value):
        self.diagnostics.note = value

    def start(self, library, pc, manager):
        self.climbing = False
        if self.release_pending and not self.busy:
            self.release()
        if self.callback is not None:
            raise RuntimeError('Camera collision cleanup required')
        self.lifetime.bind(pc, pc.OakCharacter, manager)
        if any(address < MIN_POINTER for address in self.lifetime.ids):
            raise ValueError('Invalid collision identity')
        self.invalidate()
        self.diagnostics.reset()
        self.thread = threading.get_ident()
        library.view_set_collision.argtypes = [Callback]
        library.view_set_collision.restype = ctypes.c_int
        self.callback = Callback(self._resolve)
        if library.view_set_collision(self.callback):
            raise RuntimeError('Camera collision registration refused')

    def release(self):
        self.climbing = False
        self.offset_permission = None
        # Only CameraBridge calls this after the native hook has stopped successfully.
        # A reentrant stop must not free a libffi thunk while its epilogue is executing.
        if self.busy:
            self.release_pending = True
            self.reference_clear = False
            return
        self.release_pending = False
        self.callback = self.thread = None
        self.lifetime.clear()
        self.invalidate()

    def invalidate(self):
        self.reference_clear = False
        self.margin_blocked = False
        self.path.reset()
        self.clearance.clear()

    def _mode_allowed(self, manager, actor):
        # Check the elected owner's permission before ThirdPerson too: ADS may
        # already want the camera while its native mode name has not changed yet.
        if self.offset_permission is not None:
            permitted = self.offset_permission(manager, actor)
            if permitted is not None:
                return permitted is True
        mode = str(manager.GetActorCameraMode(actor))
        return mode == THIRD_PERSON_MODE or (getattr(self, 'climbing', False) and mode == 'ThirdPersonClimbing')

    def _owned(self, query):
        pc = self.lifetime.pc_ref() if self.lifetime.pc_ref else None
        _, actor, manager, _, changed = self.lifetime.inspect(pc)
        owned_actor, owned_manager = self.lifetime.owned()
        if (changed or self.release_pending or owned_actor is None or owned_manager is None
                or self.lifetime.address(owned_actor) != self.lifetime.address(actor)
                or self.lifetime.address(owned_manager) != self.lifetime.address(manager)
                or query.manager != self.lifetime.ids[2]):
            raise ValueError('Camera collision identity unavailable')
        return actor

    def _resolve(self, pointer, output):
        self.reference_clear = False
        if self.busy or self.thread != threading.get_ident() or not pointer or not output:
            return 1
        self.busy = True
        started = time.perf_counter_ns()
        try:
            query = pointer.contents
            actor = self._owned(query)
            manager = self.lifetime.owned()[1]
            if not self._mode_allowed(manager, actor):
                self.invalidate()
                return 1  # ADS/vehicle/Orbit may legitimately own this frame; not an incident.
            # The game has already resolved its own camera. Sweep only the added offset,
            # not a second waist-to-camera path that incorrectly hits low cover.
            anchor, desired = point(tuple(query.before)), point(tuple(query.desired))
            if math.dist(anchor, desired) <= config.MIN_LENGTH:
                self.invalidate()
                position = desired
            else:
                self.visibility.begin_frame()
                distance = self.sweep.distance(actor, anchor, desired)
                length = math.dist(anchor, desired)
                endpoint = tuple(a + (b - a) * distance / length for a, b in zip(anchor, desired))
                if self.margin_blocked or self.sweep.reduced:
                    extra = config.RELEASE_MARGIN if self.margin_blocked else 0.0
                    # Release belongs to the swept target, independent of this frame's small return step.
                    clear = self.sweep.endpoint_clear(actor, endpoint, extra)
                    if self.margin_blocked and not clear and not self.sweep.reduced:
                        # A shortened shoulder touches its 12 cm margin; a clear native anchor can release the latch.
                        clear = self.sweep.endpoint_clear(actor, anchor, config.RELEASE_MARGIN)
                    self.margin_blocked = not clear
                if self.margin_blocked:
                    # No sightline can permit an unsafe target; skip visibility while the wall owns the frame.
                    self.path.reset()
                    self.path.fraction = 0.0
                    # Native was rendered during the latch: release is a smooth return, not a new entry.
                    self.path.initialized = True
                    position = anchor
                else:
                    target = self.visibility.target(actor)
                    position = self._position(actor, anchor, desired, distance, target, query.delta)
                self.clearance.record(self.sweep, actor, manager, anchor, desired, distance, self.margin_blocked,
                                      position)
            self._owned(query)
            if not self._mode_allowed(manager, actor):
                self.invalidate()
                return 1
            for index, value in enumerate(position):
                output[index] = value
            now = time.perf_counter_ns()
            self.diagnostics.record(now, now - started, self.path.fraction < 1.0 - config.MIN_LENGTH)
            self.reference_clear = self.path.fraction >= 1.0 - config.MIN_LENGTH
            return 0
        except Exception as error:
            self.invalidate()
            now = time.perf_counter_ns()
            self.diagnostics.record(now, now - started, error=error)
            return 1
        finally:
            self.busy = False

    def _position(self, actor, anchor, desired, distance, target, delta):
        length = math.dist(anchor, desired)
        previous = min(self.path.fraction, distance / length)
        current = tuple(a + (b - a) * previous for a, b in zip(anchor, desired))
        clear = self.visibility.clear(actor, current, target)
        if not self.path.initialized:
            self.path.initialized = True
            if not clear:
                # Entry has no passing-obstacle grace: the obstruction already exists.
                visible = self.visibility.distance(actor, anchor, desired, distance, target)
                self.path.fraction = visible / length
                return tuple(a + (b - a) * self.path.fraction for a, b in zip(anchor, desired))
        if clear:
            self.path.obscured_for = 0.0
            limit = self.visibility.recovery_distance(actor, anchor, desired, distance, previous, target)
            return self.path.resolve(anchor, desired, limit, delta)
        endpoint = tuple(a + (b - a) * distance / length for a, b in zip(anchor, desired))
        if self.visibility.clear(actor, endpoint, target):
            # Already hidden: escape toward the clear shoulder instead of following
            # the passing obstacle inward. A barrier only protects an existing view.
            self.path.obscured_for = 0.0
            return self.path.resolve(anchor, desired, distance, delta)
        # Aim at the current native anchor while hidden, not a moving shadow edge.
        # Stop retracting once visible; the return-path barrier then keeps that side.
        return self.path.resolve(anchor, desired, distance, delta, 0.0)
