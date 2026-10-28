# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Mod Settings: a MODS entry in the pause menu and the main menu, opening a page drawn with the pieces of the game's
Options screen, where every SDK mod's settings are shown and changed (Kevin, 25 October 2026). Its page lives in a
pak built from page/ (build_pak.py); this package lists the mods, applies and saves what the player changes.

Menu closed, it costs nothing: its service waits on its socket, its game-thread queue runs only what the page asks
(docs/mod-settings/OPTI.md, rule 1)."""

import pkgutil
import threading

import mods_base
from unrealsdk import logging

from . import bridge, capture, catalog, game_thread, game_thread_start, protocol, routes, sdk_source, server

__version__ = "1.0.0"
__author__ = "kevin-hDev"

CONSTANTS = protocol.parse_constants(pkgutil.get_data(__package__, protocol.CONSTANTS_NAME))
PREFIX = CONSTANTS["logPrefix"]
# What runs while the mod is on: the starter waiting for the game's thread, then the service; and the mod itself.
_state = {"starter": None, "service": None, "mod": None}
_log_lock = threading.Lock()


def log(message: str) -> None:
    # The game's thread, the service's and the capture's write in the same log.
    with _log_lock:
        logging.info(message)


def start() -> None:
    """Game thread: the queue, the bridge and the service; then the service waits on its own thread."""
    _state["starter"] = None
    try:
        game = game_thread.GameThread(CONSTANTS["http"]["maxQueuedTasks"],
                                      lambda name: log(f"{PREFIX} GAME_TASK_ERROR type={name}"))
    except OSError as error:
        log(f"{PREFIX} START_FAILED game_queue errno={error.errno}")
        return
    link = bridge.Bridge(CONSTANTS, protocol, catalog, sdk_source.SdkSource(mods_base, lambda: _state["mod"]), log,
                         game.thread_id)
    keys = capture.WindowsKeys()

    def make_routes(service_log):
        return routes.Routes(CONSTANTS, protocol, catalog, service_log, link, game,
                             lambda on_end: capture.KeyCapture(CONSTANTS, keys, on_end))

    def shutdown() -> None:
        link.save("stopped")
        game.close()
        log(f"{PREFIX} STOPPED_GAME_SIDE messages={game.messages} task_errors={game.errors}")

    def stopped() -> None:
        # The service's thread, as it ends: the game-side cleanup belongs to the game's thread.
        if not game.post(shutdown):
            log(f"{PREFIX} SHUTDOWN_NOT_QUEUED")

    try:
        service = server.Service(CONSTANTS, make_routes, log, on_stopped=stopped)
    except OSError as error:
        # Another program holds the port, or a Mod Settings turned off a moment ago has not let it go yet.
        log(f"{PREFIX} START_FAILED port_in_use_or_refused errno={error.errno}")
        game.close()
        return
    _state["service"] = service
    log(f"{PREFIX} GAME_QUEUE_READY thread={game.thread_id}")
    service.start()


def _on_enable() -> None:
    # Run by the SDK at a launch from inside build_mod, on the load's own thread, before `mod` exists below; turned
    # on from the SDK's console, on the game's thread itself.
    if _state["starter"] is not None or _state["service"] is not None:
        return
    try:
        target = game_thread_start.main_thread_id()
        if threading.get_native_id() == target:
            log(f"{PREFIX} enabled, version {__version__}, on the game's thread")
            start()
            return
        _state["starter"] = game_thread_start.OnThread(
            target, start, lambda name: log(f"{PREFIX} START_FAILED error={name}"), CONSTANTS["start"]["timeoutS"],
            lambda: log(f"{PREFIX} START_TIMEOUT seconds={CONSTANTS['start']['timeoutS']} (turn the mod off and on "
                        f"in the SDK's console to try again)"))
    except OSError as error:
        log(f"{PREFIX} START_FAILED game_thread errno={error.errno}")
        return
    log(f"{PREFIX} enabled, version {__version__}, waiting for the game's thread {target}")


def _on_disable() -> None:
    starter, service = _state["starter"], _state["service"]
    _state["starter"] = _state["service"] = None
    if starter is not None:
        starter.cancel()
    if service is not None:
        # Asked, never waited for: the game must not wait for the service (OPTI.md). Its STOPPED line follows.
        service.request_stop("disabled")
    log(f"{PREFIX} disabled")


mod = mods_base.build_mod(
    name="Mod Settings",
    keybinds=[],
    hooks=[],
    commands=[],
    options=[],
    on_enable=_on_enable,
    on_disable=_on_disable,
)
_state["mod"] = mod

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
