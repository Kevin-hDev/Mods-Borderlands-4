"""The shared third-person unit is built as soon as the elected mod runs, first person included."""
import sys
import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime.setup_gate import SetupGate


class Setup:
    def __init__(self, fail=False):
        self.calls, self.fail = 0, fail

    def __call__(self, runtime):
        self.calls += 1
        if self.fail:
            raise RuntimeError("native library blocked")
        runtime.third_person = object()


class SetupGateTest(unittest.TestCase):
    def setUp(self):
        self.gate, self.runtime = SetupGate(), NS(third_person=None)

    def test_first_person_builds_the_unit_so_the_first_switch_does_not_wait(self):
        setup = Setup()
        self.assertIsNone(self.gate.prepare(self.runtime, "apex", False, setup))
        self.assertIsNotNone(self.runtime.third_person)
        self.gate.prepare(self.runtime, "apex", True, setup)
        self.assertEqual(setup.calls, 1)

    def test_an_early_failure_is_silent_tried_once_and_reported_on_the_first_request(self):
        setup = Setup(fail=True)
        for _ in range(3):
            self.assertIsNone(self.gate.prepare(self.runtime, "apex", False, setup))
        self.assertEqual(setup.calls, 1)
        self.assertIsInstance(self.gate.prepare(self.runtime, "apex", True, setup), RuntimeError)
        self.assertEqual(setup.calls, 2)

    def test_a_reported_failure_is_retried_only_when_the_view_is_asked_for_again(self):
        setup = Setup(fail=True)
        self.assertIsInstance(self.gate.prepare(self.runtime, "apex", True, setup), RuntimeError)
        self.assertIsNone(self.gate.prepare(self.runtime, "apex", True, setup))
        self.gate.prepare(self.runtime, "apex", False, setup)
        self.assertEqual(setup.calls, 1)
        self.assertIsInstance(self.gate.prepare(self.runtime, "apex", True, setup), RuntimeError)
        self.assertEqual(setup.calls, 2)

    def test_a_new_owner_gets_its_own_attempt(self):
        setup = Setup(fail=True)
        self.gate.prepare(self.runtime, "apex", False, setup)
        self.gate.forget("apex")
        self.gate.prepare(self.runtime, "omni", False, setup)
        self.assertEqual(setup.calls, 2)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1).result
    ok = result.wasSuccessful()
    print(f"RESULTAT: {'OK' if ok else 'ECHEC'} ({result.testsRun} tests)")
    sys.exit(0 if ok else 1)
