# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of bridge.py on the SDK's own option classes and settings save (fixture_sdk.py). The test's thread
plays the game thread. python test_bridge.py"""

import copy
import json
import sys
import threading

import package_path  # noqa: F401  (before the package's modules)
import fixture_sdk
import bridge
import catalog
import protocol
import sdk_source
import fixture_test_mod

BASE = protocol.load_constants()
FAILURES = []


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


class World:
    def __init__(self, constants=BASE, sdk=None):
        self.constants = constants
        self.sdk = sdk or fixture_sdk.sdk()
        self.logs = []
        self.test_mod = fixture_test_mod.build(self.sdk, constants, self.sdk.folder, self.logs.append,
                                             threading.get_native_id())
        self.sdk.register_mod(self.test_mod)
        self.other = self.sdk.Mod(name="Other", options=[self.sdk.BoolOption("other_switch", False)])
        self.sdk.register_mod(self.other)
        self.own = self.sdk.Mod(name="Mod Settings", options=[self.sdk.BoolOption("own_switch", False)])
        self.sdk.register_mod(self.own)
        self.bridge = bridge.Bridge(constants, protocol, catalog,
                                               sdk_source.SdkSource(self.sdk, lambda: self.own),
                                               self.logs.append, threading.get_native_id())

    def entries(self):
        return self.bridge.published().entries

    def entry(self, label, mod_index=0):
        for entry in self.entries().values():
            if entry.model is not None and entry.model.get("label") == label and entry.mod is self.mods()[mod_index]:
                return entry
        return None

    def mods(self):
        return self.sdk.get_ordered_mod_list()

    def row_id(self, label, mod_index=0):
        return next(key for key, entry in self.entries().items() if entry is self.entry(label, mod_index))

    def revision(self):
        return self.bridge.published().revision

    def option(self, identifier):
        return next(option for option in self.test_mod.walk(self.test_mod.options) if option.identifier == identifier)

    def joined(self):
        return "\n".join(self.logs)


def test_rebuild_publishes():
    world = World()
    check("first build published", world.bridge.rebuild() is True and world.bridge.published().revision == 1)
    body = json.loads(world.bridge.published().encoded)
    check("encoded with marker and revision", body["marker"] == BASE["marker"] and body["revision"] == 1
          and len(body["mods"]) == 3)
    encoded = world.bridge.published().encoded
    check("same mods: nothing encoded again", world.bridge.rebuild() is False
          and world.bridge.published().encoded is encoded)
    check("build logged with its measures", "MODEL_BUILT revision=1 mods=3" in world.joined() and "thread=game" in world.joined())
    check("a read that changes nothing is measured too", "MODEL_SAME revision=1 ms=" in world.joined())


def test_apply_runs_the_mods_callback():
    world = World()
    world.bridge.rebuild()
    whole = world.row_id("Whole number")
    world.bridge.apply(whole, 65, 0.0, world.revision())
    check("option set", world.option("sample_whole").value == 65)
    check("the mod's own callback ran, on this thread", "TEST_MOD_CALLBACK option=sample_whole value=65 thread=game"
          in world.joined())
    check("applied logged with its wait", f"APPLIED id={whole} wait_ms=" in world.joined())
    check("rebuild after a change encodes again", world.bridge.rebuild() is True and world.bridge.published().revision == 2)
    body = json.loads(world.bridge.published().encoded)
    check("new value in the model", any(row.get("value") == 65 for row in body["mods"][0]["entries"]))


def test_locked_and_unknown_refused():
    world = World()
    world.bridge.rebuild()
    revision = world.revision()
    other_id = world.row_id("other_switch", 1)
    world.bridge.apply(other_id, True, 0.0, revision)
    check("any other mod's option is set", world.other.options[0].value is True)
    own_id = world.row_id("own_switch", 2)
    world.bridge.apply(own_id, True, 0.0, revision)
    check("Mod Settings' own option is never set", world.own.options[0].value is False)
    check("refusal logged", f"CHANGE_REFUSED id={own_id} reason=locked" in world.joined())
    world.bridge.apply("m9_9", True, 0.0, revision)
    check("unknown id refused", "CHANGE_REFUSED id=m9_9 reason=unknown" in world.joined())
    world.bridge.press(world.row_id("Whole number"), 0.0, revision)
    check("press on a non-button refused", "PRESS_REFUSED" in world.joined())


def test_newer_model_and_older_ids():
    """The service checked the change against revision N; a newer model published before the game thread runs it
    may give that id to another row (review, 26 October 2026). A change of the model just before still applies when
    its id names the same option in both: the service had answered it 200 (second review)."""
    world = World()
    world.bridge.rebuild()
    held = world.revision()
    whole = world.row_id("Whole number")
    world.bridge.apply(whole, 40, 0.0, held)
    world.bridge.rebuild()
    check("a newer model is published", world.revision() == held + 1)
    world.bridge.apply(whole, 45, 0.0, held)
    check("a change of the model just before applies when its id is the same option", world.option(
        "sample_whole").value == 45 and "reason=old_model" not in world.joined())
    world.test_mod.options.insert(0, world.sdk.BoolOption("added_first", False))
    world.bridge.rebuild()
    check("an option added at the top moves the ids", world.revision() == held + 2 and world.row_id("Whole number")
          != whole)
    world.bridge.apply(whole, 70, 0.0, held + 1)
    check("then a change of the model just before is refused on the game thread", world.option(
        "sample_whole").value == 45 and f"CHANGE_REFUSED id={whole} reason=old_model" in world.joined())
    world.bridge.apply(world.row_id("Whole number"), 75, 0.0, held)
    check("as is any change of an older model", world.option("sample_whole").value == 45)
    world.bridge.press(world.row_id("Button"), 0.0, held)
    check("so is a press", "TEST_MOD_BUTTON" not in world.joined())


def test_enable_press_save_and_reload():
    world = World()
    world.bridge.rebuild()
    revision = world.revision()
    world.bridge.apply("m0_on", True, 0.0, revision)
    check("test mod enabled", world.test_mod.is_enabled and "TEST_MOD_ENABLED thread=game" in world.joined())
    world.bridge.press(world.row_id("Button"), 0.0, revision)
    check("button callback ran", "TEST_MOD_BUTTON option=sample_button thread=game" in world.joined())
    saves = world.test_mod.saves
    world.bridge.apply(world.row_id("Fraction"), 2.5, 0.0, revision)
    world.bridge.apply(world.row_id("Fraction"), 2.0, 0.0, revision)
    check("a slider's steps are not saved one by one", world.test_mod.saves == saves)
    world.bridge.apply(world.row_id("Arrows"), "Ultra", 0.0, revision)
    check("any other change saved at once, the slider's mod with it, as the SDK's console does",
          world.test_mod.saves == saves + 1 and "SAVED reason=change mods=1" in world.joined())
    world.bridge.apply(world.row_id("Key"), "K", 0.0, revision)
    check("a key saved at once", world.test_mod.saves == saves + 2)
    world.bridge.apply(world.row_id("Fraction"), 2.5, 0.0, revision)
    world.bridge.save("page_closed")
    check("a slider's mod saved when the page closes", world.test_mod.saves == saves + 3
          and "SAVED reason=page_closed mods=1" in world.joined())
    world.bridge.save("page_closed")
    check("nothing left to save", world.test_mod.saves == saves + 3)
    again = World(sdk=fixture_sdk.sdk(world.sdk.folder))
    check("values back after a restart, by the SDK's own load", again.option("sample_arrows").value == "Ultra"
          and again.option("sample_fraction").value == 2.5 and again.option("sample_key").value == "K"
          and again.test_mod.is_enabled)


def test_too_big():
    constants = copy.deepcopy(BASE)
    constants["http"]["maxModelBytes"] = 200
    world = World(constants)
    check("too big model not published", world.bridge.rebuild() is False and world.bridge.published().encoded is None)
    check("too big logged", "MODEL_TOO_BIG" in world.joined())


def main():
    test_rebuild_publishes()
    test_apply_runs_the_mods_callback()
    test_locked_and_unknown_refused()
    test_newer_model_and_older_ids()
    test_enable_press_save_and_reload()
    test_too_big()
    print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


main()
