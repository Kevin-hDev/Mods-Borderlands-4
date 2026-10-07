"""Default camera keys named the way the game names them on the player's keyboard (Kevin, 2026-10-07).

The game (Unreal) names a letter or top-row key after the sign it types without Shift: on Kevin's AZERTY the 6 key is
Hyphen and the 7 key E_AccentGrave (his COMMANDS page, 2026-10-07), his 1 to 4 Ampersand, E_AccentAigu, Quote and
Apostrophe (verified in game, 2026-09-26). A default written "Six" never fires there, so each default names a place
on the keyboard and Windows says which sign sits there, before any game is loaded.
"""

import os

# Windows' scan codes: the same place on every keyboard.
RIGHT_OF_TAB = 0x10
TOP_ROW_SIX = 0x07
TOP_ROW_SEVEN = 0x08
TOP_ROW_EIGHT = 0x09
MAPVK_VSC_TO_VK = 1
MAPVK_VK_TO_CHAR = 2
# Set on a dead key (^ on AZERTY): it types nothing alone, the game gives it no usable name.
DEAD_KEY = 0x80000000

DIGITS = ("Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine")
# Unreal's names for the other signs a key can type unshifted (InputCoreTypes, EKeys).
SIGNS = {
    ";": "Semicolon", "=": "Equals", ",": "Comma", "-": "Hyphen", ".": "Period", "/": "Slash", "`": "Tilde",
    "[": "LeftBracket", "\\": "Backslash", "]": "RightBracket", "'": "Apostrophe", "&": "Ampersand",
    "*": "Asterix", "^": "Caret", ":": "Colon", "$": "Dollar", "!": "Exclamation", "(": "LeftParantheses",
    ")": "RightParantheses", '"': "Quote", "_": "Underscore", "à": "A_AccentGrave", "ç": "C_Cedille",
    "é": "E_AccentAigu", "è": "E_AccentGrave", "§": "Section",
}


def _windows_sign(scan: int) -> int:
    import ctypes
    from ctypes import wintypes
    api = ctypes.WinDLL("user32")
    api.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    api.GetKeyboardLayout.restype = wintypes.HANDLE
    api.MapVirtualKeyExW.argtypes = [wintypes.UINT, wintypes.UINT, wintypes.HANDLE]
    api.MapVirtualKeyExW.restype = wintypes.UINT
    # 0: the layout of the game's own thread, the one its keys go through.
    layout = api.GetKeyboardLayout(0)
    return api.MapVirtualKeyExW(api.MapVirtualKeyExW(scan, MAPVK_VSC_TO_VK, layout), MAPVK_VK_TO_CHAR, layout)


def name(code) -> str | None:
    """The game's name for the sign a key types (letters come as capitals), None when it has no known name."""
    if type(code) is not int or code <= 0 or code & DEAD_KEY or code > 0x10FFFF:
        return None
    sign = chr(code)
    if "A" <= sign <= "Z":
        return sign
    if "0" <= sign <= "9":
        return DIGITS[ord(sign) - ord("0")]
    return SIGNS.get(sign)


def key_at(scan: int, fallback: str, read=None) -> str:
    """read(scan) gives the sign typed there; without Windows' answer, the QWERTY name most players have."""
    if read is None:
        if os.name != "nt":
            return fallback
        read = _windows_sign
    try:
        code = read(scan)
    except (OSError, AttributeError, ValueError):
        return fallback
    return name(code) or fallback
