"""Keep framing usable without alignment; retain ownership of unsafe cleanup."""
from .interaction_bridge import make_config

STARTED_MESSAGE = 'third person interaction alignment installed'
STOPPED_MESSAGE = 'third person interaction alignment released'
UNAVAILABLE_MESSAGE = ('WARNING: Interaction alignment unavailable. '
                       'Third-person camera remains active; loot targeting may be offset.')


class CameraBridge:
    def __init__(self, view, interaction, log, collision=None):
        self.view = view
        self.interaction = interaction
        self.log = log
        self.collision = collision
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
            if not self.view.start(manager, right):
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
        except Exception:
            # Degrade only after confirmed cleanup; otherwise keep the normal retry path.
            if self._interaction_pending:
                self.interaction.stop()
                self._interaction_pending = False
            self._warn_alignment()
            return
        self._alignment_warned = False
        self.log(STARTED_MESSAGE)

    def _warn_alignment(self):
        if not self._alignment_warned:
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
                if resource is self.view and self.collision is not None:
                    self.collision.release()
                setattr(self, flag, False)
            except Exception as error:
                errors.append(error)
        if errors:
            raise RuntimeError('Camera cleanup incomplete') from errors[0]
        if alignment_pending:
            self.log(STOPPED_MESSAGE)

    def suspend(self, suspended):
        # The native interaction hook reads this state on each call, including ADS/vehicle/Orbit.
        self.view.suspend(suspended)
        if suspended and self.collision is not None:
            self.collision.invalidate()

    def set_right(self, right):
        return self.view.set_right(right)

    def stats(self):
        return self.view.stats()
