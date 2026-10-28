"""Ownership reads must stop contention without turning wall proximity into a takeover."""

import importlib
import pathlib
import sys
import types
import unittest
from unittest.mock import patch

import sdk_stubs

state = sdk_stubs.install()
PACKAGE = "coordination_test_grapple"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(pathlib.Path(__file__).resolve().parent / "apex_grapple")]
sys.modules[PACKAGE] = package
try:
    coordination = importlib.import_module(f"{PACKAGE}.coordination")
except ModuleNotFoundError as exc:
    if exc.name != f"{PACKAGE}.coordination":
        raise
    coordination = None
report = importlib.import_module(f"{PACKAGE}.report")


class BrokenRules:
    @property
    def start(self):
        raise RuntimeError("private engine detail")


class BrokenMantle:
    @property
    def ActionIndex(self):
        raise RuntimeError("private engine detail")


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(coordination, "the shared takeover decision is missing")
        self.modules = patch.dict(sys.modules, {"apex_movement": None, "apex_wall_climb": None})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        report.reset()
        state["errors"].clear()
        self.movement = types.SimpleNamespace(ReplicatedMantleState=types.SimpleNamespace(ActionIndex=-1))
        self.character = types.SimpleNamespace(CharacterMovement=self.movement)

    def load(self, name="apex_movement", character=None, enabled=True, started=True):
        module = types.ModuleType(name)
        module.mod = types.SimpleNamespace(is_enabled=enabled)
        module.game = types.SimpleNamespace(character=lambda: self.character if character is None else character)
        module.wall_climb = types.SimpleNamespace(_rules=types.SimpleNamespace(start=object() if started else None))
        module.settings = types.SimpleNamespace(wall_climb=types.SimpleNamespace(value=True))
        sys.modules[name] = module
        return module

    def test_absent_mods_are_not_imported(self):
        self.assertIsNone(coordination.takeover(self.character))
        self.assertIsNone(sys.modules["apex_movement"])
        self.assertIsNone(sys.modules["apex_wall_climb"])

    def test_each_built_package_reports_real_climb(self):
        for name in ("apex_movement", "apex_wall_climb"):
            with self.subTest(name=name):
                module = self.load(name)
                self.assertEqual(coordination.takeover(self.character), "wall climb")
                module.mod.is_enabled = False

    def test_disabled_module_with_stale_climb_is_ignored(self):
        module = self.load(enabled=False)
        module.wall_climb._rules = BrokenRules()
        self.assertIsNone(coordination.takeover(self.character))
        self.assertEqual(state["errors"], [])

    def test_different_character_does_not_own_this_rope(self):
        module = self.load(character=object())
        module.wall_climb._rules = BrokenRules()
        self.assertIsNone(coordination.takeover(self.character))

    def test_menu_switch_off_does_not_preempt_deferred_stop(self):
        module = self.load()
        module.settings.wall_climb.value = False
        self.assertEqual(coordination.takeover(self.character), "wall climb")

    def test_wall_proximity_and_idle_rules_do_not_cut(self):
        self.load(started=False)
        self.movement.LadderState = types.SimpleNamespace(OverlappingClimbables=[object()])
        self.assertIsNone(coordination.takeover(self.character))

    def test_dash_slide_and_custom_modes_are_not_generalized(self):
        self.movement.IsPerformingControlledMove = lambda: True
        self.movement.MovementMode = "MOVE_Custom"
        self.assertIsNone(coordination.takeover(self.character))

    def test_module_without_stable_mod_root_is_ignored(self):
        module = self.load()
        del module.mod
        self.assertIsNone(coordination.takeover(self.character))
        module.mod = None
        self.assertIsNone(coordination.takeover(self.character))

    def test_active_same_character_with_missing_rules_is_unavailable(self):
        module = self.load()
        del module.wall_climb._rules
        self.assertEqual(coordination.takeover(self.character), "movement unavailable")
        self.assertEqual(len(state["errors"]), 1)

    def test_read_failure_blocks_once_without_sensitive_details(self):
        module = self.load()
        module.wall_climb._rules = BrokenRules()
        for _ in range(5):
            self.assertEqual(coordination.takeover(self.character), "movement unavailable")
        self.assertEqual(len(state["errors"]), 1)
        self.assertNotIn("private engine detail", state["errors"][0])

    def test_missing_character_reader_on_enabled_mod_is_unavailable(self):
        module = self.load()
        del module.game.character
        self.assertEqual(coordination.takeover(self.character), "movement unavailable")

    def test_no_current_character_in_other_mod_is_not_a_takeover(self):
        module = self.load()
        module.game.character = lambda: None
        self.assertIsNone(coordination.takeover(self.character))

    def test_mantle_boundaries_use_actual_action_index(self):
        for index, expected in ((-1, None), (0, "mantle"), (1, "mantle")):
            with self.subTest(index=index):
                self.movement.ReplicatedMantleState.ActionIndex = index
                self.assertEqual(coordination.takeover(self.character), expected)

    def test_missing_mantle_api_is_reported_once_as_unavailable_capability(self):
        del self.movement.ReplicatedMantleState
        for _ in range(5):
            self.assertIsNone(coordination.takeover(self.character))
        self.assertEqual(len(state["errors"]), 1)

    def test_mantle_read_error_blocks(self):
        self.movement.ReplicatedMantleState = BrokenMantle()
        self.assertEqual(coordination.takeover(self.character), "movement unavailable")
        self.assertEqual(len(state["errors"]), 1)

    def test_invalid_mantle_index_is_not_treated_as_free_movement(self):
        for index in ("bad index", "0", 0.5, True, None):
            with self.subTest(index=index):
                self.movement.ReplicatedMantleState.ActionIndex = index
                self.assertEqual(coordination.takeover(self.character), "movement unavailable")

    def test_missing_character_movement_is_not_a_missing_optional_api(self):
        self.character.CharacterMovement = None
        self.assertEqual(coordination.takeover(self.character), "movement unavailable")


if __name__ == "__main__":
    unittest.main(verbosity=2)
