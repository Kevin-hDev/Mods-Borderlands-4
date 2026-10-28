# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The SDK as the mod's Python tests see it. The option classes, the plain-text conversion and the settings save
are the SDK's own: read from the installed mods_base.sdkmod (never written), with unrealsdk reduced to its log.
A stand-in keeps a failing fake from hiding a fault: a wrong argument order to an option is caught here.
Only Mod and the mod list are played by the test (FakeMod): the real ones need the running game. FakeMod
follows Mod.iter_display_options, enable, disable and save_settings as mods_base 1.12 writes them.

sdk(settings_dir) -> a module standing for mods_base, with a fresh mod list."""

import os
import re
import sys
import tempfile
import types
import zipfile
from pathlib import Path

import game_tools
import package_path  # noqa: F401  (before the package's modules)
import protocol

MODULES = ("html_to_plain_text", "options", "settings")
# Read only. BL4_SDK_MODS names an installed sdk_mods folder, the convention of this repository's other tests.
SDK_MODS_VARIABLE = "BL4_SDK_MODS"
# The game runs Python 3.14, whose except clause may list types without parentheses (PEP 758); the tests may run
# on an older Python, so only that form is rewritten, with parentheses, before compiling.
BARE_EXCEPT = re.compile(r"except ([A-Za-z_][\w.]*(?:, [A-Za-z_][\w.]*)+):")
LOADED = {}


def mods_base_archive():
    """The installed mods_base.sdkmod: in BL4_SDK_MODS, else in the workshop's default game (the copy the mod is
    written for); None when neither is known, as in the public copy."""
    folder = os.environ.get(SDK_MODS_VARIABLE)
    if folder:
        return Path(folder).expanduser() / "mods_base.sdkmod"
    games = game_tools.known_games()
    if games is None:
        return None
    folders, default = games
    return Path(folders[default]) / "sdk_mods" / "mods_base.sdkmod"


def unrealsdk_stub():
    module = types.ModuleType("unrealsdk")
    module.logging = types.SimpleNamespace(info=lambda *_: None, error=lambda *_: None, warning=lambda *_: None,
                                           misc=lambda *_: None)
    return module


def real_modules(settings_dir: Path) -> dict:
    """The SDK's own modules, loaded once per test run from the installed copy."""
    if LOADED:
        return LOADED
    archive = mods_base_archive()
    if archive is None:
        print(f"SKIP  | set {SDK_MODS_VARIABLE} to an installed sdk_mods folder: the tests read the SDK's own classes")
        print("RESULTAT: SKIP")
        raise SystemExit(0)
    if not archive.is_file():
        raise RuntimeError(f"mods_base.sdkmod is missing from {archive.parent}")
    sys.modules["unrealsdk"] = unrealsdk_stub()
    package = types.ModuleType("mods_base")
    package.__path__ = []
    package.MODS_DIR = settings_dir
    sys.modules["mods_base"] = package
    with zipfile.ZipFile(archive) as files:
        for name in MODULES:
            module = types.ModuleType(f"mods_base.{name}")
            module.__package__ = "mods_base"
            sys.modules[module.__name__] = module
            source = files.read(f"mods_base/{name}.py").decode("utf-8")
            if sys.version_info < (3, 14):
                source = BARE_EXCEPT.sub(r"except (\1):", source)
            exec(compile(source, f"mods_base/{name}.py", "exec"), module.__dict__)
            setattr(package, name, module)
            LOADED[name] = module
    return LOADED


class FakeMod:
    def __init__(self, name, author="Unknown Author", version="Unknown Version", description="", settings_file=None,
                 keybinds=None, options=None, hooks=None, commands=None, on_enable=None, on_disable=None,
                 enabling_locked=False, settings=None):
        self.name = name
        self.author = author
        self.version = version
        self.description = description
        self.settings_file = settings_file
        self.keybinds = keybinds or []
        self.options = options or []
        self.on_enable = on_enable
        self.on_disable = on_disable
        self.enabling_locked = enabling_locked
        self.is_enabled = False
        self.auto_enable = True
        self.saves = 0
        self.listing_fails = False
        self.settings = settings
        for option in self.walk(self.options):
            option.mod = self

    def walk(self, options):
        for option in options:
            yield option
            yield from self.walk(getattr(option, "children", ()))

    def iter_display_options(self):
        if self.listing_fails:
            raise RuntimeError("listing")
        options = self.settings.options if self.settings else None
        if any(not option.is_hidden for option in self.options):
            yield options.GroupedOption("Options", self.options)

    def enable(self):
        if self.enabling_locked or self.is_enabled:
            return
        self.is_enabled = True
        if self.on_enable:
            self.on_enable()
        self.save_settings()

    def disable(self, dont_update_setting=False):
        if self.enabling_locked or not self.is_enabled:
            return
        self.is_enabled = False
        if self.on_disable:
            self.on_disable()
        if not dont_update_setting:
            self.save_settings()

    def save_settings(self):
        self.saves += 1
        LOADED["settings"].default_save_mod_settings(self)

    def load_settings(self):
        LOADED["settings"].default_load_mod_settings(self)


def sdk(settings_dir: Path = None):
    folder = settings_dir or Path(tempfile.mkdtemp(prefix="ms_sdk_"))
    modules = real_modules(folder)
    options = modules["options"]
    module = types.SimpleNamespace()
    for name in ("BaseOption", "ValueOption", "HiddenOption", "SliderOption", "SpinnerOption", "BoolOption",
                 "DropdownOption", "ButtonOption", "KeybindOption", "GroupedOption", "NestedOption"):
        setattr(module, name, getattr(options, name))
    module.html_to_plain_text = modules["html_to_plain_text"].html_to_plain_text
    module.mod_list = []
    holder = types.SimpleNamespace(options=options)

    def make_mod(**kwargs):
        return FakeMod(settings=holder, **kwargs)

    def register_mod(mod):
        if mod not in module.mod_list:
            module.mod_list.append(mod)
            mod.load_settings()

    def deregister_mod(mod):
        if mod.is_enabled:
            mod.disable(dont_update_setting=True)
        module.mod_list.remove(mod)

    module.Mod = make_mod
    module.register_mod = register_mod
    module.deregister_mod = deregister_mod
    module.get_ordered_mod_list = lambda: list(module.mod_list)
    module.folder = folder
    return module
