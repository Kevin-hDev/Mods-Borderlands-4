"""Coordinate optional ADS presentation without owning another camera or weapon state."""
import ctypes
from .ads_feedback import Feedback
from .ads_policy import decide
from .aiming import wants_to_aim
from .generated_ads import ADS_ABI, CATEGORY_HEAVY, CATEGORY_SNIPER, ERROR_CONTEXT, ERROR_IDENTITY, AdsContext, ObjectId


class AdsSession:
    def __init__(self, native, reader, log):
        self.native, self.reader = native, reader
        self.feedback = Feedback(log)
        self.wanted = self.effective = False
        self.trial = False
        self._snapshot = self._key = None
        self._blocked_key = None
        self._generation = self._counter = self._fov_baseline = 0
        self._published = self._thread_failed = False
        self._released = self._input_aim = False
        self._release_baseline = 0
        self._preflight_aim = False
        self.extra_zoom_pending = lambda: False

    def set_trial(self, enabled):
        if type(enabled) is not bool:
            raise ValueError("Invalid aiming trial")
        self.trial = enabled
        if not enabled:
            self.stop()

    @property
    def pending(self):
        if not self.native or not self._generation:
            return False
        try:
            return bool(self.native.stats().pending)
        except Exception as error:
            self.feedback.exception(self._key, "cleanup_failed", "pending", error)
            return True

    def stop(self):
        previous_key = self._key
        self.wanted = self.effective = self._published = False
        self._released = self._input_aim = False
        self._snapshot = self._key = None
        if self.reader is not None:
            self.reader.clear()
        if not self._generation or self.native is None:
            return True
        try:
            # Cleanup reports its own ownership validation, independently of the preceding frame.
            completed = self.native.clear(self._generation)
            if completed:
                if self.native.stats().error in (ERROR_IDENTITY, ERROR_CONTEXT):
                    self.feedback.report(previous_key, "owner_abandoned")
                self._generation = 0
            return completed
        except Exception as error:
            self.feedback.exception(None, "cleanup_failed", "clear", error)
            return False

    @staticmethod
    def _key_for(snapshot):
        return tuple((ref.address, ref.index, ref.serial) for ref in snapshot.references), snapshot.category

    def _enabled(self, settings):
        read = getattr(settings, "third_person_ads", None)
        value = read() if callable(read) else False
        return self.trial or value is True

    def prepare(self, pc, actor, manager, settings, *, foot_mode, vehicle, pending):
        self.feedback.begin_frame()
        previous = self.wanted
        self._input_aim = wants_to_aim(actor)
        if not self._input_aim:
            self._preflight_aim = False
            # One held press stays blocked; a fresh press must recapture all native identities.
            self._blocked_key = None
        self.effective = False
        if ((not self._input_aim and not self._published) or not self._enabled(settings)
                or foot_mode != "ThirdPerson" or vehicle or pending):
            if self.wanted or self._published or self._generation:
                self.stop()
            self.wanted = False
            return False
        if self._thread_failed:
            self.feedback.report(None, "wrong_thread", terminal=True)
            return False
        try:
            supported = self.native is not None and self.native.prepare()
        except Exception as error:
            self.wanted = False
            self.feedback.exception(None, "preparation_failed", "prepare", error)
            return False
        if supported is None:
            # Never switch presentation halfway through an aim begun before verification.
            self._preflight_aim = self._input_aim
            self.wanted = False
            return False
        if not supported:
            self.wanted = False
            self.feedback.report(None, getattr(self.native, "reason", None) or "unavailable", terminal=True)
            return False
        self.feedback.reason = None
        if self._preflight_aim:
            # Poll terminal failures during this press, but never change its native presentation halfway through.
            return False
        try:
            status = self.native.stats()
        except Exception as error:
            self.stop()
            self.feedback.exception(None, "reference_unavailable", "stats", error)
            return False
        if status.wrong_thread:
            self._thread_failed = True
            self.stop()
            self.feedback.report(None, "wrong_thread", terminal=True)
            return False
        if self._generation:
            if status.error in (ERROR_IDENTITY, ERROR_CONTEXT):
                self._blocked_key = self._key if self._input_aim else None
                refused_key = self._key
                self.stop()
                # Cleanup may log abandoned ownership; the visible status still explains the refusal.
                self.feedback.report(refused_key, "reference_unavailable")
                return False
            self.effective = (self._published and status.generation == self._generation
                              and status.fov_writes > self._fov_baseline and bool(status.active))
        snapshot = self.reader.read(pc, actor, manager)
        if snapshot is None:
            reason = self.reader.reason
            error_kind = getattr(self.reader, "error_kind", None)
            self.stop()
            # An absent animation is a normal reconstruction gap, not a camera shutdown.
            self.wanted = previous and reason == "animation_pending"
            self.feedback.report(None, "animation_pending" if self.wanted else
                                 "unknown_weapon" if reason == "unknown_weapon" else "reference_unavailable")
            if error_kind is not None:
                self.feedback.diagnostic("context", error_kind)
            return self.wanted
        decision = decide(aiming=True, enabled=True, category=snapshot.category,
                          foot_mode=foot_mode, vehicle=vehicle, pending=pending, supported=supported)
        if decision != "third":
            if previous or self._published:
                self.stop()
            self.wanted = False
            if snapshot.category != CATEGORY_SNIPER:
                self.feedback.report(self._key_for(snapshot),
                                     "heavy_native" if snapshot.category == CATEGORY_HEAVY else "unknown_weapon")
            return False
        key = self._key_for(snapshot)
        if key == self._blocked_key:
            self.wanted = False
            self.feedback.report(key, "reference_unavailable")
            return False
        if not self._input_aim and key != self._key:
            # Zoom-out belongs only to its already published weapon, never to a new hip-fire context.
            self.stop()
            return False
        if self._key is not None and key != self._key:
            if not self.stop():
                self.feedback.report(None, "cleanup_pending")
        self._snapshot, self._key, self.wanted = snapshot, key, True
        self._input_aim = wants_to_aim(actor)
        if not self._input_aim and self._published:
            try:
                if not self._released:
                    self.native.release(self._generation)
                    self._released = True
                    self._release_baseline = status.fov_writes
                # A fresh native write at scale 1 ends the weapon's own curve; no timer or second easing.
                if (status.generation == self._generation and status.active
                        and status.fov_writes > self._release_baseline and status.zoom_scale == 1.0
                        and not self.extra_zoom_pending()):
                    self.stop()
                    return False
            except Exception as error:
                self.stop()
                self.feedback.exception(None, "cleanup_failed", "release", error)
                return False
        return True

    def confirm(self, mode):
        if (not self.wanted or self._snapshot is None or mode != "ThirdPerson" or self.pending
                or (not self._input_aim and not self._published)):
            return False
        if self._published and (not self._released or not self._input_aim):
            return True
        if not self.reader.current(self._snapshot):
            refused_key = self._blocked_key = self._key
            error_kind = getattr(self.reader, "error_kind", None)
            self.stop()
            self.feedback.report(refused_key, "reference_unavailable")
            if error_kind is not None:
                self.feedback.diagnostic("confirm_context", error_kind)
            return False
        try:
            status = self.native.stats()
        except Exception as error:
            refused_key = self._blocked_key = self._key
            self.stop()
            self.feedback.exception(refused_key, "reference_unavailable", "confirm_stats", error)
            return False
        self._counter = max(self._counter, status.generation) + 1
        if self._counter >= (1 << 64) - 1:
            self.stop()
            self.feedback.report(self._key, "publication_refused")
            return False
        context = AdsContext(ADS_ABI, ctypes.sizeof(AdsContext), 1, 0, self._counter,
                             (ObjectId * 8)(*self._snapshot.references), self._snapshot.paths)
        try:
            self.native.publish(context)
        except Exception as error:
            refused_key = self._blocked_key = self._key
            self.stop()
            self.feedback.exception(refused_key, "publication_refused", "publish", error)
            return False
        self._generation = self._counter
        self._fov_baseline = status.fov_writes
        self._published = True
        self._released = False
        self.effective = False
        return True
