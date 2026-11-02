# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What the service answers, request by request, without the socket: the tests drive it directly. Runs on the
service's thread and touches no game object. Every request is checked first as coming from the game's UI on this
machine; the two actions take an empty body only, so the page can choose neither what is copied nor what is opened
(conception, section 6). Our log lines carry sizes, durations, codes and the file names of mods' paks, never a
path, the player's name or the log's text: the SDK log is what the player copies and posts."""

import re
import time

from . import copy_texts

OK = b'{"ok":true}'
# A pak's file name in our log line: what Windows allows in a name, minus what would read as another field.
LOG_NAME = re.compile(r"[^A-Za-z0-9._~+-]")


class Routes:
    def __init__(self, constants: dict, protocol, parts: dict, log, clock=time.perf_counter,
                 now_text=lambda: time.strftime("%H:%M:%S")):
        """parts: 'log_file', 'masking', 'conflicts', 'windows' (modules), 'api' (Windows), 'log_path', 'folder',
        'mask_patterns', 'version', and what conflicts.gather reads."""
        self.constants = constants
        self.protocol = protocol
        self.parts = parts
        self.log = log
        self.clock = clock
        self.now_text = now_text
        self.budget = protocol.LogBudget(constants)
        self.prefix = constants["logPrefix"]
        self.requests = 0
        # The last log sent to the page, masked, and the last conflicts: COPY copies what the player sees
        # (conception, section 5).
        self.shown = None
        self.shown_conflicts = None
        # Set by the service once its socket is bound: the Host header must name that port.
        self.port = None

    def note(self, kind: str, message: str) -> None:
        verdict = self.budget.admit(kind)
        if verdict == "skip":
            return
        self.log(f"{self.prefix} {message}")
        if verdict == "last":
            self.log(f"{self.prefix} LOG_BUDGET_REACHED kind={kind} (later ones are not written)")

    def admitted(self, headers, path: str, allowed: tuple):
        """(route key, revision) when the request may go on, else the refusal to send as (status, body)."""
        self.requests += 1
        if not self.protocol.trusted_request(headers, self.port, self.constants):
            self.note("rejected", "REFUSED reason=untrusted")
            return None, (403, b'{"error":"refused"}')
        route = self.protocol.route_of(path, self.constants)
        if route is None or route[0] not in allowed:
            return None, (404, b'{"error":"unknown"}')
        return route, None

    def answer(self, body: dict, limit: int = None) -> tuple:
        return 200, self.protocol.payload(body, self.constants, limit)

    def get(self, headers, path: str) -> tuple:
        route, refusal = self.admitted(headers, path, ("hello", "log", "conflicts"))
        if refusal:
            return refusal
        key, revision = route
        if key == "hello":
            return self.answer({"state": "ready", "mod": self.parts["version"]})
        return self.send_log(revision) if key == "log" else self.send_conflicts()

    def post(self, headers, path: str, raw) -> tuple:
        route, refusal = self.admitted(headers, path, ("copy", "copyConflicts", "openFolder", "event"))
        if refusal:
            return refusal
        key = route[0]
        # None: a body too long or of unreadable size, never taken for an empty one (server.py).
        if raw is None:
            return 413, b'{"error":"size"}'
        if key == "event":
            return self.event(raw)
        if raw:
            self.note("rejected", f"REFUSED reason=body_on_{key}")
            return 400, b'{"error":"invalid"}'
        if key == "openFolder":
            return self.open_folder()
        return self.copy() if key == "copy" else self.copy_conflicts()

    def read_log(self, revision):
        """The log read and masked, or {'unchanged'}; raises the log module's LogError."""
        parts = self.parts
        read = parts["log_file"].read(parts["log_path"], revision, self.constants)
        if read.get("unchanged"):
            return read
        replacement, patterns, masking = (self.constants["masking"]["replacement"], parts["mask_patterns"],
                                          parts["masking"])
        # Each part with the text on the other side of its cut, then cut again: never shown, never sent.
        head, join, head_count, _ = masking.mask_joined(read["head"], read.pop("afterHead"), patterns, replacement)
        read["head"] = head[:join]
        tail, join, _, tail_count = masking.mask_joined(read.pop("beforeTail"), read["tail"], patterns, replacement)
        read["tail"] = tail[join:]
        read["masked"] = head_count + tail_count
        read["readAt"] = self.now_text()
        return read

    def send_log(self, revision) -> tuple:
        start = self.clock()
        try:
            read = self.read_log(revision)
        except self.parts["log_file"].LogError as error:
            self.note(f"log_failed_{error.code}", f"LOG_FAILED reason={error.code}")
            return self.answer({"state": "error", "code": error.code})
        if read.get("unchanged"):
            self.note("log_unchanged", "LOG_UNCHANGED")
            return self.answer({"state": "unchanged", "revision": read["revision"]})
        self.shown = read
        body = {"state": "ok", **{key: read[key] for key in ("revision", "size", "cut", "masked", "readAt", "head",
                                                             "tail")}}
        encoded = self.answer(body, self.constants["http"]["maxLogResponseBytes"])
        self.note("log_sent", f"LOG_SENT bytes={read['size']} cut={read['cut']} masked={read['masked']} "
                              f"ms={round((self.clock() - start) * 1000)}")
        return encoded

    def send_conflicts(self) -> tuple:
        start = self.clock()
        found, trace = self.parts["conflicts"].gather(self.parts, self.constants, self.clock)
        encoded = self.answer({"state": "ok", **found}, self.constants["http"]["maxConflictsResponseBytes"])
        # Kept for COPY once it could be sent: COPY copies what the page shows.
        self.shown_conflicts = {**found, "readAt": self.now_text()}
        for name, reason in trace["failures"]:
            self.note("pak_unreadable", f"PAK_UNREADABLE name={LOG_NAME.sub('_', name)[:80]} "
                                        f"reason={LOG_NAME.sub('_', reason)[:48]}")
        checked, unreadable = found["checked"], found["unreadable"]
        # One count per section, named after it; what was looked at under other names, so no field comes twice.
        counts = " ".join(f"{name}={len(found['sections'][name])}" for name in self.constants["conflicts"]["sections"])
        self.note("conflicts_sent", f"CONFLICTS_SENT {counts} enabled_mods={checked['mods']} "
                                    f"bound_keys={checked['keys']} mod_commands={checked['commands']} "
                                    f"paks_read={checked['containers']} "
                                    f"unreadable_mods={unreadable['mods']} unreadable_paks={unreadable['containers']} "
                                    f"log={found['log']} paks_folder={found['paks']} partial={int(found['partial'])} "
                                    f"cut={int(found['cut'])} "
                                    f"mods_ms={trace['modsMs']} log_ms={trace['logMs']} paks_ms={trace['paksMs']} "
                                    f"ms={round((self.clock() - start) * 1000)}")
        return encoded

    def copy(self) -> tuple:
        shown = self.shown
        text = None if shown is None else copy_texts.log_text(shown, self.constants, self.parts["version"],
                                                               getattr(self.parts["log_path"], "name", "log"))
        return self.clip(text, "nothing_to_copy")

    def copy_conflicts(self) -> tuple:
        shown = self.shown_conflicts
        text = None if shown is None else copy_texts.conflicts_text(shown, self.constants, self.parts["version"])
        return self.clip(text, "conflicts_not_read")

    def clip(self, text, missing: str) -> tuple:
        """missing: the code the page tells when its view was never read, so there is nothing to copy."""
        if text is None:
            return self.answer({"state": "error", "code": missing})
        parts = self.parts
        ok, tries, step = parts["windows"].set_clipboard(parts["api"], text, self.constants["clipboard"]["retriesMs"])
        if not ok:
            self.note(f"copy_failed_{step}",
                      f"COPY_FAILED reason={step} tries={tries} error={parts['api'].last_error()}")
            return self.answer({"state": "error", "code": "clipboard_busy" if step == "open" else "clipboard_failed"})
        self.note("copied", f"COPIED bytes={len(text.encode('utf-8'))} tries={tries}")
        return self.answer({"state": "ok", "bytes": len(text.encode("utf-8"))})

    def open_folder(self) -> tuple:
        result = self.parts["windows"].open_folder(self.parts["folder"])
        if result != "opened":
            # "missing" or "failed": the Windows error number is no part of the kind, which stays a few.
            self.note(f"folder_failed_{result.partition('_')[0]}", f"FOLDER_FAILED reason={result}")
            return self.answer({"state": "error", "code": "folder_failed"})
        self.note("folder_opened", "FOLDER_OPENED")
        return self.answer({"state": "ok"})

    def event(self, raw: bytes) -> tuple:
        event = self.protocol.parse_event(raw, self.constants)
        if event is None:
            self.note("rejected", "EVENT_REJECTED")
            return 400, b'{"error":"invalid"}'
        self.note(event["event"], self.protocol.log_line(event, self.constants)[len(self.prefix) + 1:])
        return 200, OK
