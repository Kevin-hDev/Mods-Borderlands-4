"""Which Steam account is connected: Steam's ActiveUser, read in the current user's registry key, as the 64-bit
number the save folders are named by; None when the key or the value is missing, when the value is 0 (no user), not
a 32-bit number, or when the game's Python has no registry module. No real registry read: winreg is faked."""

import sys
import types

import sdk_stubs

sdk_stubs.install()

from hunter_change import steam_account  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Key:
    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


def registry(value=None, kind=4, missing_key: bool = False, missing_value: bool = False) -> list:
    """A fake winreg holding ActiveUser as given; the list it returns records what was opened and asked."""
    asked: list = []
    fake = types.ModuleType("winreg")
    fake.HKEY_CURRENT_USER, fake.REG_DWORD, fake.REG_SZ = "HKCU", 4, 1

    def open_key(root, path):
        asked.append((root, path))
        if missing_key:
            raise FileNotFoundError(2, "The system cannot find the file specified")
        return Key()

    def query(key, name):
        asked.append(name)
        if missing_value:
            raise FileNotFoundError(2, "The system cannot find the file specified")
        return value, kind

    fake.OpenKey, fake.QueryValueEx = open_key, query
    sys.modules["winreg"] = fake
    return asked


asked = registry(12345)
check("the connected account as the 64-bit number of the save folders",
      steam_account.connected() == 76561197960265728 + 12345)
check("read from Steam's ActiveUser in the current user's key",
      asked == [("HKCU", r"Software\Valve\Steam\ActiveProcess"), "ActiveUser"])
registry(0)
check("no user connected (0): None", steam_account.connected() is None)
registry(2 ** 32)
check("more than 32 bits: None", steam_account.connected() is None)
registry("12345", kind=1)
check("a value that is not a number: None", steam_account.connected() is None)
registry(12345, kind=11)
check("a number that is not Steam's 32-bit kind: None", steam_account.connected() is None)
registry(missing_key=True)
check("no Steam key: None", steam_account.connected() is None)
registry(missing_value=True)
check("no ActiveUser: None", steam_account.connected() is None)
sys.modules["winreg"] = None
check("no registry module in the game's Python: None", steam_account.connected() is None)
del sys.modules["winreg"]

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
