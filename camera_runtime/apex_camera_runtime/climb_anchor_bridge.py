"""Bound the animated anchor to SDK weak identities and native ownership."""
import ctypes

from .ads_category import address


class Statistics(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in (
        'calls', 'eligible', 'applied', 'refused', 'expired', 'active', 'installed', 'reserved')]


class NativeRefusal(RuntimeError):
    def __init__(self, stage, code):
        super().__init__('Climb anchor unavailable')
        self.stage, self.code = stage, int(code)


class ClimbAnchorBridge:
    def __init__(self, library, weak_ref):
        self.library, self.weak_ref = library, weak_ref
        for name, arguments in (
            ('anchor_start', [ctypes.c_uint64]), ('anchor_stop', []),
            ('anchor_refresh', []), ('anchor_stats', [ctypes.POINTER(Statistics)]),
        ):
            function = getattr(library, name)
            function.argtypes, function.restype = arguments, ctypes.c_int

    def start(self, manager):
        inputs = manager.CameraModeInputs
        controller = inputs.Controller
        actor = controller.Pawn
        objects = (manager, manager.CameraModeState, inputs, controller, actor, actor.Mesh)
        # WeakPointer initializes lazy serials before the native capture validates them.
        references = tuple(self.weak_ref(item) for item in objects)
        for item, reference in zip(objects, references):
            resolved = reference()
            if resolved is None or address(resolved) != address(item):
                raise RuntimeError('Climb anchor reference unavailable')
        status = self.library.anchor_start(address(manager))
        if status:
            raise NativeRefusal('start', status)

    def refresh(self):
        status = self.library.anchor_refresh()
        if status:
            raise NativeRefusal('refresh', status)

    def stop(self):
        status = self.library.anchor_stop()
        if status:
            raise NativeRefusal('stop', status)

    def stats(self):
        value = Statistics()
        if self.library.anchor_stats(ctypes.byref(value)):
            raise RuntimeError('Climb anchor statistics unavailable')
        return value
