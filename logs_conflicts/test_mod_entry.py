# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of the package's __init__.py with a fake SDK: a fresh install turns the mod on, the mod starts its service
when enabled, logs no path, stops it when disabled, and says once when its port is taken. python test_mod_entry.py"""

import socket
import sys
import tempfile
import time
import types
from pathlib import Path

FAILURES = []
LINES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


class FakeMod:
    def __init__(self, fields):
        self.fields = fields
        # A fresh install: no settings file yet.
        self.settings_file = Path(__file__).resolve().parent / "no_such_settings_file.json"
        self.enabled_by_install = False

    def enable(self):
        self.enabled_by_install = True


RAW_MODS = ["first", "second"]


def install_fake_sdk():
    unrealsdk = types.ModuleType("unrealsdk")
    unrealsdk.config = {"unrealsdk": {}}
    logging = types.ModuleType("unrealsdk.logging")
    logging.info = LINES.append
    unrealsdk.logging = logging
    mods_base = types.ModuleType("mods_base")
    mods_base.build_mod = lambda **fields: FakeMod(fields)
    # No get_ordered_mod_list: sorting reads each mod's name and compares mods, which runs their code.
    mods_base.mod_list = types.ModuleType("mods_base.mod_list")
    mods_base.mod_list.mod_list = RAW_MODS
    mods_base.Mod = FakeMod
    sys.modules.update({"unrealsdk": unrealsdk, "unrealsdk.logging": logging, "mods_base": mods_base})


install_fake_sdk()
sys.path.insert(0, str(Path(__file__).resolve().parent))
import logs_conflicts as package  # noqa: E402

package.CONSTANTS["http"]["port"] = 0
expect(package.mod.fields["name"] == "Logs & Conflicts" and package.mod.fields["hooks"] == [], "mod built, no hook")
expect(package.mod.enabled_by_install, "a fresh install turns the mod on")
package.windows.dll_folder = lambda _api, _name: Path(r"C:\Users\Jane Doe\Game\Plugins")
package._on_enable()
service = package._state["service"]
expect(service is not None and service.thread.is_alive(), "service started when enabled")
expect(any(line.startswith("[LogsConflicts] PATHS dll_found=1 folder=Plugins parent=Game") for line in LINES),
       "paths logged by their last two names")
expect(any(line.endswith("log_exists=0 paks_exists=0") for line in LINES), "the Paks folder looked for, said absent")
expect(all("Users" not in line and "Jane" not in line for line in LINES), "no home path in the log")
package._on_enable()
expect(package._state["service"] is service, "enabling twice starts nothing more")
with tempfile.TemporaryDirectory() as game:
    (Path(game) / "OakGame" / "Content" / "Paks").mkdir(parents=True)
    plugins = Path(game) / "OakGame" / "Binaries" / "Win64" / "Plugins"
    package.windows.dll_folder = lambda _api, _name: plugins
    found = package.parts()
    expect(Path(found["paks"].folder) == Path(game) / "OakGame" / "Content" / "Paks"
           and LINES[-1].endswith("paks_exists=1"), "the Paks folder found from the SDK's folder")
    expect(found["modClass"] is FakeMod and ("sys", sys) in found["modules"](),
           "mods_base's class and the loaded modules, for the mods dropped from the list")
    listed = found["mods"]()
    expect(listed == RAW_MODS and listed is not RAW_MODS,
           "mods_base's own list, copied as it is, never sorted by the mods' code")
package._on_disable()
service.thread.join(3)
expect(not service.thread.is_alive() and package._state["service"] is None, "service stopped when disabled")
expect(any("STOPPED reason=disabled" in line for line in LINES), "stop logged")
time.sleep(0.05)

taken = socket.socket()
taken.bind(("127.0.0.1", 0))
taken.listen(1)
package.CONSTANTS["http"]["port"] = taken.getsockname()[1]
package._on_enable()
expect(package._state["service"] is None and any("START_FAILED port_in_use_or_refused" in line for line in LINES),
       "port taken: said once, no service left")
taken.close()

print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
