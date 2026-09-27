"""Orbit distance belongs to one camera owner and cannot leak across interruptions."""

import unittest
from types import SimpleNamespace as NS

from camera_test_fixtures import Bridge, Hooks, Manager, Settings
from apex_camera_runtime.third_person import ThirdPersonController
from apex_camera_runtime.runtime import CameraRuntime


class ZoomSettings(Settings):
    def __init__(self):
        super().__init__()
        self.orbit = True
        self.distance = 300
        self.fail_save = False

    def orbit_distance(self):
        return self.distance

    def set_orbit_distance(self, value):
        if self.fail_save:
            raise RuntimeError("save refused")
        self.distance = value

    def note(self, _message):
        pass


class AddressAlias:
    def __init__(self, address):
        self.address = address

    def _get_address(self):
        return self.address


class ZoomTests(unittest.TestCase):
    def setUp(self):
        self.hooks, self.manager, self.settings = Hooks(), Manager(), ZoomSettings()
        self.animation = object()
        self.actor = NS(Mesh=NS(GetAnimInstance=lambda: self.animation), ZoomState=None)
        self.manager.CameraModeState = NS(CameraLocationOffset=NS(X=0., Y=12., Z=5.))
        self.pc = NS(OakCharacter=self.actor, PlayerCameraManager=self.manager,
                     ClientSetCameraMode=lambda mode: setattr(self.manager, "mode", mode))
        self.controller = ThirdPersonController(self.hooks, Bridge(), "zoom-test")
        self.runtime = CameraRuntime(NS(stop=lambda: None, apply=lambda *_args: None), self.controller)
        self.runtime.register("test", 200, self.settings)
        self.assertTrue(hasattr(self.runtime, "adjust_orbit_zoom"), "zoom action missing")
        self.controller.sync("test", self.pc, self.settings, 1)

    def frame(self, animation=None):
        callbacks = [callback for (path, kind, _), callback in self.hooks.items.items()
                     if path == "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
                     and kind == Hooks.Type.POST]
        self.assertEqual(len(callbacks), 1)
        callbacks[0](animation or self.animation, None, None, None)

    def test_steps_clamp_and_preserve_other_axes(self):
        self.assertFalse(self.runtime.adjust_orbit_zoom("other", -1))
        self.assertFalse(self.runtime.adjust_orbit_zoom("test", True))
        self.assertTrue(self.runtime.adjust_orbit_zoom("test", -1))
        self.frame()
        self.assertEqual(self.settings.distance, 275)
        offset = self.manager.CameraModeState.CameraLocationOffset
        self.assertEqual((offset.X, offset.Y, offset.Z), (25, 12, 5))
        for _ in range(30):
            self.runtime.adjust_orbit_zoom("test", -1)
        self.frame()
        self.assertEqual((self.settings.distance, offset.X), (75, 225))
        for _ in range(40):
            self.runtime.adjust_orbit_zoom("test", 1)
        self.frame()
        self.assertEqual((self.settings.distance, offset.X), (600, -300))

    def test_reassertion_and_animation_filter(self):
        self.runtime.adjust_orbit_zoom("test", 1)
        self.frame()
        offset = self.manager.CameraModeState.CameraLocationOffset
        offset.X = 0
        self.frame(object())
        self.assertEqual(offset.X, 0)
        self.frame()
        self.assertEqual(offset.X, -25)

    def test_interruption_does_not_erase_saved_distance_or_write_other_mode(self):
        self.runtime.adjust_orbit_zoom("test", -1)
        self.frame()
        offset = self.manager.CameraModeState.CameraLocationOffset
        for mode in ("Default", "Slide", "Vehicle", "ThirdPerson"):
            self.manager.mode = "Orbit"
            self.frame()
            self.manager.mode = mode
            self.frame()
            self.assertEqual(offset.X, 0)
            self.assertFalse(self.runtime.adjust_orbit_zoom("test", 1))
            offset.X = 91
            self.frame()
            self.assertEqual(offset.X, 91)
            self.assertEqual(self.settings.distance, 275)
        self.manager.mode = "Orbit"
        self.frame()
        self.assertEqual(offset.X, 25)

    def test_aim_and_pending_transition_refuse_zoom(self):
        for flag in ("_aiming", "_aim_returning", "_in_vehicle", "_recovery_requested"):
            setattr(self.controller, flag, True)
            self.assertFalse(self.runtime.adjust_orbit_zoom("test", -1))
            setattr(self.controller, flag, False)
        self.controller.foot_mode.begin("ThirdPerson", 2)
        self.assertFalse(self.runtime.adjust_orbit_zoom("test", -1))

    def test_failed_save_keeps_previous_distance_and_camera(self):
        self.runtime.adjust_orbit_zoom("test", -1)
        self.frame()
        self.settings.fail_save = True
        self.assertFalse(self.runtime.adjust_orbit_zoom("test", -1))
        self.frame()
        self.assertEqual(self.settings.distance, 275)
        self.assertEqual(self.manager.CameraModeState.CameraLocationOffset.X, 25)

    def test_stop_releases_offset_and_hook_without_changing_saved_distance(self):
        self.runtime.adjust_orbit_zoom("test", 1)
        self.frame()
        self.controller.stop()
        self.assertEqual(self.manager.CameraModeState.CameraLocationOffset.X, 0)
        self.assertEqual(self.settings.distance, 325)
        self.assertFalse(self.hooks.items)
        self.controller.sync("test", self.pc, self.settings, 10)
        self.frame()
        self.assertEqual(self.manager.CameraModeState.CameraLocationOffset.X, -25)

    def test_cleanup_does_not_overwrite_new_game_offset(self):
        self.runtime.adjust_orbit_zoom("test", 1)
        self.frame()
        self.manager.CameraModeState.CameraLocationOffset.X = 99
        self.controller.stop()
        self.assertEqual(self.manager.CameraModeState.CameraLocationOffset.X, 99)

    def test_lost_pawn_refuses_shortcuts(self):
        self.pc.OakCharacter = None
        self.assertFalse(self.runtime.adjust_orbit_zoom("test", -1))

    def test_changed_manager_refuses_shortcuts(self):
        self.pc.PlayerCameraManager = Manager()
        self.assertFalse(self.runtime.adjust_orbit_zoom("test", -1))

    def test_native_identity_accepts_different_wrappers(self):
        self.pc.OakCharacter = AddressAlias(id(self.actor))
        self.pc.PlayerCameraManager = AddressAlias(id(self.manager))
        self.runtime.adjust_orbit_zoom("test", -1)
        self.manager.CameraModeState.CameraLocationOffset.X = 0
        self.frame(AddressAlias(id(self.animation)))
        self.assertEqual(self.manager.CameraModeState.CameraLocationOffset.X, 25)

    def test_missing_animation_waits_then_installs_once(self):
        animation = [None]
        actor = NS(Mesh=NS(GetAnimInstance=lambda: animation[0]), ZoomState=None)
        manager, settings, hooks = Manager(), ZoomSettings(), Hooks()
        manager.CameraModeState = NS(CameraLocationOffset=NS(X=0., Y=0., Z=0.))
        pc = NS(OakCharacter=actor, PlayerCameraManager=manager,
                ClientSetCameraMode=lambda mode: setattr(manager, "mode", mode))
        controller = ThirdPersonController(hooks, Bridge(), "zoom-delayed-animation")
        for now in range(3):
            controller.sync("test", pc, settings, now)
        self.assertTrue(controller.cleanup_pending)
        self.assertFalse(any(name.endswith(":orbit_zoom") for _, _, name in hooks.items))
        animation[0] = object()
        controller.sync("test", pc, settings, 4)
        self.assertEqual(sum(name.endswith(":orbit_zoom") for _, _, name in hooks.items), 1)
        controller.stop()

    def test_owner_handoff_uses_each_saved_distance_without_an_early_write(self):
        self.runtime.tick(self.pc, 2)
        self.runtime.adjust_orbit_zoom("test", -1)
        self.frame()
        other = ZoomSettings()
        other.distance = 600
        self.runtime.register("other", 300, other)
        self.assertFalse(self.runtime.adjust_orbit_zoom("other", -1))
        self.assertFalse(self.runtime.adjust_orbit_zoom("test", -1))
        self.runtime.tick(self.pc, 3)
        self.frame()
        self.assertEqual(self.manager.CameraModeState.CameraLocationOffset.X, -300)
        self.runtime.unregister("other")
        self.runtime.tick(self.pc, 4)
        self.frame()
        self.assertEqual(self.manager.CameraModeState.CameraLocationOffset.X, 25)
        self.assertEqual((self.settings.distance, other.distance), (275, 600))

    def test_disabled_setting_stops_frame_writes_before_next_sync(self):
        self.runtime.adjust_orbit_zoom("test", -1)
        self.frame()
        self.settings.enabled = False
        self.frame()
        self.assertEqual(self.manager.CameraModeState.CameraLocationOffset.X, 0)

    def test_failed_frame_and_hook_removal_cannot_resume_zoom_writes(self):
        self.runtime.adjust_orbit_zoom("test", -1)
        self.frame()
        original = self.manager.CameraModeState
        self.manager.CameraModeState = None
        remove = self.hooks.remove_hook
        def fail(*args):
            raise RuntimeError("hook removal refused")
        self.hooks.remove_hook = fail
        callback = next(cb for (_path, _kind, name), cb in self.hooks.items.items()
                        if name.endswith(":orbit_zoom"))
        callback(self.animation, None, None, None)
        self.manager.CameraModeState = original
        self.manager.mode = "Orbit"
        original.CameraLocationOffset.X = 91
        callback(self.animation, None, None, None)
        self.assertEqual(original.CameraLocationOffset.X, 91)
        self.hooks.remove_hook = remove
        self.controller.stop()
        self.assertFalse(self.hooks.items)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
