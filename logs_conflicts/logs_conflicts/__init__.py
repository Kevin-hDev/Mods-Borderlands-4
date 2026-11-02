# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Logs & Conflicts: an entry in the pause menu and the main menu opening a page, drawn with the game's pieces, that
shows the SDK log of this session with the player's user name hidden, copies it, opens its folder, and lists the
conflicts between the player's mods (docs/tools/journaux-et-conflits.md). Its page lives in a pak built from page/
(build_pak.py); this package runs the small local service the page talks to.

Menu closed, it costs nothing: the service waits on its socket. It touches no game object, so it needs no hook and
no game thread (conception, section 5)."""

import os
import pkgutil
import sys
import threading

import mods_base
import unrealsdk
from unrealsdk import logging

from . import conflicts, log_file, masking, pak_overlaps, protocol, routes, server, windows

__version__ = "1.0.0"
__author__ = "kevin-hDev"

CONSTANTS = protocol.parse_constants(pkgutil.get_data(__package__, protocol.CONSTANTS_NAME))
PREFIX = CONSTANTS["logPrefix"]
_state = {"service": None}
_log_lock = threading.Lock()


def log(message: str) -> None:
    # The game's thread and the service's write in the same log.
    with _log_lock:
        logging.info(message)


def parts() -> dict:
    """What the service needs, found once at its start: the log's place is never taken from the page."""
    api = windows.WindowsApi()
    folder = windows.dll_folder(api, CONSTANTS["log"]["dllName"])
    path, source = log_file.log_path(folder, getattr(unrealsdk, "config", None), CONSTANTS)
    paks = os.path.normpath(os.path.join(folder, CONSTANTS["conflicts"]["paks"]["fromDll"])) if folder else None
    # Names of the folder and its parent only: the log line must not carry the player's path.
    log(f"{PREFIX} PATHS dll_found={int(folder is not None)} folder={folder.name if folder else '-'} "
        f"parent={folder.parent.name if folder else '-'} log_file={source} "
        f"log_exists={int(path is not None and path.is_file())} "
        f"paks_exists={int(paks is not None and os.path.isdir(paks))}")
    return {"log_file": log_file, "masking": masking, "conflicts": conflicts, "windows": windows, "api": api,
            "log_path": path, "folder": path.parent if path is not None else None,
            "mask_patterns": masking.home_patterns(windows.homes(api, os.path.expanduser("~"))
                                                   + masking.linux_homes(os.environ)),
            # The list as mods_base holds it, copied in one step: get_ordered_mod_list sorts by reading each mod's
            # name and comparing mods, which runs their code on the service's thread (mods_base 1.12, mod_list.py).
            "mods": lambda: list(mods_base.mod_list.mod_list), "modClass": mods_base.Mod,
            # A copy, taken in one step: the game's thread may import a module meanwhile.
            "modules": lambda: list(sys.modules.items()),
            "paks": pak_overlaps.PakScan(paks, CONSTANTS), "version": __version__}


def _on_enable() -> None:
    if _state["service"] is not None:
        return
    try:
        found = parts()
        service = server.Service(CONSTANTS, lambda service_log: routes.Routes(CONSTANTS, protocol, found, service_log),
                                 log)
    except OSError as error:
        # Another program holds the port, or a Logs & Conflicts turned off a moment ago has not let it go yet. The
        # menu entry stays hidden: it is shown only when the service answers.
        log(f"{PREFIX} START_FAILED port_in_use_or_refused errno={error.errno}")
        return
    _state["service"] = service
    log(f"{PREFIX} enabled, version {__version__}")
    service.start()


def _on_disable() -> None:
    service = _state["service"]
    _state["service"] = None
    if service is not None:
        # Asked, never waited for: the game must not wait for the service. Its STOPPED line follows.
        service.request_stop("disabled")
    log(f"{PREFIX} disabled")


mod = mods_base.build_mod(
    name=CONSTANTS["modName"],
    description=CONSTANTS["modDescription"],
    keybinds=[],
    hooks=[],
    commands=[],
    options=[],
    on_enable=_on_enable,
    on_disable=_on_disable,
)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
