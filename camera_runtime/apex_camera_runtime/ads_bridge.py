"""One generated ctypes boundary for the optional native ADS presentation."""
import ctypes
from .ads_category import address
from .ads_feedback import NATIVE_FAILURES, exception_kind, native_failure_kind, native_status_code
from .ads_preflight import Preflight
from .generated_ads import AdsContext, AdsStats, ObjectId


class AdsBridge:
    def __init__(self, library, log=lambda _message: None):
        self.library = library
        self._log, self.reason = log, None
        self._prepared = None
        for name, arguments in (
            ("ads_verify_files", []),
            ("ads_prepare", []),
            ("ads_identify", [ctypes.c_uint64, ctypes.POINTER(ObjectId)]),
            ("ads_publish", [ctypes.POINTER(AdsContext)]),
            ("ads_clear", [ctypes.c_uint64]),
            ("ads_release", [ctypes.c_uint64]),
            ("ads_stats", [ctypes.POINTER(AdsStats)]),
        ):
            function = getattr(library, name)
            function.argtypes, function.restype = arguments, ctypes.c_int
        self._preflight = Preflight(library.ads_verify_files, log)

    def start_preflight(self):
        self._preflight.start()

    def prepare(self):
        if self._prepared is None:
            ready = self._preflight.result()
            if ready is None:
                return None
            # A partial native installation is terminal until a fresh game launch.
            self._prepared = False
            if not ready:
                self.reason = ("unavailable" if type(self._preflight.native_status) is int
                               and self._preflight.native_status in NATIVE_FAILURES
                               else "preparation_failed")
            else:
                try:
                    status = self.library.ads_prepare()
                    self._prepared = type(status) is int and status == 0
                    if not self._prepared:
                        self.reason = ("unavailable" if type(status) is int and status in NATIVE_FAILURES
                                       else "preparation_failed")
                        self._log(f"aiming installation refused reason={native_failure_kind(status)} "
                                  f"native_status={native_status_code(status)}")
                except Exception as error:
                    self._log(f"aiming installation refused error_type={exception_kind(error)}")
                if not self._prepared and self.reason is None:
                    self.reason = "preparation_failed"
        return self._prepared

    def identify(self, item):
        pointer = address(item)
        if self._prepared is not True:
            raise RuntimeError("Third-person aiming unavailable")
        output = ObjectId()
        if (self.library.ads_identify(pointer, ctypes.byref(output))
                or output.address != pointer or output.index < 0 or output.serial <= 0):
            raise RuntimeError("Third-person aiming reference unavailable")
        return output

    def publish(self, context):
        if not isinstance(context, AdsContext):
            raise ValueError("Invalid aiming context")
        if self._prepared is not True or self.library.ads_publish(ctypes.byref(context)):
            raise RuntimeError("Third-person aiming unavailable")

    def _generation_call(self, name, generation):
        if type(generation) is not int or not 0 < generation < (1 << 64):
            raise ValueError("Invalid aiming generation")
        if getattr(self.library, name)(generation):
            raise RuntimeError("Aiming cleanup unavailable")

    def release(self, generation):
        self._generation_call("ads_release", generation)

    def clear(self, generation):
        self._generation_call("ads_clear", generation)
        return not bool(self.stats().pending)

    def stats(self):
        result = AdsStats()
        if self.library.ads_stats(ctypes.byref(result)):
            raise RuntimeError("Aiming status unavailable")
        return result
