# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The mod's Python side as the tests assemble it: the SDK of fixture_sdk.py with the sample mod, two more mods
and Mod Settings itself, the only one locked,
a thread playing the game thread, the bridge and the routes, wired as mod_settings.py wires them.

World(constants, log, make_capture, locked="own") -> .sdk, .game, .test_mod, .real, .wide, .own, .bridge, .routes
(port still unset). locked names the mod the page may not change: Mod Settings itself in the mod, "real" in the
browser test, so that the locked rows are seen on long pages with sub-pages."""

import queue
import threading

import package_path  # noqa: F401  (before the package's modules)
import fixture_sdk
import bridge
import catalog
import protocol
import routes
import sdk_source
import fixture_test_mod

REAL_LONG_PAGE = 8
WIDE_TABS = 12
WIDE_DESCRIPTION = "&lt;b&gt;Wide&lt;/b&gt; &lt;img src=x&gt;"
WIDE_SHOWN = "<b>Wide</b> <img src=x>"


class FakeGame:
    """The game thread's queue: a thread of its own that runs the posted tasks, bounded like the real one."""

    def __init__(self, max_tasks=8):
        self.tasks = queue.Queue(max_tasks)
        # Each task's error, by type: the real queue goes on after one (game_thread.py, drain), and so must this one,
        # or a test stuck in settle() would never say ECHEC.
        self.errors = []
        self.native_id = None
        self.ready = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        self.ready.wait(5)

    def run(self):
        self.native_id = threading.get_native_id()
        self.ready.set()
        while True:
            task = self.tasks.get()
            try:
                task()
            except BaseException as error:
                self.errors.append(type(error).__name__)
            finally:
                self.tasks.task_done()

    def post(self, task):
        try:
            self.tasks.put_nowait(task)
            return True
        except queue.Full:
            return False

    def settle(self):
        self.tasks.join()


class World:
    def __init__(self, constants: dict, log, make_capture, locked="own"):
        self.constants = constants
        self.sdk = fixture_sdk.sdk()
        self.game = FakeGame()
        self.real_pressed = []
        self.test_mod = fixture_test_mod.build(self.sdk, constants, self.sdk.folder, log, self.game.native_id)
        self.sdk.register_mod(self.test_mod)
        # Long pages, as Kevin's mods have (trial 8): longer than the browser test's scrolled area. Its page holds a
        # page (a sub-tab) whose long rows end with a deeper page, opened from a scrolled list.
        self.real = self.sdk.Mod(name="Real", options=[
            self.sdk.ButtonOption("restore", on_press=lambda _option: self.real_pressed.append(True)),
            self.sdk.SliderOption("speed", 2.0, 0.0, 10.0, step=0.5, is_integer=False),
            *self.sliders("extra", REAL_LONG_PAGE),
            self.sdk.NestedOption("real_more", [self.sdk.NestedOption("real_sub", [
                *self.sliders("inner", REAL_LONG_PAGE),
                self.sdk.NestedOption("real_deep", [self.sdk.BoolOption("deep_flag", True)], display_name="Real deep"),
            ], display_name="Real sub")], display_name="Real more"),
        ])
        self.sdk.register_mod(self.real)
        # More tabs than the screen is wide, as Apex Movement has: the bar scrolls sideways to the chosen one. Its
        # description is markup once the SDK decodes it: the page must show it as text.
        self.wide = self.sdk.Mod(name="Wide", description=WIDE_DESCRIPTION, options=[
            self.sdk.NestedOption(f"wide_{n}", [self.sdk.BoolOption(f"wide_flag_{n}", True)],
                                  display_name=f"Wide page number {n}") for n in range(WIDE_TABS)])
        self.sdk.register_mod(self.wide)
        self.own = self.sdk.Mod(name="Mod Settings", options=[])
        self.sdk.register_mod(self.own)
        self.bridge = bridge.Bridge(constants, protocol, catalog,
                                               sdk_source.SdkSource(self.sdk, lambda: getattr(self, locked)), log,
                                               self.game.native_id)
        self.routes = routes.Routes(constants, protocol, catalog, log, self.bridge,
                                               self.game, make_capture)

    def sliders(self, prefix, count):
        return [self.sdk.SliderOption(f"{prefix}_{n}", 1.0, 0.0, 5.0, step=0.5, is_integer=False) for n in range(count)]

    def option(self, identifier):
        return next(option for option in self.test_mod.walk(self.test_mod.options) if option.identifier == identifier)
