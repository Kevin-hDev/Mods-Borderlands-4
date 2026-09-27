"""Range lifecycle stays independent from camera mode and failed setup is bounded."""
import unittest
from types import SimpleNamespace as NS
from apex_camera_runtime.cleanup_retry import CleanupRetry
from apex_camera_runtime.loot_unit import LootUnit
from apex_camera_runtime.loot_runtime import LootRuntime


class Unit:
    def __init__(self):
        self.pending = False
        self.values = []
        self.fail = False
        self.starts = 0

    def start(self, value):
        self.starts += 1
        self.pending = True
        if self.fail:
            raise RuntimeError('refused')
        self.values.append(value)

    def refresh(self, value):
        self.values.append(value)

    def stop(self):
        self.pending = False

    def reset_cleanup_context(self):
        pass


class Hooks:
    Type = NS(POST='post')

    def __init__(self): self.callbacks = {}
    def add_hook(self, _path, _kind, key, callback): self.callbacks[key] = callback
    def remove_hook(self, _path, _kind, key): self.callbacks.pop(key)
    def has_hook(self, _path, _kind, key): return key in self.callbacks


class FailingBridge:
    def __init__(self): self.failed = False
    def start(self, _distance): pass
    def refresh(self, _distance): pass
    def stop(self):
        if self.failed: raise RuntimeError('refused')


class Fields:
    def __init__(self): self.saved = {}; self.pending = False
    def apply(self, _value): self.pending = True
    def restore(self): self.pending = False


class RuntimeTests(unittest.TestCase):
    def test_mode_independent_and_option_off(self):
        unit = Unit()
        runtime = LootRuntime(lambda: unit)
        settings = NS(loot_distance=lambda: 660, note=lambda _: None)
        pc = NS(_get_address=lambda: 0x10000, OakCharacter=NS(_get_address=lambda: 0x20000))
        runtime.sync('a', pc, settings, 0)
        runtime.sync('a', pc, settings, 1)
        self.assertEqual(unit.values, [660])
        settings.loot_distance = lambda: 990
        runtime.sync('a', pc, settings, 2)
        self.assertEqual(unit.values, [660, 990])
        settings.loot_distance = lambda: 0
        runtime.sync('a', pc, settings, 3)
        self.assertFalse(unit.pending)

    def test_missing_player_releases_immediately(self):
        unit = Unit()
        runtime = LootRuntime(lambda: unit)
        settings = NS(loot_distance=lambda: 660, note=lambda _: None)
        pc = NS(_get_address=lambda: 0x10000, OakCharacter=NS(_get_address=lambda: 0x20000))
        runtime.sync('a', pc, settings, 0)
        runtime.sync('a', None, settings, 1)
        self.assertFalse(unit.pending)

    def test_failed_start_not_repeated_every_frame(self):
        unit = Unit()
        unit.fail = True
        runtime = LootRuntime(lambda: unit)
        settings = NS(loot_distance=lambda: 660, note=lambda _: None)
        pc = NS(_get_address=lambda: 0x10000, OakCharacter=NS(_get_address=lambda: 0x20000))
        for now in range(200):
            runtime.sync('a', pc, settings, now * 1_000_000_000)
        self.assertEqual(unit.starts, 1)
        self.assertFalse(unit.pending)

    def test_reenable_after_failure_retries_once(self):
        unit = Unit()
        unit.fail = True
        runtime = LootRuntime(lambda: unit)
        settings = NS(loot_distance=lambda: 660, note=lambda _: None)
        pc = NS(_get_address=lambda: 0x10000, OakCharacter=NS(_get_address=lambda: 0x20000))
        runtime.sync('a', pc, settings, 0)
        runtime.stop()
        unit.fail = False
        runtime.sync('a', pc, settings, 1)
        self.assertEqual(unit.starts, 2)
        self.assertEqual(unit.values, [660])

    def test_character_change_starts_new_unit_without_old_fields(self):
        unit = Unit()
        runtime = LootRuntime(lambda: unit)
        settings = NS(loot_distance=lambda: 660, note=lambda _: None)
        pc = NS(_get_address=lambda: 0x10000, OakCharacter=NS(_get_address=lambda: 0x20000))
        runtime.sync('a', pc, settings, 0)
        pc.OakCharacter = NS(_get_address=lambda: 0x30000)
        runtime.sync('a', pc, settings, 1)
        self.assertEqual(unit.starts, 2)

    def test_normal_multiplier_releases_override(self):
        unit = Unit()
        runtime = LootRuntime(lambda: unit)
        settings = NS(loot_distance=lambda: 660, note=lambda _: None)
        pc = NS(_get_address=lambda: 0x10000, OakCharacter=NS(_get_address=lambda: 0x20000))
        runtime.sync('a', pc, settings, 0)
        settings.loot_distance = lambda: 330
        runtime.sync('a', pc, settings, 1)
        self.assertFalse(unit.pending)

    def test_character_change_rearms_exhausted_cleanup(self):
        now, hooks, bridge, fields = [0], Hooks(), FailingBridge(), Fields()
        retry = CleanupRetry(hooks, 'loot', lambda: now[0], lambda _: None)
        unit = LootUnit(bridge, fields, retry, lambda: now[0], lambda _: None)
        runtime = LootRuntime(lambda: unit)
        settings = NS(loot_distance=lambda: 660, note=lambda _: None)
        pc = NS(_get_address=lambda: 0x10000, OakCharacter=NS(_get_address=lambda: 0x20000))
        runtime.sync('a', pc, settings, 0)
        bridge.failed = True
        pc.OakCharacter = NS(_get_address=lambda: 0x30000)
        runtime.sync('a', pc, settings, 1)
        for instant in (200_000_000, 1_000_000_000, 3_000_000_000):
            now[0] = instant
            for callback in tuple(hooks.callbacks.values()):
                callback(None, None, None, None)
        self.assertTrue(unit.pending)
        self.assertFalse(hooks.callbacks)
        settings.loot_distance = lambda: 0
        runtime.sync('a', pc, settings, 3_100_000_000)
        pc.OakCharacter = NS(_get_address=lambda: 0x40000)
        settings.loot_distance = lambda: 660
        runtime.sync('a', pc, settings, 4_000_000_000)
        bridge.failed = False
        now[0] = 4_200_000_000
        for callback in tuple(hooks.callbacks.values()):
            callback(None, None, None, None)
        self.assertFalse(unit.pending)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
