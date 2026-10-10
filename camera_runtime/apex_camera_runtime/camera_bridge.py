"""Keep framing usable without alignment; retain ownership of unsafe cleanup.

The game places the shoulder now (shoulder_offset.py, 2026-10-08): the native camera starts without one, and the
shoulder's side, swap time and glides go to the shoulder offset. The native camera still hears every suspension: its
aiming, framing zoom and the aim alignment (the hunter's eyes on the crosshair's line) read them.
"""
from .interaction_bridge import make_config
from .shoulder_offset import ShoulderOffset
from .transition_catalog import CLIMB_SECONDS

STARTED_MESSAGE = 'third person aim alignment installed'
STOPPED_MESSAGE = 'third person aim alignment released'
UNAVAILABLE_MESSAGE = ('WARNING: Aim alignment unavailable. '
                       'Third-person camera remains active; thrown objects and loot targeting may be offset.')


class CameraBridge:
    def __init__(self, view, interaction, log, collision=None, shoulder=None):
        self.view = view
        self.interaction = interaction
        self.log = log
        self.collision = collision
        self.shoulder = shoulder if shoulder is not None else ShoulderOffset()
        self._view_pending = False
        self._interaction_pending = False
        self._alignment_warned = False

    @property
    def library(self):
        # Existing consumers use the framing DLL's ABI, not the interaction DLL.
        return self.view.library

    @property
    def pending(self):
        return self._view_pending or self._interaction_pending

    def start(self, manager, right, pc):
        if self.pending:
            raise RuntimeError('Camera cleanup required')
        # A native start may partly succeed before raising: own it before calling.
        self._view_pending = True
        try:
            self.shoulder.reset()
            if not self.shoulder.show(right) or not self.view.start(manager):
                self.stop()
                return False
            if self.collision is not None:
                self.collision.start(self.library, pc, manager)
            self._start_alignment(pc, manager)
        except Exception:
            self.stop()
            raise
        return True

    def _start_alignment(self, pc, manager):
        if self.interaction is None:
            self._warn_alignment()
            return
        try:
            config = make_config(pc, manager, self.library)
            self._interaction_pending = True
            self.interaction.start(config)
        except Exception as error:
            # Degrade only after confirmed cleanup; otherwise keep the normal retry path.
            if self._interaction_pending:
                self.interaction.stop()
                self._interaction_pending = False
            self._warn_alignment(f'aim alignment refused: {type(error).__name__} ({error})')
            return
        self._alignment_warned = False
        self.log(STARTED_MESSAGE)

    def _warn_alignment(self, cause=None):
        if not self._alignment_warned:
            # The refusal code tells a moved game function from a camera that is not ready.
            if cause is not None:
                self.log(cause)
            self.log(UNAVAILABLE_MESSAGE)
            self._alignment_warned = True

    def stop(self):
        alignment_pending = self._interaction_pending
        errors = []
        for resource, flag in ((self.interaction, '_interaction_pending'),
                               (self.view, '_view_pending')):
            if not getattr(self, flag):
                continue
            try:
                resource.stop()
                if resource is self.view:
                    if self.collision is not None:
                        self.collision.release()
                    self.shoulder.reset()
                setattr(self, flag, False)
            except Exception as error:
                errors.append(error)
        if errors:
            raise RuntimeError('Camera cleanup incomplete') from errors[0]
        if alignment_pending:
            self.log(STOPPED_MESSAGE)

    def suspend(self, suspended):
        # The native aim alignment reads this state on each call, including ADS/vehicle/Orbit.
        self.view.suspend(suspended)
        self.shoulder.suspend(suspended)
        if suspended and self.collision is not None:
            self.collision.invalidate()

    def suspend_climb(self, suspended):
        self.view.suspend_climb(suspended)
        self.shoulder.suspend(suspended, CLIMB_SECONDS, climbing=suspended)
        if self.collision is not None:
            self.collision.invalidate()

    def suspend_orbit(self, suspended, seconds, permission):
        self.view.suspend_offset(suspended, seconds)
        self.shoulder.suspend(suspended, seconds, permission=permission)
        if self.collision is not None:
            self.collision.invalidate()

    def cancel_orbit_transition(self, suspended):
        if self.shoulder.permission is not None and self.shoulder.transition_active():
            self.suspend(suspended)

    def offset_transition_active(self):
        return self.shoulder.transition_active()

    def transition_duration(self, seconds):
        self.shoulder.transition_duration(seconds)

    def set_right(self, right):
        return self.shoulder.show(right)

    def stats(self):
        return self.view.stats()
