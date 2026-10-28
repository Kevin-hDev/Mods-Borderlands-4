"""Validated native boundary for the hunter's beams on the crosshair's line in third person. There the game starts a
beam's query (Ohm I Got) from the hunter's own view point, parallel to the view, so it lands beside the crosshair on
the hunter's side (docs/investigations/third_person_fov/camera/2026-10-21-rayon-ohm-et-couteau.md). Same library as
the hunter's eyes (interaction_bridge.py), started after them with the same camera."""
import ctypes

from .interaction_bridge import Config

BEAM_CLASS = 'OakLightBeam'
STATE_FIELD, INSTIGATOR_FIELD = 'ClientState', 'instigator'
MAX_FIELD_OFFSET = 0x1000
MAX_POINTER = 2**64 - 1 - 0x2000


class BeamConfig(ctypes.Structure):
    _fields_ = [('camera', Config), ('beam_default', ctypes.c_uint64),
                ('instigator_offset', ctypes.c_uint32), ('reserved', ctypes.c_uint32)]


class Query(ctypes.Structure):
    _fields_ = [(name, ctypes.c_double * 3) for name in ('origin', 'direction')]


class BeamStats(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64)
                for name in ('calls', 'writes', 'bypassed', 'rejected_view', 'off_view', 'tick_ms')]
    _fields_ += [(name, ctypes.c_uint32) for name in ('active', 'installed')]
    _fields_ += [(name, Query) for name in ('before', 'after')]


def make_beam_config(camera, sdk):
    """The beam class's default object (its table is every beam's) and where a beam keeps its instigator, both from
    the SDK's own types: the native side only compares that field with the hunter."""
    beam_class = sdk.find_class(BEAM_CLASS)
    state = beam_class._find_prop(STATE_FIELD)
    who = state.Struct._find_prop(INSTIGATOR_FIELD)
    if str(state.Class.Name) != 'StructProperty' or str(who.Class.Name) != 'ObjectProperty':
        raise ValueError('Beam instigator layout unavailable')
    offset = state.Offset_Internal + who.Offset_Internal
    default = beam_class.ClassDefaultObject._get_address()
    if type(offset) is not int or not 0 < offset <= MAX_FIELD_OFFSET or offset % 8:
        raise ValueError('Invalid beam instigator offset')
    if type(default) is not int or not 0x10000 <= default <= MAX_POINTER or default % 8:
        raise ValueError('Invalid beam class default')
    return BeamConfig(camera, default, offset, 0)


class BeamBridge:
    def __init__(self, library):
        self.library = library
        library.beam_start.argtypes = [ctypes.POINTER(BeamConfig)]
        library.beam_start.restype = ctypes.c_int
        library.beam_stop.argtypes, library.beam_stop.restype = [], ctypes.c_int
        library.beam_stats.argtypes = [ctypes.POINTER(BeamStats)]
        library.beam_stats.restype = ctypes.c_int

    @staticmethod
    def _check(status):
        if status:
            raise RuntimeError(f'native beam operation refused ({status})')

    def start(self, config):
        self._check(self.library.beam_start(ctypes.byref(config)))

    def stop(self):
        self._check(self.library.beam_stop())

    def stats(self):
        result = BeamStats()
        self._check(self.library.beam_stats(ctypes.byref(result)))
        return result
