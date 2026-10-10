"""The camera guard hands the game's camera back unchanged, holds the last good camera through the vehicle climb's
folded frame and any failure right after a good frame, and reads the shown shoulder's room for the automatic
shoulder."""
import ctypes
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

from apex_camera_runtime import camera_guard, collision_config
from apex_camera_runtime.generated_ads import CollisionQuery
from apex_camera_runtime.shoulder_offset import ShoulderOffset


class Function:
    def __init__(self):
        self.callback = None

    def __call__(self, callback):
        self.callback = callback
        return 0


class SDK:
    @staticmethod
    def make_struct(_name, **values):
        return NS(**values)


class Physics:
    def __init__(self):
        self.distance, self.penetrating, self.lines = None, False, []

    def SphereTraceSingle(self, _actor, first, last, *_args):
        self.lines.append(((first.X, first.Y, first.Z), (last.X, last.Y, last.Z)))
        if self.penetrating:
            return True, NS(Distance=0.0, bStartPenetrating=True, PenetrationDepth=float('nan'))
        if self.distance is None:
            return False, NS()
        return True, NS(Distance=self.distance, bStartPenetrating=False)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.messages, self.physics = [], Physics()
        self.mode, self.hunter = 'ThirdPerson', [0.0, 0.0, 0.0]
        self.manager = NS(_get_address=lambda: 0x30000, GetActorCameraMode=lambda _: self.mode,
                          GetCameraRotation=lambda: NS(Yaw=0.0))
        self.actor = NS(_get_address=lambda: 0x20000,
                        K2_GetActorLocation=lambda: NS(X=self.hunter[0], Y=self.hunter[1], Z=self.hunter[2]))
        self.pc = NS(_get_address=lambda: 0x10000, OakCharacter=self.actor, PlayerCameraManager=self.manager)
        self.library = NS(view_set_collision=Function())
        self.shoulder = ShoulderOffset(clock=lambda: 0)
        self.guard = camera_guard.CameraGuard(self.physics, SDK, lambda x: lambda: x, self.messages.append,
                                              self.shoulder)
        self.guard.start(self.library, self.pc, self.manager)
        # Yaw 0 looks along +X: the camera stands behind the hunter and to its right (+Y).
        self.query = CollisionQuery(manager=0x30000, before=(-250, 92, 50), desired=(-250, 92, 50), delta=0.008)

    def invoke(self):
        output = (ctypes.c_double * 3)(-1, -1, -1)
        status = self.library.view_set_collision.callback(ctypes.pointer(self.query), output)
        return status, tuple(output)

    def test_the_games_camera_comes_back_unchanged(self):
        self.assertEqual(self.invoke(), (0, (-250, 92, 50)))
        self.assertEqual(self.physics.lines, [])
        self.assertEqual(self.guard.diagnostics.frames, 1)

    def test_the_vehicle_climb_keeps_the_last_good_camera(self):
        self.invoke()
        # The hunter walks on; the game folds its camera onto its head, 71 cm straight over its centre.
        self.hunter[:] = (7, -3, 0)
        self.query.before[:] = (7, -3, 71)
        self.assertEqual(self.invoke(), (0, (-250, 92, 50)))
        self.assertIn('previous position held: ValueError (camera folded onto the hunter)', self.messages[-1])
        self.pc.OakCharacter = NS(_get_address=lambda: 0x90000)
        self.assertEqual(self.invoke(), (0, (-250, 92, 50)))

    def test_a_camera_close_to_the_hunter_but_off_its_head_is_shown(self):
        self.invoke()
        for camera in ((-25, 0, 71), (0, -6, 71), (0, 0, 250)):
            self.query.before[:] = camera
            self.assertEqual(self.invoke(), (0, camera))
        self.assertEqual(self.guard.diagnostics.errors, 0)

    def test_the_fold_limits_hold_at_their_edges(self):
        across, reach = collision_config.FOLD_ACROSS_CM, collision_config.FOLD_REACH_CM
        self.assertTrue(camera_guard.folded((across, 0, 0), (0, 0, 0)))
        self.assertTrue(camera_guard.folded((0, 0, reach), (0, 0, 0)))
        self.assertFalse(camera_guard.folded((across + 0.1, 0, 0), (0, 0, 0)))
        self.assertFalse(camera_guard.folded((0, 0, reach + 0.1), (0, 0, 0)))

    def test_the_held_camera_expires_and_the_game_gets_its_camera_back(self):
        self.invoke()
        self.pc.OakCharacter = NS(_get_address=lambda: 0x90000)
        later = self.guard.held[1] + collision_config.HOLD_NS + 1
        with patch('apex_camera_runtime.camera_guard.time.perf_counter_ns', return_value=later):
            self.assertEqual(self.invoke(), (1, (-1, -1, -1)))
        self.assertIsNone(self.guard.held)

    def test_another_mode_gets_the_games_camera_and_drops_the_held_one(self):
        self.invoke()
        self.mode = 'Orbit'
        self.assertEqual(self.invoke(), (1, (-1, -1, -1)))
        self.assertIsNone(self.guard.held)

    def test_the_room_is_swept_from_the_hunters_line_with_the_shoulder_the_game_got(self):
        self.shoulder.show(61.5)
        self.shoulder.place(0.5, 0.0)
        self.physics.distance = 20.0
        self.invoke()
        self.assertEqual(self.physics.lines[0], ((-250, 0, 50), (-250, 92.25, 50)))
        self.assertAlmostEqual(self.guard.clearance.take().room, 20.0 / 92.25)

    def test_a_camera_the_game_pulled_in_from_a_side_wall_still_meets_the_wall(self):
        self.shoulder.show(61.5)
        self.shoulder.place(0.5, 0.0)
        self.physics.distance = 30.0
        self.query.before[:] = (-250, 30, 50)
        self.assertEqual(self.invoke(), (0, (-250, 30, 50)))
        self.assertEqual(self.physics.lines[0][0], (-250, 0, 50))
        self.assertLess(self.guard.clearance.take().room, 0.5)

    def test_no_shoulder_given_means_no_reading(self):
        self.assertEqual(self.invoke()[0], 0)
        self.assertIsNone(self.guard.clearance.take())

    def test_a_sweep_from_inside_a_wall_reads_nothing_and_keeps_the_games_camera(self):
        self.shoulder.show(61.5)
        self.shoulder.place(0.0, 0.0)
        self.physics.penetrating = True
        self.assertEqual(self.invoke(), (0, (-250, 92, 50)))
        self.assertIsNone(self.guard.clearance.take())
        self.assertEqual(self.messages[-1].split()[0], 'camera')

    def test_failures_without_a_good_frame_give_the_game_its_camera_and_a_generic_cause(self):
        self.pc.OakCharacter = NS(_get_address=lambda: 0x90000)
        for _ in range(20):
            self.assertEqual(self.invoke(), (1, (-1, -1, -1)))
        incidents = [line for line in self.messages if 'unavailable' in line]
        self.assertEqual(len(incidents), 1)
        self.assertIn('Camera collision identity unavailable', incidents[0])

    def test_release_forgets_the_held_camera(self):
        self.invoke()
        self.guard.release()
        self.assertIsNone(self.guard.held)
        self.assertIsNone(self.guard.callback)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
