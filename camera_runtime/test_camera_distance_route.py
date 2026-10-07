"""The camera distance key: the elected owner only, on foot in third person; it saves the next distance, which the
camera offset then applies."""

import unittest
from types import SimpleNamespace as NS

from camera_test_fixtures import Bridge, Hooks, Manager, Settings
from apex_camera_runtime import camera_distance_route
from apex_camera_runtime.camera_distance import CLOSE, FAR, NORMAL, offset
from apex_camera_runtime.third_person import ThirdPersonController

FRAME_NS = 16_666_667


class DistanceSettings(Settings):
    def __init__(self):
        super().__init__()
        self.index, self.saves = NORMAL, []

    def camera_distance(self):
        return self.index

    def set_camera_distance(self, value):
        self.saves.append(value)
        self.index = value


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.now, self.lines = [0], []
        self.hooks, self.manager, self.settings = Hooks(), Manager(), DistanceSettings()
        self.animation = object()
        movement = NS(bIsSprinting=False, MovementMode="EMovementMode.MOVE_Walking", Velocity=NS(X=0.0, Y=0.0, Z=0.0),
                      IsPerformingControlledMove=lambda: False, ControlledMoveReplicationData=NS(ControlledMove=None))
        self.actor = NS(Mesh=NS(GetAnimInstance=lambda: self.animation), ZoomState=NS(bWantsToZoom=False,
                        State=NS(name="NotZoomed")), CharacterMovement=movement, bIsCrouched=False)
        self.offset = NS(X=0.0, Y=0.0, Z=0.0)
        self.manager.CameraModeState = NS(CameraLocationOffset=self.offset)
        self.manager.GetCameraRotation = lambda: NS(Pitch=0.0, Yaw=0.0, Roll=0.0)
        self.pc = NS(OakCharacter=self.actor, PlayerCameraManager=self.manager,
                     ClientSetCameraMode=lambda mode: setattr(self.manager, "mode", mode))
        self.controller = ThirdPersonController(self.hooks, Bridge(), "distance-test", log=self.lines.append,
                                                clock=lambda: self.now[0])
        self.controller.sync("test", self.pc, self.settings, 1)
        self.client = NS(owner="apex_movement", settings=self.settings)
        self.runtime = NS(arbiter=NS(active=lambda: self.client), third_person=self.controller)

    def frames(self, count):
        hook = next(callback for (_path, kind, name), callback in self.hooks.items.items()
                    if kind == Hooks.Type.POST and name.endswith(":camera_offset"))
        for _ in range(count):
            self.offset.X = self.offset.Y = self.offset.Z = 0.0
            self.now[0] += FRAME_NS
            hook(self.animation, None, None, None)

    def test_each_press_saves_the_next_distance_and_the_camera_follows(self):
        self.assertTrue(camera_distance_route.cycle(self.runtime, "apex_movement"))
        self.assertEqual(self.settings.saves, [FAR])
        self.assertEqual(self.lines[-1], "camera distance far")
        self.frames(60)
        self.assertAlmostEqual(self.offset.X, offset(FAR), places=3)
        self.assertTrue(camera_distance_route.cycle(self.runtime, "apex_movement"))
        self.assertEqual(self.settings.index, CLOSE)
        self.frames(60)
        self.assertAlmostEqual(self.offset.X, offset(CLOSE), places=3)

    def test_the_camera_follows_the_distances_set_on_the_page(self):
        self.settings.camera_distances = lambda: (125.0, 256.0, 450.0)
        self.assertTrue(camera_distance_route.cycle(self.runtime, "apex_movement"))
        self.frames(60)
        self.assertAlmostEqual(self.offset.X, 256.0 - 450.0, places=3)
        self.assertTrue(camera_distance_route.cycle(self.runtime, "apex_movement"))
        self.frames(60)
        self.assertAlmostEqual(self.offset.X, 256.0 - 125.0, places=3)

    def test_another_owner_is_refused(self):
        self.assertFalse(camera_distance_route.cycle(self.runtime, "omni_sprint"))
        self.assertEqual(self.settings.saves, [])

    def test_a_mod_older_than_the_key_is_refused(self):
        self.client.settings = Settings()
        self.assertFalse(camera_distance_route.cycle(self.runtime, "apex_movement"))

    def test_nothing_outside_third_person_on_foot(self):
        self.settings.enabled = False
        self.assertFalse(camera_distance_route.cycle(self.runtime, "apex_movement"))
        self.settings.enabled = True
        for name, value in (("_in_vehicle", True), ("_desired_mode", "Orbit")):
            previous = getattr(self.controller, name)
            setattr(self.controller, name, value)
            self.assertFalse(camera_distance_route.cycle(self.runtime, "apex_movement"), name)
            setattr(self.controller, name, previous)
        self.manager.mode = "Default"
        self.assertFalse(camera_distance_route.cycle(self.runtime, "apex_movement"))
        self.assertEqual(self.settings.saves, [])

    def test_a_failed_save_is_noted_and_refused(self):
        def fail(_value):
            raise RuntimeError("save refused")
        self.settings.set_camera_distance = fail
        self.assertFalse(camera_distance_route.cycle(self.runtime, "apex_movement"))
        self.assertEqual(self.settings.notes, ["camera distance shortcut: setting could not be saved"])


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
