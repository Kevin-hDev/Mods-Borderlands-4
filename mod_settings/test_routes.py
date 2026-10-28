# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of routes.py, without a socket, on the SDK's own option classes (fixture_sdk.py). A thread of the
test plays the game thread: the routes must hand every change to it. python test_routes.py"""

import copy
import json
import sys
from email.message import Message

import package_path  # noqa: F401  (before the package's modules)
import fixture_world
import protocol

BASE = protocol.load_constants()
HTTP = BASE["http"]
PORT = 40000
FAILURES = []


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


class Capture:
    """Stand-in for KeyCapture: records its calls, ends as the test says."""

    def __init__(self, on_end):
        self.on_end = on_end
        self.calls = []
        self.state = ("idle", None)

    def start(self, ident):
        self.calls.append(("start", ident))
        if self.state[0] == "waiting":
            return False
        self.state = ("waiting", None)
        return True

    def cancel(self):
        self.calls.append(("cancel",))

    def status(self):
        return self.state


WORLDS = []


class World(fixture_world.World):
    def __init__(self, **http):
        constants = copy.deepcopy(BASE)
        constants["http"].update(http)
        self.logs = []
        super().__init__(constants, self.logs.append, Capture)
        self.routes.port = PORT
        WORLDS.append(self)

    def model(self):
        status, payload = self.routes.get(headers(), HTTP["modelPath"])
        return status, json.loads(payload) if status == 200 else None

    def change(self, **fields):
        status, _ = self.routes.post(headers(), HTTP["changePath"], body(**fields))
        self.game.settle()
        return status

    def row(self, model, label, mod_index=0):
        rows = list(model["mods"][mod_index]["entries"])
        while rows:
            row = rows.pop(0)
            if row.get("label") == label:
                return row
            rows.extend(row.get("entries", []))
        return None

    def joined(self):
        return "\n".join(self.logs)


def headers(host=f"127.0.0.1:{PORT}", origin="coui://uiresources", site=None):
    message = Message()
    message["Host"] = host
    if origin:
        message["Origin"] = origin
    if site:
        message["Sec-Fetch-Site"] = site
    return message


def body(**fields):
    return json.dumps({"marker": BASE["marker"], **fields}).encode()


def test_model_read_on_the_game_thread():
    world = World()
    status, model = world.model()
    check("model answered after the game thread read the mods", status == 200 and model["revision"] == 1
          and [mod["name"] for mod in model["mods"]] == ["Sample Mod", "Real", "Wide", "Mod Settings"])
    check("mods read on the game thread", f"thread=game" in world.joined() and "MODEL_SENT revision=1 fresh=yes"
          in world.joined())
    check("foreign origin refused", world.routes.get(headers(origin="http://evil.test"), HTTP["modelPath"])[0] == 403)
    check("rebinding host refused", world.routes.get(headers(host="evil.test"), HTTP["modelPath"])[0] == 403)
    check("unknown path", world.routes.get(headers(), "/other")[0] == 404)
    rebuilds = world.joined().count("MODEL_")
    cross = world.routes.post(headers(origin="null", site="cross-site"), HTTP["changePath"],
                              body(action="value", id="m1_on", revision=model["revision"], value=True))
    world.game.settle()
    check("a web page's frame (Origin null, another site) cannot change a mod", cross[0] == 403
          and world.real.is_enabled is not True)
    check("nor make the game thread read the mods",
          world.routes.get(headers(origin=None, site="cross-site"), HTTP["modelPath"])[0] == 403
          and world.joined().count("MODEL_") == rebuilds)


def test_reads_never_pile_up():
    """A read waiting on a late game thread is joined by the next one, not queued again (review, 26 October 2026)."""
    world = World(modelWaitMs=10)
    posted = []
    world.game.post = lambda task: posted.append(task) or True
    world.model()
    world.model()
    check("one read queued while the game thread is late", len(posted) == 1)
    posted[0]()
    world.model()
    check("a new read once it has run", len(posted) == 2)


def test_change_goes_to_the_game_thread():
    world = World()
    _, model = world.model()
    revision = model["revision"]
    switch = world.row(model, "Switch")["id"]
    check("change accepted", world.change(action="value", id=switch, revision=revision, value=True) == 200)
    check("set by the game thread, the mod's callback there", world.option("sample_switch").value is True
          and "TEST_MOD_CALLBACK option=sample_switch value=True thread=game" in world.joined())
    arrows = world.row(model, "Arrows")["id"]
    world.change(action="value", id=arrows, revision=revision, value=3)
    check("index turned into the choice", world.option("sample_arrows").value == "Ultra")
    check("bad value refused", world.change(action="value", id=arrows, revision=revision, value=9) == 400)
    check("old model refused", world.change(action="value", id=switch, revision=revision + 5, value=False) == 409
          and world.option("sample_switch").value is True)
    button = world.row(model, "Button")["id"]
    check("press handed over", world.change(action="press", id=button, revision=revision) == 200
          and "TEST_MOD_BUTTON option=sample_button thread=game" in world.joined())


def test_every_mod_but_mod_settings():
    world = World()
    _, model = world.model()
    restore = world.row(model, "restore", 1)["id"]
    check("another mod's button pressed", world.change(action="press", id=restore, revision=model["revision"]) == 200)
    world.game.settle()
    check("on the game thread", world.real_pressed == [True])
    check("another mod enabled", world.change(action="value", id="m1_on", revision=model["revision"], value=True)
          == 200)
    world.game.settle()
    check("its own enable ran", world.real.is_enabled is True)
    check("Mod Settings cannot turn itself off", world.change(action="value", id="m3_on",
                                                             revision=model["revision"], value=False) == 403)


def test_page_closed_saves_once():
    world = World()
    _, model = world.model()
    world.change(action="value", id=world.row(model, "Whole number")["id"], revision=model["revision"], value=20)
    world.change(action="value", id=world.row(model, "Fraction")["id"], revision=model["revision"], value=3.5)
    saves = world.test_mod.saves
    world.routes.post(headers(), HTTP["eventPath"], body(event="page_closed", reason="escape"))
    world.game.settle()
    check("saved once, by the game thread", world.test_mod.saves == saves + 1
          and "SAVED reason=page_closed mods=1 failed=0" in world.joined())


def test_capture():
    world = World()
    _, model = world.model()
    revision = model["revision"]
    key = world.row(model, "Key")["id"]
    check("capture of an older model refused", json.loads(world.routes.post(
        headers(), HTTP["capturePath"], body(action="start", id=key, revision=revision + 1))[1])["state"]
        == "old_model")
    status, reply = world.routes.post(headers(), HTTP["capturePath"], body(action="start", id=key, revision=revision))
    check("capture started", status == 200 and json.loads(reply)["state"] == "started")
    switch = world.row(model, "Switch")["id"]
    check("capture of a switch refused", json.loads(world.routes.post(
        headers(), HTTP["capturePath"], body(action="start", id=switch, revision=revision))[1])["state"] == "locked")
    world.routes.capture.on_end(key, "done", "F8")
    world.game.settle()
    check("captured key set by the game thread", world.option("sample_key").value == "F8"
          and "TEST_MOD_CALLBACK option=sample_key value='F8' thread=game" in world.joined())
    world.routes.capture.on_end(key, "timeout", None)
    world.game.settle()
    check("no key on timeout", world.option("sample_key").value == "F8")
    world.routes.capture.state = ("idle", None)
    world.routes.post(headers(), HTTP["capturePath"], body(action="start", id=key, revision=world.model()[1]["revision"]))
    world.change(action="value", id=switch, revision=world.bridge.published().revision, value=False)
    world.model()
    world.routes.capture.on_end(key, "done", "F9")
    world.game.settle()
    check("a key captured while a newer model came, its row the same option: set", world.option("sample_key").value
          == "F9")
    world.routes.capture.state = ("idle", None)
    world.routes.post(headers(), HTTP["capturePath"], body(action="start", id=key, revision=world.model()[1]["revision"]))
    world.test_mod.options.insert(0, world.sdk.BoolOption("added_first", False))
    world.model()
    world.routes.capture.on_end(key, "done", "F10")
    world.game.settle()
    check("a key captured while the ids moved goes nowhere", world.option("sample_key").value == "F9"
          and f"CHANGE_REFUSED id={key} reason=old_model" in world.joined())


def test_full_queue():
    world = World()
    _, model = world.model()
    world.game.post = lambda task: False
    status = world.routes.post(headers(), HTTP["changePath"],
                               body(action="value", id=world.row(model, "Switch")["id"], revision=model["revision"],
                                    value=True))[0]
    check("busy game queue said, not waited for", status == 503 and "GAME_QUEUE_REFUSED" in world.joined())
    status, _payload = world.routes.get(headers(), HTTP["modelPath"])
    check("model still answered from the last snapshot", status == 200 and "fresh=no" in world.logs[-1])


def main():
    test_model_read_on_the_game_thread()
    test_reads_never_pile_up()
    test_change_goes_to_the_game_thread()
    test_every_mod_but_mod_settings()
    test_page_closed_saves_once()
    test_capture()
    test_full_queue()
    check("no task raised on the game thread", all(world.game.errors == [] for world in WORLDS))
    print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


main()
