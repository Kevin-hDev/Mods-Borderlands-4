"""The shared runtime receives one native third-person controller."""

import pathlib
import sys
import types
import unittest
from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import bootstrap  # noqa: E402
from apex_camera_runtime.bootstrap import attach  # noqa: E402
from camera_test_fixtures import Hooks, Manager, Settings


class Runtime:
    third_person = None

    def set_third_person(self, controller):
        self.third_person = controller


class Function:
    def __init__(self, result=0):
        self.result = result

    def __call__(self, *_args):
        return self.result


library = types.SimpleNamespace(view_start=Function(), view_stop=Function(),
                                view_set_suspended=Function(), view_set_right=Function(True),
                                view_stats=Function())
interaction_library = types.SimpleNamespace(interaction_start=Function(), interaction_stop=Function(),
                                             interaction_stats=Function())
kismet = object()
sdk = types.SimpleNamespace(make_struct=lambda *_args, **kwargs: types.SimpleNamespace(**kwargs))

class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.runtime, self.messages = Runtime(), []

    def attach(self, alignment):
        return attach(self.runtime, library, alignment, Hooks(), sdk,
                      lambda item: lambda: item, kismet, self.messages.append)

    def assert_camera_works(self, controller):
        manager = Manager()
        manager._get_address = lambda: 0x30000
        actor = types.SimpleNamespace(_get_address=lambda: 0x20000)
        pc = types.SimpleNamespace(_get_address=lambda: 0x10000, OakCharacter=actor,
                                   PlayerCameraManager=manager)
        controller.sync('test', pc, Settings(), 1)
        self.assertEqual(manager.mode, 'ThirdPerson')
        controller.stop()
        self.assertFalse(controller.cleanup_pending)
        self.assertTrue(any('unavailable' in message for message in self.messages))

    def test_second_attach_reuses_one_controller(self):
        first = self.attach(interaction_library)
        self.assertIs(self.attach(interaction_library), first)
        self.assertIs(self.runtime.third_person, first)

    def test_ads_uses_the_same_library_and_stays_disabled_before_trial(self):
        exports = {name: Function() for name in
                   ("ads_prepare", "ads_identify", "ads_publish", "ads_clear", "ads_release", "ads_stats")}
        with patch.dict(library.__dict__, exports), \
                patch.dict(sdk.__dict__, {"find_all": lambda _: []}):
            controller = self.attach(interaction_library)
        self.assertIsNotNone(controller.ads)
        self.assertIs(controller.ads.native.library, library)
        self.assertFalse(controller.ads.trial)

    def test_missing_ads_exports_keep_existing_camera(self):
        controller = self.attach(None)
        self.assertIsNone(controller.ads)
        self.assert_camera_works(controller)

    def test_missing_interaction_library_keeps_camera(self):
        self.assert_camera_works(self.attach(None))

    def test_incompatible_interaction_exports_keep_camera(self):
        self.assert_camera_works(self.attach(types.SimpleNamespace()))
        self.assertTrue(any('interaction alignment setup failed: AttributeError' in message
                            for message in self.messages))

    def modules(self):
        sdk_module = types.ModuleType('unrealsdk')
        sdk_module.hooks = Hooks()
        sdk_module.logging = types.SimpleNamespace(info=self.messages.append)
        sdk_module.find_class = lambda _name: types.SimpleNamespace(ClassDefaultObject=kismet)
        unreal = types.ModuleType('unrealsdk.unreal')
        unreal.WeakPointer = lambda item: lambda: item
        mods = types.ModuleType('mods_base')
        mods.MODS_DIR = HERE
        return {'unrealsdk': sdk_module, 'unrealsdk.unreal': unreal, 'mods_base': mods}

    def test_alignment_load_failure_keeps_camera_and_does_not_loop_loading(self):
        with patch.dict(sys.modules, self.modules()), \
                patch.object(bootstrap, 'load_packaged_library', return_value=library), \
                patch.object(bootstrap, 'load_interaction_library', side_effect=OSError('missing')) as load:
            controller = bootstrap.ensure(self.runtime)
            self.assertTrue(any('interaction alignment load failed: OSError' in message
                                for message in self.messages))
            self.assert_camera_works(controller)
            self.assertIs(bootstrap.ensure(self.runtime), controller)
            self.assertEqual(load.call_count, 1)

    def test_framing_library_failure_still_blocks_camera(self):
        with patch.dict(sys.modules, self.modules()), \
                patch.object(bootstrap, 'load_packaged_library', side_effect=OSError('missing')):
            with self.assertRaises(OSError):
                bootstrap.ensure(self.runtime)
        self.assertIsNone(self.runtime.third_person)


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
