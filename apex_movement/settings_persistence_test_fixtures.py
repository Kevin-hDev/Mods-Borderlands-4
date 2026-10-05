"""Real Windows handles and the shared SDK-shaped persistence fixture."""
import ctypes
import os
import unittest
from ctypes import wintypes

def save_successfully(case):
    # Only this expected-success operation becomes an assertion; setup errors stay runner errors.
    try:
        case.mod.save_settings()
    except unittest.SkipTest:
        raise
    except Exception as error:
        case.fail(f"Settings save failed unexpectedly: {type(error).__name__}")


class PersistenceCase(unittest.TestCase):
    save_successfully = save_successfully

    def setUp(self):
        # Lazy fixture access lets the original tests reuse the assertion without an import cycle.
        from test_settings_persistence import Tests
        Tests.setUp(self)

    def assert_intact(self):
        from test_settings_persistence import Tests
        Tests.assert_intact(self)

    def save_failing(self, expected_type):
        try:
            self.mod.save_settings()
        except unittest.SkipTest:
            raise
        except Exception as error:
            self.assertTrue(isinstance(error, expected_type),
                            f"Expected {expected_type.__name__}, got {type(error).__name__}")
            return error
        self.fail(f"Expected settings save to fail with {expected_type.__name__}")


class WindowsReader:
    """Allow direct writes, but deny delete/replace while the handle is open."""
    def __init__(self, path):
        if os.name != "nt":
            raise unittest.SkipTest("Windows handle sharing is unavailable")
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateFileW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                                        wintypes.HANDLE)
        self.api.CreateFileW.restype = wintypes.HANDLE
        self.api.CloseHandle.argtypes = (wintypes.HANDLE,)
        self.api.CloseHandle.restype = wintypes.BOOL
        self.handle = self.api.CreateFileW(str(path), 0x80000000, 3, None, 3, 0x80, None)
        if self.handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self):
        if self.handle is not None:
            handle, self.handle = self.handle, None
            if not self.api.CloseHandle(handle):
                raise ctypes.WinError(ctypes.get_last_error())
