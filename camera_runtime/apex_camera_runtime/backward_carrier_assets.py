"""Create a private backward-run BlendSpace for the current player and weapon."""

import math
from itertools import islice

MAX_FIELDS = 96
MAX_SAMPLES = 64
MAX_LAYOUT_ITEMS = 2048
MAX_PATH = 512
TRANSIENT_FLAG = 0x40
SPRINT_SUFFIX = '_MoveSlope_Sprint'
MOVE_SUFFIX = '_Move'


def fields(owner):
    found = list(islice(owner._properties(), MAX_FIELDS + 1))
    if len(found) > MAX_FIELDS:
        raise ValueError('Animation schema is too large')
    return {str(item.Name): str(item.Class.Name) for item in found}


def same(left, right):
    return left is not None and right is not None and int(left._get_address()) == int(right._get_address())


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Invalid animation value')
    return float(value)


def samples(asset):
    found = asset.SampleData
    count = len(found)
    if count < 1 or count > MAX_SAMPLES:
        raise ValueError('Unexpected animation sample count')
    return [found[index] for index in range(count)]


def move_path(source):
    name = str(source.Name)
    if not name.startswith('BS_') or not name.endswith(SPRINT_SUFFIX):
        raise ValueError('Unsupported sprint resource')
    path = source._path_name()
    ending = '/' + name + '.' + name
    if (not isinstance(path, str) or len(path) > MAX_PATH or '..' in path
            or not path.startswith('/Game/') or not path.endswith(ending)
            or '/PlayerCharacters/' not in path or '/Animation/3rd/' not in path):
        raise ValueError('Unsupported sprint resource path')
    move_name = name[:-len(SPRINT_SUFFIX)] + MOVE_SUFFIX
    return path[:-len(ending)] + '/' + move_name + '.' + move_name


def direct_back_path(source):
    path = move_path(source)
    folder, _ = path.rsplit('/', 1)
    stem = str(source.Name)[3:-len(SPRINT_SUFFIX)]
    name = 'AS_' + stem + '_Run_B'
    return folder + '/' + name + '.' + name


def back_clip(move):
    if move is None or str(move.Class.Name) != 'BlendSpace':
        raise ValueError('Matching movement BlendSpace is unavailable')
    candidates = []
    for item in samples(move):
        position = item.SampleValue
        if abs(abs(finite(position.X)) - 180.0) > 1.0:
            continue
        clip = item.Animation
        if clip is None or str(clip.Class.Name) != 'AnimSequence' or not str(clip.Name).endswith('_Run_B'):
            continue
        candidates.append((finite(position.Y), clip))
    if not candidates:
        raise ValueError('No backward run in current movement BlendSpace')
    fastest = max(speed for speed, _ in candidates)
    chosen = [clip for speed, clip in candidates if speed == fastest]
    if any(not same(clip, chosen[0]) for clip in chosen):
        raise ValueError('Ambiguous backward run')
    return chosen[0]


def layout(asset):
    counts = (len(asset.GridSamples), len(asset.BlendSpaceData.Triangles),
              len(asset.BlendSpaceData.Segments))
    if any(value > MAX_LAYOUT_ITEMS for value in counts) or not any(counts):
        raise ValueError('Missing cooked animation layout')
    return counts


def build(source, owner, find, construct):
    path = move_path(source)
    expected = {'Skeleton': 'ObjectProperty', 'SampleData': 'ArrayProperty',
                'BlendParameters': 'StructProperty', 'GridSamples': 'ArrayProperty',
                'BlendSpaceData': 'StructProperty', 'AnimLength': 'FloatProperty',
                'bAllowMarkerBasedSync': 'BoolProperty'}
    actual = fields(source.Class)
    if str(source.Class.Name) != 'BlendSpace' or any(actual.get(k) != v for k, v in expected.items()):
        raise ValueError('Unsupported sprint BlendSpace schema')
    original = samples(source)
    original_clips = tuple(item.Animation for item in original)
    original_layout = layout(source)
    move = find('BlendSpace', path)
    if move is None:
        clip_path = direct_back_path(source)
        clip = find('AnimSequence', clip_path)
        if clip is None or clip._path_name() != clip_path or str(clip.Name) != clip_path.rsplit('/', 1)[1].split('.')[0]:
            raise ValueError('Matching backward sequence is unavailable')
    else:
        if move._path_name() != path or not same(move.Skeleton, source.Skeleton):
            raise ValueError('Matching movement resource is unavailable')
        clip = back_clip(move)
    clip_fields = fields(clip.Class)
    if (clip_fields.get('Skeleton') != 'ObjectProperty'
            or clip_fields.get('SequenceLength') != 'FloatProperty'
            or not same(source.Skeleton, clip.Skeleton)):
        raise ValueError('Backward run skeleton or schema mismatch')
    duration = finite(clip.SequenceLength)
    if duration <= 0:
        raise ValueError('Empty backward run')
    clone = construct(cls=source.Class, outer=owner, flags=TRANSIENT_FLAG, template_obj=source)
    if (clone is None or same(clone, source) or str(clone.Class.Name) != 'BlendSpace'
            or not same(clone.Skeleton, source.Skeleton) or layout(clone) != original_layout):
        raise ValueError('Private animation carrier is incomplete')
    copied = samples(clone)
    if len(copied) != len(original):
        raise ValueError('Private animation samples are incomplete')
    old_addresses = {int(item._get_address()) for item in original}
    if any(int(item._get_address()) in old_addresses for item in copied):
        raise ValueError('Private animation samples share game storage')
    for item in copied:
        item.Animation = clip
        item.RateScale = 1.0
    clone.AnimLength = duration
    clone.bAllowMarkerBasedSync = False
    if (any(not same(item.Animation, clip) or finite(item.RateScale) != 1.0 for item in copied)
            or finite(clone.AnimLength) != duration or clone.bAllowMarkerBasedSync):
        raise ValueError('Backward animation could not be assigned')
    if any(not same(item.Animation, old) for item, old in zip(original, original_clips)):
        raise ValueError('Original sprint animation changed')
    return clone
