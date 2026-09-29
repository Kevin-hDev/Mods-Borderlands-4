"""The keyboard key by default: the one right of Tab, named after the player's own keyboard layout.

Why, Kevin, 2026-09-25: "maintient A, c'est la seule qui est proche de la main" (French keyboard). The game names keys
after what they print: on an English keyboard the key at that place is Q, and A moves left there. Taken by name, A
would put the weapon away each time an English player strafes left; taken by place, it is A for Kevin and Q for most
players. That this key is free in the game: releves/apex_inputs_2026-09-16.log gives no action to A on Kevin's layout
(old install); free on other layouts too is inferred, not verified.
"""

import ctypes
from ctypes import wintypes
from typing import Any

# Windows' scan code of the key right of Tab, the same on every keyboard whatever it prints.
RIGHT_OF_TAB = 0x10
MAPVK_VSC_TO_VK = 1


def name_for(virtual_key: int) -> str | None:
    """The game's name for a Windows virtual key, for letters only: other keys have names this does not know."""
    return chr(virtual_key) if ord("A") <= virtual_key <= ord("Z") else None


def _windows() -> Any:
    api = ctypes.WinDLL("user32")
    api.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    api.GetKeyboardLayout.restype = wintypes.HANDLE
    api.MapVirtualKeyExW.argtypes = [wintypes.UINT, wintypes.UINT, wintypes.HANDLE]
    api.MapVirtualKeyExW.restype = wintypes.UINT
    return api


def default_key(api: Any = None) -> str | None:
    """The key right of Tab, or None when the layout cannot be read or puts no letter there: no key is safer than a
    key that may already move the player."""
    try:
        api = api if api is not None else _windows()
        layout = api.GetKeyboardLayout(0)
        return name_for(api.MapVirtualKeyExW(RIGHT_OF_TAB, MAPVK_VSC_TO_VK, layout))
    except (OSError, AttributeError, ValueError):
        return None
