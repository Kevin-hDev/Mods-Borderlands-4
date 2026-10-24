"""The Free Look unit against a fake game: its own clock while a key is set, the hold time, aiming, a vehicle taken
during the hold, a mistake that stops it until the next character, and everything back when stopped."""

import sys
import types
import unittest
from collections import namedtuple
from unittest.mock import patch

from camera_test_fixtures import Hooks
from free_look_test_fixtures import MODES, Controller, Memory, Pawn, Sdk
from apex_camera_runtime import free_look, frame_hooks
from apex_camera_runtime.free_look import FRAME, IDENTIFIER, FreeLook

# free_look_options.Values, without the SDK's option classes it is made of.
Values = namedtuple("Values", "keys holds hold_s")

FRAME_NS = 16_000_000
HOLD = Values(keys=("A", "Gamepad_LeftThumbstick"), holds=(True, True), hold_s=0.20)


class Game:
    def __init__(self, pc):
        self.pc, self.memory, self.hooks, self.said, self.now = pc, Memory(), Hooks(), [], 0

    def load(self):
        return (Sdk(), self.memory, self.hooks, lambda possibly_loading=False: self.pc, lambda: self.now,
                self.said.append, id, lambda item: (lambda: item))

    def frames(self, unit, count):
        for _ in range(count):
            self.now += FRAME_NS
            unit.on_frame(None, None, None, None)


def started(pc, values=HOLD):
    game = Game(pc)
    unit = FreeLook(game.load)
    unit.sync(type("Settings", (), {"free_look": staticmethod(lambda: values)})())
    unit.foot.modes = MODES
    return unit, game


class OnFoot(Pawn):
    """A character: no vehicle field, each question raising inside the SDK, and counted."""

    def __init__(self):
        super().__init__(600.0)
        self.Class = types.SimpleNamespace()
        self.asked = 0

    def __getattr__(self, name):
        if name == "OakVehicleMovement":
            self.__dict__["asked"] += 1
        raise AttributeError(name)


class UnitTests(unittest.TestCase):
    def test_the_clock_runs_only_while_a_key_is_set(self):
        unit, game = started(Controller())
        self.assertIn((FRAME, "POST", IDENTIFIER), game.hooks.items)
        unit.sync(type("Settings", (), {"free_look": staticmethod(lambda: Values((None, None), (True, True), 0.2))})())
        self.assertEqual(game.hooks.items, {})

    def test_switched_off_it_stops_and_gives_the_camera_back(self):
        # free_look_options.values() is None while its switch is off (Kevin, 2026-10-08).
        pc = Controller("ThirdPerson")
        unit, game = started(pc)
        pc.held["A"] = 1.0
        game.frames(unit, 20)
        self.assertEqual(game.memory.method("ThirdPerson"), 1)
        unit.sync(type("Settings", (), {"free_look": staticmethod(lambda: None)})())
        self.assertEqual((game.hooks.items, game.memory.method("ThirdPerson")), ({}, 0))
        game.frames(unit, 20)
        self.assertEqual(game.memory.method("ThirdPerson"), 0)

    def test_held_past_the_hold_time_it_starts_and_the_release_puts_back(self):
        pc = Controller("ThirdPerson")
        unit, game = started(pc)
        pc.held["A"] = 1.0
        game.frames(unit, 10)
        self.assertEqual(game.memory.method("ThirdPerson"), 0)
        game.frames(unit, 10)
        self.assertEqual((game.memory.method("ThirdPerson"), game.said), (1, ["free look on foot"]))
        pc.held.clear()
        game.frames(unit, 2)
        self.assertEqual(game.memory.method("ThirdPerson"), 0)

    def test_aiming_ends_it(self):
        pc = Controller("ThirdPerson")
        unit, game = started(pc)
        pc.held["A"] = 1.0
        game.frames(unit, 20)
        pc.Pawn.ZoomState.bWantsToZoom = True
        game.frames(unit, 2)
        self.assertEqual(game.memory.method("ThirdPerson"), 0)

    def test_a_vehicle_taken_during_the_hold_gives_the_hunter_back_and_holds_the_vehicle(self):
        pc = Controller("ThirdPerson", speed=600.0)
        unit, game = started(pc)
        pc.held["A"] = 1.0
        game.frames(unit, 20)
        driver = Controller(speed=1500.0, vehicle_throttle=1.0)
        pc.Pawn, pc.OakCharacter = driver.Pawn, None
        game.frames(unit, 2)
        self.assertEqual((pc.ignores, game.memory.method("ThirdPerson")), ([True, False], 0))
        self.assertEqual(game.said[-1], "free look on wheel")

    def test_a_mistake_stops_it_until_the_next_character(self):
        pc = Controller("ThirdPerson")
        unit, game = started(pc)
        pc.held["A"] = 1.0
        pc.Pawn.GetLastMovementInputVector = None
        game.frames(unit, 20)
        self.assertTrue(game.said[-1].startswith("free look stopped"))
        self.assertEqual(game.memory.method("ThirdPerson"), 0)
        count = len(game.said)
        game.frames(unit, 5)
        self.assertEqual(len(game.said), count)

    def test_on_foot_the_character_is_asked_for_a_vehicle_field_once(self):
        # The question raised inside the SDK at every frame (2026-10-24).
        pc = Controller("ThirdPerson")
        pc.Pawn = pc.OakCharacter = OnFoot()
        unit, game = started(pc)
        pc.held["A"] = 1.0
        game.frames(unit, 20)
        self.assertEqual(game.said, ["free look on foot"])
        self.assertEqual(pc.Pawn.asked, 1)

    def test_its_clock_goes_through_the_copy_s_shared_hook(self):
        sdk = types.ModuleType("unrealsdk")
        sdk.hooks, sdk.logging = Hooks(), types.SimpleNamespace(info=print, error=print)
        unreal = types.ModuleType("unrealsdk.unreal")
        unreal.WeakPointer = lambda item: (lambda: item)
        mods = types.ModuleType("mods_base")
        mods.get_pc = lambda possibly_loading=False: None
        with patch.dict(sys.modules, {"unrealsdk": sdk, "unrealsdk.unreal": unreal, "mods_base": mods}):
            game = free_look.game_modules()
            self.assertIs(game[2], frame_hooks.front(sdk.hooks))
        self.assertIs(game[7], unreal.WeakPointer)

    def test_stop_puts_everything_back(self):
        pc = Controller("Default", speed=600.0)
        unit, game = started(pc)
        pc.held["A"] = 1.0
        game.frames(unit, 20)
        unit.stop()
        self.assertEqual((game.memory.method("ThirdPerson"), game.memory.method("Default")), (0, 0))
        self.assertEqual((pc.ignores, pc.PlayerCameraManager.layers, game.hooks.items), ([True, False], [], {}))


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
