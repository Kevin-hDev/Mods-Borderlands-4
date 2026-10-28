"""The framing at the wheel: its own clock while the elected mod's framing is on, back with the vehicle's speed,
written only while Vehicle Driving does not write, given back on foot, and a failure stopping it for that vehicle."""

import sys
import types
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

from camera_test_fixtures import Hooks
from apex_camera_runtime import frame_hooks, vehicle_framing, vehicle_share
from apex_camera_runtime.vehicle_framing import FRAME, IDENTIFIER, VehicleFraming

FRAME_NS = 16_666_667


class Settings:
    def __init__(self):
        self.strengths = (1.0, 1.0)

    def dynamic_camera(self):
        return self.strengths


def car(speed):
    return NS(OakVehicleMovement=object(), Mesh=NS(GetPhysicsLinearVelocity=lambda _bone: NS(X=speed, Y=0.0, Z=0.0)))


class OnFoot:
    """A character: no vehicle field, each question raising inside the SDK, and counted."""

    def __init__(self):
        self.Class = NS()
        self.asked = 0

    def __getattr__(self, name):
        if name == "OakVehicleMovement":
            self.__dict__["asked"] += 1
        raise AttributeError(name)


class VehicleFramingTests(unittest.TestCase):
    def setUp(self):
        sys.modules.pop(vehicle_share.SLOT, None)
        self.now, self.lines = [FRAME_NS], []
        self.hooks, self.settings = Hooks(), Settings()
        self.offset = NS(X=0.0, Y=0.0, Z=0.0)
        self.manager = NS(CameraModeState=NS(CameraLocationOffset=self.offset))
        self.pc = NS(Pawn=car(3000.0), PlayerCameraManager=self.manager)
        self.unit = VehicleFraming(lambda: (self.hooks, lambda possibly_loading: self.pc, lambda item: (lambda: item),
                                            id, lambda: self.now[0], self.lines.append))
        self.unit.sync(self.settings)

    def frames(self, count):
        for _ in range(count):
            # The game puts the offset back to zero before each frame (verified in game).
            self.offset.X = self.offset.Y = self.offset.Z = 0.0
            self.now[0] += FRAME_NS
            self.hooks.items[(FRAME, Hooks.Type.POST, IDENTIFIER)](object(), None, None, None)

    def test_the_clock_runs_only_while_the_framing_is_on(self):
        self.assertIn((FRAME, Hooks.Type.POST, IDENTIFIER), self.hooks.items)
        self.settings.strengths = (0.0, 1.0)
        self.unit.sync(self.settings)
        self.assertFalse(self.hooks.items)
        self.unit.sync(NS())
        self.assertFalse(self.hooks.items)

    def test_driving_fast_moves_the_camera_back_and_publishes_it(self):
        self.frames(60)
        self.assertAlmostEqual(self.offset.X, -80.0, delta=1.0)
        self.assertEqual((self.offset.X, self.offset.Y, self.offset.Z), vehicle_share.framing())
        self.assertEqual(self.lines, ["vehicle framing written by camera mods"])

    def test_the_same_frame_seen_again_is_skipped(self):
        self.frames(10)
        written = self.unit.written
        self.offset.X = 0.0
        self.hooks.items[(FRAME, Hooks.Type.POST, IDENTIFIER)](object(), None, None, None)
        self.assertEqual(self.offset.X, 0.0)
        self.assertEqual(self.unit.written, written)

    def test_vehicle_driving_writing_leaves_the_offset_to_it(self):
        self.frames(30)
        vehicle_share.claim()
        self.now[0] += FRAME_NS
        self.offset.X = 5.0
        self.hooks.items[(FRAME, Hooks.Type.POST, IDENTIFIER)](object(), None, None, None)
        self.assertEqual(self.offset.X, 5.0)
        self.assertLess(vehicle_share.framing()[0], -20.0)
        self.assertIsNone(self.unit.written)
        self.assertEqual(self.lines[-1], "vehicle framing written by Vehicle Driving")

    def test_on_foot_it_gives_back_its_write_and_publishes_nothing(self):
        self.frames(30)
        self.pc.Pawn = NS()
        self.now[0] += FRAME_NS
        self.hooks.items[(FRAME, Hooks.Type.POST, IDENTIFIER)](object(), None, None, None)
        self.assertEqual(self.offset.X, 0.0)
        self.assertEqual(vehicle_share.framing(), vehicle_share.ZERO)
        self.assertIsNone(self.unit.written)

    def test_switched_off_at_the_wheel_eases_back_then_writes_nothing(self):
        self.frames(60)
        self.settings.strengths = (0.0, 1.0)
        self.frames(6)
        self.assertLess(self.offset.X, -20.0)
        self.frames(120)
        self.assertIsNone(self.unit.written)
        self.assertEqual(self.offset.X, 0.0)

    def test_a_failure_stops_it_until_the_next_vehicle(self):
        self.frames(10)
        broken = self.pc.Pawn
        broken.Mesh = NS()
        self.frames(5)
        self.assertEqual(self.offset.X, 0.0)
        self.assertTrue(self.lines[-1].startswith("vehicle framing stopped until the next vehicle"))
        self.pc.Pawn = car(3000.0)
        self.frames(5)
        self.assertLess(self.offset.X, 0.0)

    def test_on_foot_the_character_is_asked_for_a_vehicle_field_once(self):
        # The question raised inside the SDK at every frame (2026-10-24).
        self.pc.Pawn = hunter = OnFoot()
        self.frames(10)
        self.assertEqual(hunter.asked, 1)
        self.assertIsNone(self.unit.written)

    def test_its_clock_goes_through_the_copy_s_shared_hook(self):
        sdk = types.ModuleType("unrealsdk")
        sdk.hooks, sdk.logging = Hooks(), NS(info=print, error=print)
        unreal = types.ModuleType("unrealsdk.unreal")
        unreal.WeakPointer = lambda item: (lambda: item)
        mods = types.ModuleType("mods_base")
        mods.get_pc = lambda possibly_loading=False: None
        with patch.dict(sys.modules, {"unrealsdk": sdk, "unrealsdk.unreal": unreal, "mods_base": mods}):
            self.assertIs(vehicle_framing.game_modules()[0], frame_hooks.front(sdk.hooks))

    def test_stop_removes_the_clock_and_gives_back_the_offset(self):
        self.frames(30)
        self.unit.stop()
        self.assertEqual(self.offset.X, 0.0)
        self.assertFalse(self.hooks.items)
        self.assertEqual(vehicle_share.framing(), vehicle_share.ZERO)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
