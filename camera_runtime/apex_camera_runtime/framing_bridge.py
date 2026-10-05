"""The existing view bridge owns this optional atomic configuration."""
import ctypes
from .generated_ads import FramingContext


class FramingBridge:
    def __init__(self, library):
        self.library = library
        library.view_set_framing.argtypes = [ctypes.POINTER(FramingContext)]
        library.view_set_framing.restype = ctypes.c_int
        library.view_framing_status.argtypes = []
        library.view_framing_status.restype = ctypes.c_uint32
        library.view_framing_zoom_pending.argtypes = []
        library.view_framing_zoom_pending.restype = ctypes.c_bool

    def publish(self, context):
        if context is not None and not isinstance(context, FramingContext):
            raise ValueError("Invalid framing context")
        if self.library.view_set_framing(ctypes.byref(context) if context is not None else None):
            raise RuntimeError("Camera framing unavailable")

    def status(self):
        return int(self.library.view_framing_status())

    def zoom_pending(self):
        return bool(self.library.view_framing_zoom_pending())
