"""Use only the elected owner's loot settings; camera mode does not set loot reach."""
import math
from .loot_constants import BASE_DISTANCE, MAX_MULTIPLIER, REFRESH_NS


class LootRuntime:
    def __init__(self, factory):
        self.factory = factory
        self.unit = None
        self.key = None
        self.identity_context = None
        self.failed = False
        self.waiting = False
        self.state_failed = False
        self.next_ns = 0
        self.distance = 0

    def sync(self, owner, pc, settings, now_ns):
        try:
            self._sync(owner, pc, settings, now_ns)
        except Exception:
            if self.state_failed:
                return
            self.state_failed = True
            self.failed = True
            settings.note('loot state unavailable')
            try:
                self._release()
            except Exception:
                settings.note('loot restoration is pending')

    def _sync(self, owner, pc, settings, now_ns):
        getter = getattr(settings, 'loot_distance', lambda: 0)
        distance = getter()
        if (isinstance(distance, bool) or not isinstance(distance, (int, float))
                or not math.isfinite(distance)
                or (distance and not BASE_DISTANCE <= distance <= BASE_DISTANCE * MAX_MULTIPLIER)):
            distance = 0
        actor = getattr(pc, 'OakCharacter', None)
        identity = ((pc._get_address(), actor._get_address())
                    if actor is not None and distance > BASE_DISTANCE else None)
        wanted = (owner, identity, distance) if identity and distance > BASE_DISTANCE else None
        wanted_identity = wanted[:2] if wanted is not None else None
        if self.state_failed:
            self.key = None
            self.state_failed = False
        if wanted != self.key:
            previous_identity = self.key[:2] if self.key else None
            self.failed = False
            self.key = wanted
            self.next_ns = 0
            if wanted is None or previous_identity != wanted[:2]:
                if (wanted_identity is not None and self.identity_context is not None
                        and wanted_identity != self.identity_context
                        and self.unit is not None and self.unit.pending):
                    self.unit.reset_cleanup_context()
                if wanted_identity is not None:
                    self.identity_context = wanted_identity
                try:
                    self._release()
                except Exception:
                    self.waiting = True
                    settings.note('loot restoration is pending')
        if self.waiting:
            if self.unit is not None and self.unit.pending:
                return
            self.waiting = False
        if wanted is None or self.failed:
            return
        if now_ns < self.next_ns:
            return
        self.next_ns = now_ns + REFRESH_NS
        try:
            if self.unit is None:
                self.unit = self.factory()
            if not self.distance:
                if self.unit.pending:
                    return
                self.unit.start(distance)
            else:
                self.unit.refresh(distance)
            self.distance = distance
        except Exception:
            self.failed = True
            settings.note('loot range unavailable; toggle the option to retry')
            try:
                self._release()
            except Exception:
                settings.note('loot restoration is pending')

    def stop(self):
        self.key, self.failed, self.waiting = None, False, False
        self.state_failed = False
        try:
            self._release()
        finally:
            if self.unit is None or not self.unit.pending:
                self.identity_context = None

    def _release(self):
        self.distance = 0
        if self.unit is not None:
            self.unit.stop()
