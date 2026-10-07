"""The camera offset's one writer: in ThirdPerson the framing and the motion, the Orbit distance first when asked,
nothing written once nothing is asked, only its own write given back, a failure stopping it cleanly."""

import unittest
from types import SimpleNamespace as NS

from camera_test_fixtures import Bridge, Hooks, Manager, Settings
from apex_camera_runtime.third_person import ThirdPersonController

FRAME_NS = 16_666_667


class DynamicSettings(Settings):
    def __init__(self):
        super().__init__()
        self.strengths = (1.0, 1.0)

    def dynamic_camera(self):
        return self.strengths


def character(velocity=(1269.0, 0.0, 0.0), sprinting=True):
    movement = NS(bIsSprinting=sprinting, MovementMode="EMovementMode.MOVE_Walking",
                  Velocity=NS(X=velocity[0], Y=velocity[1], Z=velocity[2]),
                  IsPerformingControlledMove=lambda: False, ControlledMoveReplicationData=NS(ControlledMove=None))
    return movement


class OffsetTests(unittest.TestCase):
    def setUp(self):
        self.now = [0]
        self.hooks, self.manager, self.settings = Hooks(), Manager(), DynamicSettings()
        self.animation = object()
        self.actor = NS(Mesh=NS(GetAnimInstance=lambda: self.animation), ZoomState=NS(bWantsToZoom=False,
                        State=NS(name="NotZoomed")), CharacterMovement=character(), bIsCrouched=False)
        self.offset = NS(X=0.0, Y=0.0, Z=0.0)
        self.manager.CameraModeState = NS(CameraLocationOffset=self.offset)
        self.manager.GetCameraRotation = lambda: NS(Pitch=0.0, Yaw=0.0, Roll=0.0)
        self.pc = NS(OakCharacter=self.actor, PlayerCameraManager=self.manager,
                     ClientSetCameraMode=lambda mode: setattr(self.manager, "mode", mode))
        self.controller = ThirdPersonController(self.hooks, Bridge(), "offset-test", clock=lambda: self.now[0])
        self.controller.sync("test", self.pc, self.settings, 1)
        self.assertEqual(self.manager.mode, "ThirdPerson")

    def hook(self):
        callbacks = [callback for (_path, kind, name), callback in self.hooks.items.items()
                     if kind == Hooks.Type.POST and name.endswith(":camera_offset")]
        self.assertEqual(len(callbacks), 1)
        return callbacks[0]

    def frames(self, count, reset=True):
        hook = self.hook()
        for _ in range(count):
            # The game puts the offset back to zero before each frame (verified in game).
            if reset:
                self.offset.X = self.offset.Y = self.offset.Z = 0.0
            self.now[0] += FRAME_NS
            hook(self.animation, None, None, None)

    def test_running_in_third_person_moves_the_camera_back(self):
        self.frames(90)
        self.assertLess(self.offset.X, -55.0)
        self.assertEqual(self.controller.offset.written, {"X": self.offset.X, "Y": self.offset.Y, "Z": self.offset.Z})

    def test_another_animation_is_ignored(self):
        self.hook()(object(), None, None, None)
        self.assertIsNone(self.controller.offset.written)

    def test_a_new_animation_on_the_same_hunter_is_followed(self):
        # Hunter Change's looks give the hunter a new animation (verified in game, 2026-10-07).
        self.animation = object()
        self.frames(30)
        self.assertIsNone(self.controller.offset.written)
        self.controller.offset.sync(self.settings)
        self.frames(90)
        self.assertLess(self.offset.X, -55.0)

    def test_orbit_distance_comes_first_and_writes_x_only(self):
        self.frames(30)
        self.controller.zoom.wanted_x = lambda: 25.0
        self.offset.Y, self.offset.Z = 12.0, 5.0
        self.frames(1, reset=False)
        self.assertEqual((self.offset.X, self.offset.Y, self.offset.Z), (25.0, 12.0, 5.0))
        self.assertEqual(self.controller.offset.dynamic.framing.value, (0.0, 0.0))

    def test_leaving_third_person_gives_back_only_its_own_write(self):
        self.frames(30)
        self.offset.Y = 7.0
        self.manager.mode = "Default"
        self.frames(1, reset=False)
        self.assertEqual((self.offset.X, self.offset.Y), (0.0, 7.0))
        self.assertIsNone(self.controller.offset.written)
        self.offset.X = 91.0
        self.frames(1, reset=False)
        self.assertEqual(self.offset.X, 91.0)

    def test_switched_off_eases_back_then_leaves_the_camera_to_the_game(self):
        self.frames(60)
        self.settings.strengths = (0.0, 0.0)
        self.frames(6)
        self.assertLess(self.offset.X, -20.0)
        self.frames(120)
        self.assertIsNone(self.controller.offset.written)
        self.offset.X = 91.0
        self.frames(1, reset=False)
        self.assertEqual(self.offset.X, 91.0)

    def test_nothing_in_a_vehicle_nor_without_the_option(self):
        self.controller._in_vehicle = True
        self.frames(30)
        self.assertIsNone(self.controller.offset.written)
        self.controller._in_vehicle = False
        del self.settings.strengths
        self.settings.dynamic_camera = None
        self.frames(30)
        self.assertIsNone(self.controller.offset.written)

    def test_a_failed_frame_stops_the_writer_and_its_hook(self):
        self.frames(30)
        def broken():
            raise RuntimeError("rotation unavailable")
        self.manager.GetCameraRotation = broken
        self.frames(1, reset=False)
        self.assertFalse(any(name.endswith(":camera_offset") for _path, _kind, name in self.hooks.items))
        self.assertIsNone(self.controller.offset.written)

    def test_stop_gives_back_the_offset_and_the_hook(self):
        self.frames(30)
        self.controller.stop()
        self.assertEqual((self.offset.X, self.offset.Y, self.offset.Z), (0.0, 0.0, 0.0))
        self.assertFalse(self.hooks.items)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
