# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What the mod's service answers, request by request, without the socket: the tests drive it directly.
Runs on the service's thread: it touches no game object and no mod, only the bridge's published snapshot; what
must act on the game is handed to the game thread (OPTI.md, rule 18). Each request is counted against the
service's budget and checked as coming from the game's UI first."""

import threading
import time


class Routes:
    def __init__(self, constants: dict, protocol, catalog, log, bridge, game, make_capture, clock=time.perf_counter):
        self.constants = constants
        self.protocol = protocol
        self.catalog = catalog
        self.log = log
        self.bridge = bridge
        self.game = game
        self.clock = clock
        self.capture = make_capture(self.capture_ended)
        self.budget = protocol.LogBudget(constants)
        self.requests = 0
        self.prefix = constants["logPrefix"]
        self.keys = constants["capture"]["keys"]
        # The model revision when the running capture started: its key goes to the row of that model.
        self.capture_revision = None
        # Set while a read of the mods waits on the game thread: a second request waits for it instead of queuing one.
        self.rebuild_done = None
        # Set by the service once its socket is bound: the Host header must name that port.
        self.port = None

    def admitted(self, headers, path: str, allowed: tuple):
        """None when the request may go on, else the refusal to send."""
        self.requests += 1
        if not self.protocol.trusted_request(headers, self.port, self.constants):
            return 403, b'{"error":"refused"}'
        if path not in allowed:
            return 404, b'{"error":"unknown"}'
        return None

    def get(self, headers, path: str) -> tuple:
        http = self.constants["http"]
        refusal = self.admitted(headers, path, (http["modelPath"], http["capturePath"]))
        if refusal:
            return refusal
        if path == http["capturePath"]:
            state, key = self.capture.status()
            body = {"state": state} if key is None else {"state": state, "key": key}
            return 200, self.protocol.payload(body, self.constants)
        return self.model()

    def model(self) -> tuple:
        # The mods are read on the game thread; this thread waits for it, briefly. The page never waits: it shows
        # its own copy meanwhile (OPTI.md, rules 2 and 14).
        done = self.rebuild_done
        if done is None or done.is_set():
            done = threading.Event()

            def rebuild():
                try:
                    self.bridge.rebuild()
                finally:
                    done.set()

            self.rebuild_done = done if self.game.post(rebuild) else None
        fresh = self.rebuild_done is not None and done.wait(self.constants["http"]["modelWaitMs"] / 1000)
        snapshot = self.bridge.published()
        self.log(f"{self.prefix} MODEL_SENT revision={snapshot.revision} fresh={'yes' if fresh else 'no'}")
        if snapshot.encoded is None:
            return 503, b'{"error":"no_model"}'
        return 200, snapshot.encoded

    def post(self, headers, path: str, raw) -> tuple:
        http = self.constants["http"]
        refusal = self.admitted(headers, path, (http["eventPath"], http["changePath"], http["capturePath"]))
        if refusal:
            return refusal
        if raw is None:
            return 413, b'{"error":"size"}'
        if path == http["capturePath"]:
            return self.capture_request(raw)
        if path == http["changePath"]:
            return self.change(raw)
        event = self.protocol.parse_event(raw, self.constants)
        if event is None:
            return self.rejected()
        self.write(event)
        if event["event"] == "page_closed":
            self.hand_over(lambda: self.bridge.save("page_closed"))
        return 200, b'{"ok":true}'

    def rejected(self) -> tuple:
        if self.budget.admit("rejected") != "skip":
            self.log(f"{self.prefix} EVENT_REJECTED")
        return 400, b'{"error":"invalid"}'

    def writable_row(self, entry_id: str, kinds: tuple):
        snapshot = self.bridge.published()
        entry = snapshot.entries.get(entry_id)
        return entry if entry is not None and entry.writable and entry.kind in kinds else None

    def change(self, raw) -> tuple:
        change = self.protocol.parse_change(raw, self.constants)
        if change is None:
            return self.rejected()
        snapshot = self.bridge.published()
        # Ids are counted in the model the page holds: another model may give the same id to another row.
        if change["revision"] != snapshot.revision:
            self.log(f"{self.prefix} CHANGE_REFUSED id={change['id']} reason=old_model")
            return 409, b'{"error":"old_model"}'
        entry_id, sent_at, revision = change["id"], self.clock(), change["revision"]
        if change["action"] == "press":
            if self.writable_row(entry_id, ("button",)) is None:
                return self.locked(entry_id)
            return self.hand_over(lambda: self.bridge.press(entry_id, sent_at, revision))
        entry = self.writable_row(entry_id, self.catalog.VALUE_KINDS)
        if entry is None:
            return self.locked(entry_id)
        value = self.catalog.clean_change(entry, change["value"], self.keys)
        if value is self.catalog.REFUSED:
            return self.rejected()
        return self.hand_over(lambda: self.bridge.apply(entry_id, value, sent_at, revision))

    def locked(self, entry_id: str) -> tuple:
        self.log(f"{self.prefix} CHANGE_REFUSED id={entry_id} reason=locked")
        return 403, b'{"error":"locked"}'

    def hand_over(self, task) -> tuple:
        if self.game.post(task):
            return 200, b'{"ok":true}'
        self.log(f"{self.prefix} GAME_QUEUE_REFUSED")
        return 503, b'{"error":"busy"}'

    def capture_request(self, raw) -> tuple:
        request = self.protocol.parse_capture(raw, self.constants)
        if request is None:
            return 400, b'{"error":"invalid"}'
        action, entry_id, revision = request
        if action == "cancel":
            self.capture.cancel()
            state = "cancelling"
        elif revision != self.bridge.published().revision:
            state = "old_model"
        elif self.writable_row(entry_id, ("keybind",)) is None:
            state = "locked"
        else:
            started = self.capture.start(entry_id)
            if started:
                self.capture_revision = revision
            state = "started" if started else "busy"
            self.log(f"{self.prefix} CAPTURE_START id={entry_id} state={state}")
        return 200, self.protocol.payload({"state": state}, self.constants)

    # Runs on the capture's thread: the key goes to the game thread like a change from the page.
    def capture_ended(self, entry_id: str, state: str, key) -> None:
        self.log(f"{self.prefix} CAPTURE_END id={entry_id} state={state} key={key}")
        revision = self.capture_revision
        if key is None:
            return
        entry = self.writable_row(entry_id, ("keybind",))
        if entry is None:
            reason = "old_model" if revision != self.bridge.published().revision else "locked"
            self.log(f"{self.prefix} CHANGE_REFUSED id={entry_id} reason={reason}")
            return
        value = self.catalog.clean_change(entry, key, self.keys)
        if value is self.catalog.REFUSED:
            self.log(f"{self.prefix} CHANGE_REFUSED id={entry_id} reason=key")
            return
        sent_at = self.clock()
        self.hand_over(lambda: self.bridge.apply(entry_id, value, sent_at, revision))

    def write(self, event: dict) -> None:
        verdict = self.budget.admit(event["event"])
        if verdict == "skip":
            return
        self.log(self.protocol.log_line(event, self.constants))
        if verdict == "last":
            self.log(f"{self.prefix} LOG_BUDGET_REACHED event={event['event']} (later ones are not written)")
