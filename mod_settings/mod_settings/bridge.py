# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What Mod Settings does on the game thread, and what it publishes for the service's thread.

rebuild(), apply(), press() and save() run on the game thread only (tasks of game_thread.GameThread): they
read the mods, set option values (which run the mods' own callbacks) and save. The service's thread only reads the
published snapshot: the encoded model and each row's bounds, replaced whole under a lock (OPTI.md, rules 18, 20).
Every mod is writable but Mod Settings itself (sdk_source.py).

A change names the revision of the model the page holds; its id means a row of that revision only (a mod may add
rows when one of its options changes). Once a newer model is published, a change of the one just before still
applies when its id names the same option in both, else the game thread refuses it: a read of the mods slower than
modelWaitMs lets the page change a row of the older model, already answered 200 by the service."""

import threading
import time

# A slider sends a value per step while dragged: its mod is saved when the page closes. Any other change is one
# value, saved at once, as the SDK's console does (OPTI.md, rule 21).
SAVED_LATER = ("slider",)


def same_row(older, newer) -> bool:
    """The same option of the same mod, with the same bounds: a value checked against the older row fits the newer."""
    return (older.option is newer.option and older.mod is newer.mod and older.kind == newer.kind
            and older.role == newer.role and older.meta == newer.meta)


class Snapshot:
    __slots__ = ("encoded", "revision", "entries")

    def __init__(self, encoded, revision, entries):
        self.encoded = encoded
        self.revision = revision
        self.entries = entries


class Bridge:
    def __init__(self, constants: dict, protocol, catalog, source, log, game_thread_id, clock=time.perf_counter):
        self.constants = constants
        self.protocol = protocol
        self.catalog = catalog
        self.source = source
        self.log = log
        self.game_thread_id = game_thread_id
        self.clock = clock
        self.prefix = constants["logPrefix"]
        self.lock = threading.Lock()
        self.snapshot = Snapshot(None, 0, {})
        self.previous = Snapshot(None, -1, {})
        self.model = None
        self.dirty = []
        self.budget = protocol.LogBudget(constants)

    def thread_name(self) -> str:
        return "game" if threading.get_native_id() == self.game_thread_id else "other"

    # Service's thread: the last published state.
    def published(self) -> Snapshot:
        with self.lock:
            return self.snapshot

    def rebuild(self) -> bool:
        """Game thread. Reads every mod again; encodes and publishes only when something differs."""
        start = self.clock()
        model, table, counts = self.catalog.build(self.constants, self.source)
        if model == self.model:
            # Measured too: every opening of MODS pays this read of the mods (OPTI.md, rule 3).
            if self.budget.admit("rebuild") != "skip":
                self.log(f"{self.prefix} MODEL_SAME revision={self.snapshot.revision} "
                         f"ms={(self.clock() - start) * 1000:.2f} thread={self.thread_name()}")
            return False
        revision = self.snapshot.revision + 1
        try:
            encoded = self.protocol.payload({"revision": revision, **model}, self.constants,
                                            self.constants["http"]["maxModelBytes"])
        except ValueError:
            # The page keeps the last model it could be sent; the log says why it is not newer.
            self.log(f"{self.prefix} MODEL_TOO_BIG mods={counts.mods} entries={counts.entries}")
            return False
        entries = {key: entry for key, entry in table.items()}
        with self.lock:
            self.previous, self.snapshot = self.snapshot, Snapshot(encoded, revision, entries)
        self.model = model
        elapsed = (self.clock() - start) * 1000
        self.log(f"{self.prefix} MODEL_BUILT revision={revision} mods={counts.mods} entries={counts.entries} "
                 f"widest_page={counts.widest_page} unsupported={counts.unsupported} truncated={counts.truncated} "
                 f"failed_mods={counts.failed_mods} bytes={len(encoded)} ms={elapsed:.2f} "
                 f"thread={self.thread_name()}")
        return True

    def row(self, entry_id: str, revision: int):
        """The published row a change of that revision means, or None with the reason logged."""
        entry = self.snapshot.entries.get(entry_id)
        if revision != self.snapshot.revision:
            older = self.previous.entries.get(entry_id) if revision == self.previous.revision else None
            if older is None or entry is None or not same_row(older, entry):
                self.log(f"{self.prefix} CHANGE_REFUSED id={entry_id} reason=old_model")
                return None
        if entry is None or not entry.writable:
            self.log(f"{self.prefix} CHANGE_REFUSED id={entry_id} reason={'unknown' if entry is None else 'locked'}")
            return None
        return entry

    def apply(self, entry_id: str, value, sent_at: float, revision: int) -> None:
        """Game thread. value comes clean from the service (catalog.clean_change against the same row)."""
        entry = self.row(entry_id, revision)
        if entry is None:
            return
        start = self.clock()
        if entry.role == "enabled":
            # The SDK saves the enabled state itself.
            if value:
                entry.mod.enable()
            else:
                entry.mod.disable()
        else:
            entry.option.value = value
            if entry.mod not in self.dirty:
                self.dirty.append(entry.mod)
        # The next rebuild encodes again: the kept model no longer says what the options hold.
        self.model = None
        self.timed("APPLIED", entry_id, start, sent_at)
        if entry.kind not in SAVED_LATER:
            self.save("change")

    def press(self, entry_id: str, sent_at: float, revision: int) -> None:
        entry = self.row(entry_id, revision)
        if entry is None:
            return
        if entry.kind != "button":
            self.log(f"{self.prefix} PRESS_REFUSED id={entry_id}")
            return
        start = self.clock()
        if entry.option.on_press is not None:
            entry.option.on_press(entry.option)
        self.timed("PRESSED", entry_id, start, sent_at)

    def timed(self, what: str, entry_id: str, start: float, sent_at: float) -> None:
        verdict = self.budget.admit("change")
        if verdict == "skip":
            return
        now = self.clock()
        self.log(f"{self.prefix} {what} id={entry_id} wait_ms={(start - sent_at) * 1000:.2f} "
                 f"run_ms={(now - start) * 1000:.3f} thread={self.thread_name()}")
        if verdict == "last":
            self.log(f"{self.prefix} LOG_BUDGET_REACHED event=change (later ones are not written)")

    def save(self, reason: str) -> None:
        """Game thread. Each changed mod once, by the SDK's own save (OPTI.md, rule 21)."""
        if not self.dirty:
            return
        start = self.clock()
        saved, failed = 0, 0
        for mod in self.dirty:
            try:
                mod.save_settings()
                saved += 1
            except OSError:
                failed += 1
        self.dirty = []
        # A failed save is always written; the others share a ceiling, as each click of a switch saves.
        if failed or self.budget.admit("save") != "skip":
            self.log(f"{self.prefix} SAVED reason={reason} mods={saved} failed={failed} "
                     f"ms={(self.clock() - start) * 1000:.2f} thread={self.thread_name()}")
