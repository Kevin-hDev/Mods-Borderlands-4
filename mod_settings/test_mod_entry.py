# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of mod_settings/__init__.py, loaded from a .sdkmod (a zip read by zipimport, its constants read by pkgutil)
on a stand-in SDK: build_mod and the log only. The archive is built by deploy_sdkmods.py itself, so a file the tool
would leave out fails here; the public copy has no such tool and builds it by the tool's rule, and says so.

The SDK loads the mods on a thread of its own: so does this test. The start itself is tested apart
(test_game_thread_start.py, test_server.py): here the hook targets this test's main thread, which pumps no message,
so the start never runs and the test checks that turning the mod off cancels it. python test_mod_entry.py"""

import ctypes
import importlib
import sys
import tempfile
import threading
import types
import zipfile
from ctypes import wintypes
from pathlib import Path

import game_tools

HERE = Path(__file__).resolve().parent
TOOLS = game_tools.TOOLS
FAILURES = []


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


class FakeMod:
    def __init__(self, settings_file, **kwargs):
        self.kwargs = kwargs
        self.settings_file = settings_file
        self.is_enabled = False

    def enable(self):
        self.is_enabled = True
        self.kwargs["on_enable"]()

    def disable(self):
        self.is_enabled = False
        self.kwargs["on_disable"]()


def stand_in_sdk(logs, settings_file):
    unrealsdk = types.ModuleType("unrealsdk")
    unrealsdk.logging = types.SimpleNamespace(info=logs.append)
    mods_base = types.ModuleType("mods_base")
    mods_base.build_mod = lambda **kwargs: FakeMod(settings_file, **kwargs)
    sys.modules["unrealsdk"] = unrealsdk
    sys.modules["mods_base"] = mods_base


def built_sdkmod(folder: Path) -> Path:
    archive = folder / "mod_settings.sdkmod"
    if (TOOLS / "deploy_sdkmods.py").is_file():
        sys.path.insert(0, str(TOOLS))
        try:
            deploy_sdkmods = importlib.import_module("deploy_sdkmods")
        finally:
            sys.path.pop(0)
        files = deploy_sdkmods.package_files(str(HERE), "mod_settings")
        archive.write_bytes(deploy_sdkmods.build_sdkmod("mod_settings", str(HERE), files))
        return archive
    print("NOTE: deploy_sdkmods.py absent (public copy): archive built by its rule, modules and assets/ files")
    package = HERE / "mod_settings"
    with zipfile.ZipFile(archive, "w") as files:
        for path in sorted(package.rglob("*.py")) + sorted(package.glob("assets/*")):
            if path.is_file() and "__pycache__" not in path.parts:
                files.write(path, f"mod_settings/{path.relative_to(package).as_posix()}")
    return archive


def on_load_thread(action):
    """Runs action on a thread that ends right after, as the SDK's load thread does."""
    result, errors = [], []

    def run():
        try:
            result.append(action())
        except BaseException as error:
            errors.append(error)

    thread = threading.Thread(target=run)
    thread.start()
    thread.join(10)
    if errors:
        raise errors[0]
    return result[0] if result else None


def forget_the_mod():
    for name in [name for name in sys.modules if name == "mod_settings" or name.startswith("mod_settings.")]:
        del sys.modules[name]


# The game's thread has a message queue, which the start posts to: this test's main thread plays it, so it makes one.
ctypes.WinDLL("user32").PeekMessageW(ctypes.byref(wintypes.MSG()), None, 0, 0, 0)

with tempfile.TemporaryDirectory() as temp:
    folder = Path(temp)
    archive = built_sdkmod(folder)
    with zipfile.ZipFile(archive) as files:
        names = files.namelist()
    check("the archive holds the package and its constants only",
          "mod_settings/assets/mod_settings.constants.json" in names and "mod_settings/__init__.py" in names
          and not any("test_" in name or "fixture" in name or "__pycache__" in name for name in names))
    sys.path.insert(0, str(archive))
    settings_file = folder / "settings" / "mod_settings.json"

    # A fresh install: no settings file yet, and mods_base would leave the mod off.
    logs = []
    stand_in_sdk(logs, settings_file)
    mod_settings = on_load_thread(lambda: importlib.import_module("mod_settings"))
    check("constants read from inside the archive", mod_settings.CONSTANTS["logPrefix"] == "[ModSettings]"
          and set(mod_settings.CONSTANTS["texts"]) == {"en", "fr", "zh"})
    check("built as Mod Settings, nothing that runs each frame", mod_settings.mod.kwargs["name"] == "Mod Settings"
          and mod_settings.mod.kwargs["hooks"] == [] and mod_settings.mod.kwargs["keybinds"] == [])
    check("its own mod known to the page's source", mod_settings._state["mod"] is mod_settings.mod)
    starter = mod_settings._state["starter"]
    check("fresh install: turned on at its load, the start waits for the game's thread",
          mod_settings.mod.is_enabled and starter is not None and starter.hook is not None
          and any("waiting for the game's thread" in line for line in logs))
    on_load_thread(mod_settings.mod.enable)
    check("enabled twice: one start only", mod_settings._state["starter"] is starter)
    mod_settings.mod.disable()
    check("disabled before the game's thread came: the start is cancelled", starter.hook is None and starter.done
          and mod_settings._state["starter"] is None and logs[-1] == "[ModSettings] disabled")
    forget_the_mod()

    # Installed before: the settings file says whether it is on, mods_base reads it, nothing is turned on here.
    settings_file.parent.mkdir()
    settings_file.write_text('{"enabled": false}', encoding="utf-8")
    logs = []
    stand_in_sdk(logs, settings_file)
    mod_settings = on_load_thread(lambda: importlib.import_module("mod_settings"))
    check("with a settings file: left as mods_base sets it", not mod_settings.mod.is_enabled
          and mod_settings._state["starter"] is None)
    started = []
    mod_settings.start = lambda: started.append(threading.get_native_id())
    mod_settings.mod.enable()
    check("turned on from the SDK's console, on the game's thread: started at once, no hook",
          started == [threading.get_native_id()] and mod_settings._state["starter"] is None
          and any("on the game's thread" in line for line in logs))
    forget_the_mod()
    sys.path.pop(0)

print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
sys.exit(1 if FAILURES else 0)
