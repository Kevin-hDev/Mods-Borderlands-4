"""The beam alignment boundary keeps its layout, reads the beam's instigator from the SDK's own types and refuses
any layout it cannot trust, and never hides a native refusal."""
import ctypes
from types import SimpleNamespace as NS
import unittest

from apex_camera_runtime import beam_bridge as bridge
from apex_camera_runtime.interaction_bridge import Config


class Function:
    status = 0

    def __call__(self, *args):
        self.last = args
        return self.status


def prop(kind, offset, struct=None):
    return NS(Class=NS(Name=kind), Offset_Internal=offset, Struct=struct)


def sdk(state_kind='StructProperty', who_kind='ObjectProperty', state_at=0x88, who_at=0x120, default=0x50000):
    who = prop(who_kind, who_at)
    state = prop(state_kind, state_at, NS(_find_prop=lambda name: who if name == 'instigator' else None))
    beam_class = NS(_find_prop=lambda name: state if name == 'ClientState' else None,
                    ClassDefaultObject=NS(_get_address=lambda: default))
    return NS(find_class=lambda name: beam_class if name == 'OakLightBeam' else None)


CAMERA = Config(5, 0, 0x10000, 0x20000, 0x30000, 0x40000)


class BeamBoundaryTests(unittest.TestCase):
    def test_layouts_match_the_native_side(self):
        self.assertEqual(ctypes.sizeof(bridge.BeamConfig), 56)
        self.assertEqual(ctypes.sizeof(bridge.Query), 48)
        self.assertEqual(ctypes.sizeof(bridge.BeamStats), 152)

    def test_config_reads_the_instigator_from_the_beam_types(self):
        config = bridge.make_beam_config(CAMERA, sdk())
        self.assertEqual((config.beam_default, config.instigator_offset, config.reserved), (0x50000, 0x1A8, 0))
        self.assertEqual((config.camera.pawn, config.camera.manager), (0x20000, 0x30000))

    def test_an_untrusted_layout_is_refused(self):
        for wrong in (dict(state_kind='ArrayProperty'), dict(who_kind='WeakObjectProperty'),
                      dict(who_at=0x121), dict(state_at=0x1000), dict(state_at=-0x200),
                      dict(default=0), dict(default=0x50004), dict(default=2**64), dict(default=True)):
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                bridge.make_beam_config(CAMERA, sdk(**wrong))

    def test_native_refusal_is_not_hidden(self):
        library = NS(beam_start=Function(), beam_stop=Function(), beam_stats=Function())
        api = bridge.BeamBridge(library)
        api.start(bridge.make_beam_config(CAMERA, sdk()))
        self.assertEqual(library.beam_start.last[0]._obj.instigator_offset, 0x1A8)
        self.assertIsInstance(api.stats(), bridge.BeamStats)
        library.beam_start.status = 5
        with self.assertRaisesRegex(RuntimeError, r'refused \(5\)$'):
            api.start(bridge.make_beam_config(CAMERA, sdk()))

    def test_a_library_without_beams_cannot_be_bound(self):
        with self.assertRaises(AttributeError):
            bridge.BeamBridge(NS(interaction_start=Function()))


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    raise SystemExit(not result.wasSuccessful())
