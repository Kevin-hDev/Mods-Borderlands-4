"""In-process console handoff experiment; messages target only this game's window."""

import ctypes
from ctypes import wintypes
import os

WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
KEYUP_BITS = (1 << 30) | (1 << 31)
MAPVK_VK_TO_VSC_EX = 4
MAPVK_VSC_TO_VK = 1
CONSOLE_SCAN = 0x29
ESCAPE, TILDE = 0x1B, 0xC0
DIGIT_NAMES = ("Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine")
# Unreal names -> Windows keys with layout-independent meanings. Tilde is resolved below.
KEY_NAMES = {
    "Tilde": TILDE, "BackSpace": 0x08, "Tab": 0x09, "Enter": 0x0D, "SpaceBar": 0x20,
    "PageUp": 0x21, "PageDown": 0x22, "End": 0x23, "Home": 0x24,
    "Left": 0x25, "Up": 0x26, "Right": 0x27, "Down": 0x28, "Insert": 0x2D, "Delete": 0x2E,
    **{f"F{i}": 0x6F + i for i in range(1, 25)},
    **{chr(i): i for i in range(ord("A"), ord("Z") + 1)},
    **{name: 0x30 + i for i, name in enumerate(DIGIT_NAMES)},
    **{f"NumPad{name}": 0x60 + i for i, name in enumerate(DIGIT_NAMES)},
}
EXTENDED_KEYS = frozenset(KEY_NAMES[name] for name in
                         ("PageUp", "PageDown", "End", "Home", "Left", "Up", "Right", "Down", "Insert", "Delete"))


class WindowKeys:
    def __init__(self):
        if os.name != "nt":
            raise RuntimeError("Unsupported platform")
        self.api = ctypes.WinDLL("user32", use_last_error=True)
        self.api.GetForegroundWindow.argtypes = []
        self.api.GetForegroundWindow.restype = wintypes.HWND
        self.api.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.api.GetWindowThreadProcessId.restype = wintypes.DWORD
        self.api.GetKeyboardLayout.argtypes = [wintypes.DWORD]
        self.api.GetKeyboardLayout.restype = wintypes.HANDLE
        self.api.MapVirtualKeyExW.argtypes = [wintypes.UINT, wintypes.UINT, wintypes.HANDLE]
        self.api.MapVirtualKeyExW.restype = wintypes.UINT
        self.api.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        self.api.PostMessageW.restype = wintypes.BOOL
        self.window = self.api.GetForegroundWindow()
        self.pid = os.getpid()
        self.check_target()

    def check_target(self):
        pid = wintypes.DWORD()
        thread = self.api.GetWindowThreadProcessId(self.window, ctypes.byref(pid))
        if (not self.window or self.window != self.api.GetForegroundWindow()
                or not thread or pid.value != self.pid):
            raise RuntimeError("Game window is not active")
        return thread

    def mapping(self, key):
        if type(key) is not int or key not in (ESCAPE, *KEY_NAMES.values()):
            raise ValueError("Unsupported console key")
        layout = self.api.GetKeyboardLayout(self.check_target())
        if not layout:
            raise RuntimeError("Keyboard layout unavailable")
        if key == TILDE:
            # BL4's console key is physical scan 0x29: US `, French ².
            # Hardcoding VK_OEM_3 sends ù on French keyboards (measured live).
            key = self.api.MapVirtualKeyExW(CONSOLE_SCAN, MAPVK_VSC_TO_VK, layout)
        if not 0 < key <= 0xFF:
            raise RuntimeError("Console key mapping unavailable")
        scan = self.api.MapVirtualKeyExW(key, MAPVK_VK_TO_VSC_EX, layout)
        if not 0 < (scan & 0xFF) <= 0xFF or scan >> 8 not in (0, 0xE0):
            raise RuntimeError("Unsupported keyboard mapping")
        # Windows on the test machine omits E0 for navigation keys even in EX mode.
        if key in EXTENDED_KEYS:
            scan |= 0xE000
        return key, scan

    def tap(self, key):
        key, scan = self.mapping(key)
        # Navigation keys need the extended bit; without it Insert becomes numpad zero.
        down = 1 | ((scan & 0xFF) << 16) | ((scan >> 8 == 0xE0) << 24)
        # Always release a posted press, even if focus changes immediately afterwards.
        if not self.api.PostMessageW(self.window, WM_KEYDOWN, key, down):
            raise RuntimeError("Console key could not be queued")
        if not self.api.PostMessageW(self.window, WM_KEYUP, key, down | KEYUP_BITS):
            raise RuntimeError("Console key release could not be queued")


def configured_key(name):
    if type(name) is not str or name not in KEY_NAMES:
        raise ValueError("Console shortcut not supported by this experiment")
    return KEY_NAMES[name]
