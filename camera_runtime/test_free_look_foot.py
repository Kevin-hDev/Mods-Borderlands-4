"""Free Look on foot against a fake game: Fixed for the hold and back after, first person laid in third person and
slides refused, the run kept alone and turned by left and right, everything back when stopped."""

import unittest

from camera_test_fixtures import Hooks
from free_look_test_fixtures import MODES, Controller, Memory, Sdk
from apex_camera_runtime.free_look_foot import Foot

TRANSITION = "/Script/OakGame.OakPlayerController:CameraTransition"


def foot():
    memory, hooks, said = Memory(), Hooks(), []
    unit = Foot(Sdk(), memory, hooks, said.append)
    unit.modes = MODES
    return unit, memory, hooks


class ThirdPersonTests(unittest.TestCase):
    def test_the_hold_fixes_the_camera_and_the_release_puts_it_back_the_next_frame(self):
        unit, memory, _hooks = foot()
        pc = Controller("ThirdPerson")
        self.assertTrue(unit.begin(pc))
        self.assertEqual(memory.method("ThirdPerson"), 1)
        unit.release(pc)
        self.assertEqual(memory.method("ThirdPerson"), 1)
        self.assertEqual(pc.PlayerCameraManager.CameraModeState.bases, [0.0])
        unit.finish_return()
        self.assertEqual(memory.method("ThirdPerson"), 0)

    def test_orbit_and_other_cameras_are_left_alone(self):
        unit, memory, _hooks = foot()
        self.assertFalse(unit.begin(Controller("Orbit")))
        self.assertFalse(unit.begin(Controller("Slide")))
        self.assertEqual(memory.method("Orbit"), 1)

    def test_a_value_the_game_changed_is_not_overwritten(self):
        unit, memory, _hooks = foot()
        memory.methods[MODES.addresses["ThirdPerson"] + MODES.shape.method] = 2
        self.assertFalse(unit.begin(Controller("ThirdPerson")))
        self.assertEqual(memory.method("ThirdPerson"), 2)


class FirstPersonTests(unittest.TestCase):
    def test_third_person_is_laid_and_slides_are_refused_until_the_release(self):
        unit, memory, hooks = foot()
        pc = Controller("Default")
        self.assertTrue(unit.begin(pc))
        self.assertEqual(pc.PlayerCameraManager.GetActorCameraMode(pc.Pawn), "ThirdPerson")
        self.assertEqual((memory.method("ThirdPerson"), memory.method("Default")), (1, 1))
        callback = hooks.items[(TRANSITION, "PRE", "apex_camera_runtime:free_look_guard")]
        self.assertIs(callback(pc, type("Args", (), {"NewMode": "Slide"}), None, None), Hooks.Block)
        pc.Pawn.ZoomState.bWantsToZoom = True
        self.assertIsNone(callback(pc, type("Args", (), {"NewMode": "Default"}), None, None))
        unit.release(pc)
        unit.finish_return()
        self.assertEqual(pc.PlayerCameraManager.GetActorCameraMode(pc.Pawn), "Default")
        self.assertEqual((memory.method("ThirdPerson"), memory.method("Default")), (0, 0))
        self.assertEqual(hooks.items, {})


class RunTests(unittest.TestCase):
    def test_a_moving_hunter_runs_alone_and_right_turns_the_run(self):
        unit, _memory, _hooks = foot()
        pc = Controller("ThirdPerson", speed=600.0)
        unit.begin(pc)
        self.assertEqual(pc.ignores, [True])
        pc.held["D"] = 1.0
        unit.frame(pc, pc.value, 0.5)
        self.assertAlmostEqual(pc.view.Yaw, 45.0)
        self.assertEqual(pc.view.Pitch, 5.0)
        self.assertTrue(pc.Pawn.pushes[-1]["bForce"])
        unit.release(pc)
        self.assertEqual(pc.ignores, [True, False])

    def test_standing_still_keeps_the_game_movement(self):
        unit, _memory, _hooks = foot()
        pc = Controller("ThirdPerson", speed=0.0)
        unit.begin(pc)
        unit.frame(pc, pc.value, 0.5)
        self.assertEqual((pc.ignores, pc.Pawn.pushes), ([], []))


class StopTests(unittest.TestCase):
    def test_aborting_puts_everything_back_at_once(self):
        unit, memory, hooks = foot()
        pc = Controller("Default", speed=600.0)
        unit.begin(pc)
        unit.abort(pc)
        self.assertEqual(pc.ignores, [True, False])
        self.assertEqual((memory.method("ThirdPerson"), memory.method("Default")), (0, 0))
        self.assertEqual(pc.PlayerCameraManager.layers, [])
        self.assertEqual(hooks.items, {})

    def test_a_controller_that_is_gone_is_not_touched_but_the_values_go_back(self):
        unit, memory, _hooks = foot()
        pc = Controller("Default", speed=600.0)
        unit.begin(pc)
        unit.abort(None)
        self.assertEqual(pc.ignores, [True])
        self.assertEqual(pc.PlayerCameraManager.layers, ["ThirdPerson"])
        self.assertEqual((memory.method("ThirdPerson"), memory.method("Default")), (0, 0))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
