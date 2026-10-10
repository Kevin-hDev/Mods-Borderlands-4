"""Watch the third-person camera the game places, now that the game places the shoulder too (2026-10-08).

The native camera adds nothing of its own any more (shoulder_offset.py) and this callback hands the game's camera back
unchanged, after the game's camera and its collision, each third-person frame. It keeps two jobs:
- getting into a vehicle, the game's camera folds onto the hunter's head for one frame that stays about 0.1 s on
  screen (docs/third_person_fov/camera/enquetes/2026-10-08-saccade-vehicule.md); that frame, and any failure within
  HOLD_NS of a good frame, keep the last good camera instead (Kevin, 2026-10-08);
- the automatic shoulder reads the shown side's room here, on the game's tick (shoulder_clearance.py).
"""
import ctypes
import math
import threading
import time

from . import collision_config as config
from .collision_diagnostics import CollisionDiagnostics
from .collision_path import point
from .collision_sweep import SphereSweep
from .constants import THIRD_PERSON_MODE
from .generated_ads import CollisionQuery, MIN_POINTER
from .lifetime import CameraLifetime
from .shoulder_clearance import ShoulderClearance

Callback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(CollisionQuery), ctypes.POINTER(ctypes.c_double))


def folded(camera, hunter):
    """Whether the game's camera sits on its own pivot, the hunter's head: straight over the hunter, near its centre."""
    return (math.dist(camera[:2], hunter[:2]) <= config.FOLD_ACROSS_CM
            and math.dist(camera, hunter) <= config.FOLD_REACH_CM)


class CameraGuard:
    def __init__(self, kismet, sdk, weak_ref, note, shoulder, status=None):
        self.sweep = SphereSweep(kismet, sdk)
        self.clearance = ShoulderClearance()
        self.lifetime = CameraLifetime(weak_ref)
        self.shoulder = shoulder
        self.callback = None
        self.thread = None
        self.busy = False
        self.release_pending = False
        # The last good camera and when: (position, perf_counter_ns), None once the mod gave the camera back.
        self.held = None
        self.diagnostics = CollisionDiagnostics(note, status)

    @property
    def note(self):
        return self.diagnostics.note

    @note.setter
    def note(self, value):
        self.diagnostics.note = value

    def start(self, library, pc, manager):
        if self.release_pending and not self.busy:
            self.release()
        if self.callback is not None:
            raise RuntimeError('Camera collision cleanup required')
        self.lifetime.bind(pc, pc.OakCharacter, manager)
        if any(address < MIN_POINTER for address in self.lifetime.ids):
            raise ValueError('Invalid collision identity')
        self._give_back()
        self.diagnostics.reset()
        self.thread = threading.get_ident()
        library.view_set_collision.argtypes = [Callback]
        library.view_set_collision.restype = ctypes.c_int
        self.callback = Callback(self._resolve)
        if library.view_set_collision(self.callback):
            raise RuntimeError('Camera collision registration refused')

    def release(self):
        self.held = None
        # Only CameraBridge calls this after the native hook has stopped successfully.
        # A reentrant stop must not free a libffi thunk while its epilogue is executing.
        if self.busy:
            self.release_pending = True
            return
        self.release_pending = False
        self.callback = self.thread = None
        self.lifetime.clear()
        self.invalidate()

    def invalidate(self):
        self.clearance.clear()

    def _give_back(self):
        self.invalidate()
        self.held = None

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
        if self.busy or self.thread != threading.get_ident() or not pointer or not output:
            return 1
        self.busy = True
        started = time.perf_counter_ns()
        try:
            query = pointer.contents
            actor = self._owned(query)
            manager = self.lifetime.owned()[1]
            if str(manager.GetActorCameraMode(actor)) != THIRD_PERSON_MODE:
                self._give_back()
                return 1  # Climbing, Orbit and the vehicle own this frame; not an incident.
            camera = point(tuple(query.before))
            here = actor.K2_GetActorLocation()
            hunter = point((here.X, here.Y, here.Z))
            if folded(camera, hunter):
                raise ValueError("camera folded onto the hunter")
            self._measure(actor, manager, camera, hunter)
            self._owned(query)
            for index, value in enumerate(camera):
                output[index] = value
            now = time.perf_counter_ns()
            self.held = camera, now
            self.diagnostics.record(now, now - started)
            return 0
        except Exception as error:
            self.invalidate()
            now = time.perf_counter_ns()
            if self.held is not None and now - self.held[1] > config.HOLD_NS:
                self.held = None
            self.diagnostics.record(now, now - started, error=error, held=self.held is not None)
            if self.held is None:
                return 1
            for index, value in enumerate(self.held[0]):
                output[index] = value
            return 0
        finally:
            self.busy = False

    def _measure(self, actor, manager, camera, hunter):
        """The shown side's room: the shoulder the game was given, swept from the hunter's line across the view at the
        camera's distance. The game's collision may already have pulled the camera in from a wall at its side, so the
        sweep starts on that line, not at the camera, and still meets the wall."""
        applied = self.shoulder.applied
        if applied is None or abs(applied[0]) <= config.MIN_LENGTH:
            self.clearance.clear()
            return
        yaw = math.radians(float(manager.GetCameraRotation().Yaw))
        right = (-math.sin(yaw), math.cos(yaw), 0.0)
        across = sum((c - h) * r for c, h, r in zip(camera, hunter, right))
        anchor = tuple(c - across * r for c, r in zip(camera, right))
        desired = tuple(a + applied[0] * r for a, r in zip(anchor, right))
        try:
            distance = self.sweep.distance(actor, anchor, desired)
            self.clearance.record(self.sweep, actor, manager, anchor, desired, distance, camera)
        except ValueError:
            # A sweep starting inside a wall proves nothing about the room; the camera itself is the game's and stays.
            self.clearance.clear()
