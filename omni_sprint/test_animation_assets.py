"""The published mod finds a matching backward clip and builds a private carrier."""

import copy
import sys
import types
import unittest

import sdk_stubs

sdk_stubs.install()

from omni_sprint import animation_assets  # noqa: E402


def property_(name, kind):
    return types.SimpleNamespace(Name=name, Class=types.SimpleNamespace(Name=kind))


def resource(name, path, cls, address, **values):
    fields = [property_(key, ('ObjectProperty' if key == 'Skeleton' else 'FloatProperty')) for key in values]
    return types.SimpleNamespace(Name=name, Class=types.SimpleNamespace(Name=cls, _properties=lambda: fields),
                                 _path_name=lambda: path, _get_address=lambda: address, **values)


def fixtures(weapon='RH'):
    folder = '/Game/DLC/Harmonica/PlayerCharacters/CorpoHacker/Animation/3rd/Rifle/_Shared'
    prefix = 'BS_' + weapon
    sprint_name = prefix + '_MoveSlope_Sprint'
    move_name = prefix + '_Move'
    skeleton = types.SimpleNamespace(_get_address=lambda: 10)
    clip = resource('AS_RH_Run_B', folder + '/AS_RH_Run_B.AS_RH_Run_B',
                    'AnimSequence', 20, Skeleton=skeleton, SequenceLength=0.666)
    forward = resource('AS_RH_Run_F', folder + '/AS_RH_Run_F.AS_RH_Run_F',
                       'AnimSequence', 21, Skeleton=skeleton, SequenceLength=0.75)
    def sample(anim, x, y, address):
        return types.SimpleNamespace(Animation=anim, RateScale=1.0,
            SampleValue=types.SimpleNamespace(X=x, Y=y, Z=0.0),
            _get_address=lambda: address, _type=types.SimpleNamespace(Name='BlendSample'))
    sprint_path = folder + '/' + sprint_name + '.' + sprint_name
    move_path = folder + '/' + move_name + '.' + move_name
    class_ = types.SimpleNamespace(Name='BlendSpace', _properties=lambda: [
        property_('Skeleton', 'ObjectProperty'), property_('SampleData', 'ArrayProperty'),
        property_('BlendParameters', 'StructProperty'), property_('GridSamples', 'ArrayProperty'),
        property_('BlendSpaceData', 'StructProperty'), property_('AnimLength', 'FloatProperty'),
        property_('bAllowMarkerBasedSync', 'BoolProperty')])
    source = types.SimpleNamespace(Name=sprint_name, Class=class_, _path_name=lambda: sprint_path,
        _get_address=lambda: 30, Skeleton=skeleton,
        SampleData=[sample(forward, 500, 0, 100), sample(forward, 720, 0, 101)],
        BlendParameters=[types.SimpleNamespace(X=0, Y=0, Z=0)] * 3,
        GridSamples=[], BlendSpaceData=types.SimpleNamespace(Triangles=[1], Segments=[]),
        AnimLength=0.75, bAllowMarkerBasedSync=True)
    move = types.SimpleNamespace(Name=move_name, Class=class_, _path_name=lambda: move_path,
        Skeleton=skeleton, SampleData=[sample(clip, 180, 470, 102),
                                      sample(clip, -180, 470, 103),
                                      sample(forward, 0, 470, 104)])
    return source, move, clip


class AssetTests(unittest.TestCase):
    def setUp(self):
        self.source, self.move, self.clip = fixtures()
        self.queries = []

    def find(self, kind, path):
        self.queries.append((kind, path))
        return self.move

    def construct(self, **kwargs):
        clone = copy.deepcopy(kwargs['template_obj'])
        clone._get_address = lambda: 31
        clone.Skeleton = self.source.Skeleton
        for index, item in enumerate(clone.SampleData):
            item._get_address = lambda i=index: 200 + i
        return clone

    def build(self, find=None, construct=None):
        return animation_assets.build(self.source, object(), find or self.find,
                                      construct or self.construct)

    def test_same_weapon_backward_clip_is_used_without_changing_source(self):
        original = self.source.SampleData[0].Animation
        clone = self.build()
        self.assertIs(clone.SampleData[0].Animation, self.clip)
        self.assertIs(self.source.SampleData[0].Animation, original)
        self.assertFalse(clone.bAllowMarkerBasedSync)
        self.assertEqual(clone.AnimLength, self.clip.SequenceLength)
        self.assertEqual(self.queries[0], ('BlendSpace', self.move._path_name()))

    def test_other_weapon_uses_its_own_move_resource(self):
        source, move, clip = fixtures('PS')
        self.source, self.move, self.clip = source, move, clip
        self.build()
        self.assertTrue(self.queries[0][1].endswith('/BS_PS_Move.BS_PS_Move'))

    def test_wrong_skeleton_refused_before_construction(self):
        self.clip.Skeleton = types.SimpleNamespace(_get_address=lambda: 99)
        with self.assertRaises(ValueError):
            self.build(construct=lambda **kwargs: self.fail('Must not construct'))

    def test_unavailable_move_is_refused(self):
        with self.assertRaises(ValueError):
            self.build(find=lambda *args: None)

    def test_loaded_backward_sequence_is_usable_without_loaded_move(self):
        def find(kind, path):
            if kind == 'AnimSequence' and path.endswith('/AS_RH_Run_B.AS_RH_Run_B'):
                return self.clip
            return None
        clone = self.build(find=find)
        self.assertIs(clone.SampleData[0].Animation, self.clip)

    def test_cooked_layout_missing_is_refused(self):
        def construct(**kwargs):
            clone = self.construct(**kwargs)
            clone.BlendSpaceData.Triangles = []
            return clone
        with self.assertRaises(ValueError):
            self.build(construct=construct)

    def test_shared_sample_storage_is_never_modified(self):
        original = self.source.SampleData[0].Animation
        def construct(**kwargs):
            clone = self.construct(**kwargs)
            clone.SampleData = self.source.SampleData
            return clone
        with self.assertRaises(ValueError):
            self.build(construct=construct)
        self.assertIs(self.source.SampleData[0].Animation, original)

    def test_unrecognised_asset_name_refused(self):
        self.source.Name = 'Unknown'
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.queries)


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(AssetTests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
