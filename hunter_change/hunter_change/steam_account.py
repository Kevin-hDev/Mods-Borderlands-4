"""Which Steam account the game plays with: the one module that asks.

Steam keeps the connected user's 32-bit account id as ActiveUser in the current user's registry while it runs. Added to
STEAM_BASE, it is the 64-bit number the game names that account's save folder with: read on Kevin's PC on 2026-09-29,
it named the folder of his current saves, not the older folder left by another account. The game can only load the
saves of the account it plays with, so a copy of a game in another account's folder is not the game's.
"""

STEAM_BASE = 76561197960265728  # an individual account's 64-bit Steam number is this plus its 32-bit id
STEAM_KEY = r"Software\Valve\Steam\ActiveProcess"


def connected() -> int | None:
    """The connected account's 64-bit number; None when it cannot be told: no registry module in the game's Python,
    no Steam key or value, or no user connected (0)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STEAM_KEY) as key:
            value, kind = winreg.QueryValueEx(key, "ActiveUser")
    except (ImportError, OSError):
        return None
    if kind != winreg.REG_DWORD or not isinstance(value, int) or not 0 < value < 2 ** 32:
        return None
    return STEAM_BASE + value
