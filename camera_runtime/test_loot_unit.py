"""Cleanup is independent for pickups/containers and survives the mod being disabled."""
import unittest
from types import SimpleNamespace as NS
from apex_camera_runtime.loot_unit import LootUnit
from apex_camera_runtime.loot_runtime import LootRuntime
from apex_camera_runtime.cleanup_retry import CleanupRetry
from apex_camera_runtime.runtime import CameraRuntime


class Hooks:
    Type = NS(POST='post')
    def __init__(self): self.callbacks = {}
    def add_hook(self, path, kind, key, callback): self.callbacks[key] = callback
    def remove_hook(self, path, kind, key): self.callbacks.pop(key)
    def has_hook(self, path, kind, key): return key in self.callbacks


class Bridge:
    def __init__(self): self.failed = False; self.stops = 0
    def start(self, distance): pass
    def refresh(self, distance): pass
    def stop(self):
        self.stops += 1
        if self.failed: raise RuntimeError('refused')


class Fields:
    def __init__(self): self.saved = {}; self.pending = False; self.failed = False
    def apply(self, value): self.pending = True
    def restore(self):
        if self.failed: raise RuntimeError('refused')
        self.pending = False


class UnitTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.hooks, self.bridge, self.fields = Hooks(), Bridge(), Fields()
        self.retry = CleanupRetry(self.hooks, 'loot', lambda: self.now, lambda _: None)
        self.unit = LootUnit(self.bridge, self.fields, self.retry, lambda: self.now, lambda _: None)
        self.unit.start(660)

    def test_native_failure_does_not_skip_fields(self):
        self.bridge.failed = True
        with self.assertRaises(RuntimeError): self.unit.stop()
        self.assertFalse(self.fields.pending)
        self.assertTrue(self.unit.pending)
        self.bridge.failed = False
        self.now = 200_000_000
        for callback in tuple(self.hooks.callbacks.values()): callback(None, None, None, None)
        self.assertFalse(self.unit.pending)
        self.assertFalse(self.hooks.callbacks)

    def test_cleanup_is_spaced_and_bounded(self):
        self.bridge.failed = True
        with self.assertRaises(RuntimeError): self.unit.stop()
        for _ in range(100): self.retry.retry(self.unit, 0)
        self.assertEqual(self.bridge.stops, 1)
        for now in (200_000_000, 1_000_000_000, 3_000_000_000):
            self.retry.retry(self.unit, now)
        self.assertEqual(self.bridge.stops, 4)
        self.assertFalse(self.hooks.callbacks)

    def test_field_failure_does_not_leave_pickup_hook_enabled(self):
        self.fields.failed = True
        with self.assertRaises(RuntimeError): self.unit.stop()
        self.assertFalse(self.unit.native_pending)
        self.assertTrue(self.fields.pending)

    def test_loot_failure_does_not_block_fov(self):
        applied = []
        runtime = CameraRuntime(NS(stop=lambda: None, apply=lambda *args: applied.append(args)))
        runtime.loot = LootRuntime(lambda: self.unit)
        settings = NS(loot_distance=lambda: 660, note=lambda _: None)
        runtime.register('owner', 1, settings)
        # A stale/missing address must not break the unrelated FOV update.
        runtime.tick(NS(Player='player', OakCharacter=object()), 0)
        self.assertEqual(len(applied), 1)

    def test_no_cleanup_hook_when_error_occurs_after_last_release(self):
        def released_then_failed():
            self.fields.pending = False
            raise RuntimeError('enumeration failed')
        self.fields.restore = released_then_failed
        with self.assertRaises(RuntimeError): self.unit.stop()
        self.assertFalse(self.unit.pending)
        self.assertFalse(self.hooks.callbacks)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
