# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of routes.py with a real log file in a temporary folder and a fake Windows. python test_routes.py"""

import copy
import json
import sys
import tempfile
import types
from email.message import Message
from pathlib import Path

import package_path  # noqa: F401
from logs_conflicts import conflicts, log_file, masking, protocol, routes
from fixture_windows import FakeApi, FakeWindows

FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


C = protocol.load_constants()
BASE = C["http"]["basePath"]
PORT = C["http"]["port"]


class Key:
    def __init__(self, key):
        self.key, self.identifier, self.is_enabled = key, "Bind", True
        self.display_name, self.is_rebindable = None, True


class Mod:
    def __init__(self, name, keys):
        self.name, self.is_enabled, self.keybinds = name, True, [Key(key) for key in keys]
        self.commands, self.settings_file = [], None


class Paks:
    """pak_overlaps.PakScan's part the routes see."""

    def __init__(self, **found):
        self.found = {"entries": [], "containers": 2, "unreadable": 0, "missing": False, "failures": [],
                      "fresh": True, **found}

    def find(self):
        return dict(self.found)


def headers(origin=None):
    message = Message()
    message["Host"] = f"127.0.0.1:{PORT}"
    if origin:
        message["Origin"] = origin
    return message


def make(folder: Path, windows=None, text="hello\n"):
    log = folder / "unrealsdk.log"
    log.write_bytes(text.encode("utf-8"))
    lines = []
    parts = {"log_file": log_file, "masking": masking, "conflicts": conflicts, "windows": windows or FakeWindows(),
             "api": FakeApi(), "log_path": log, "folder": folder,
             "mask_patterns": masking.home_patterns([r"C:\Users\Kev"]),
             "mods": lambda: [Mod("A", ["F5"]), Mod("B", ["f5", "G"])], "modules": lambda: [], "modClass": Mod,
             "paks": Paks(), "version": "1.0.0"}
    made = routes.Routes(C, protocol, parts, lines.append, clock=lambda: 0.0, now_text=lambda: "14:32:05")
    made.port = PORT
    return made, lines, parts


def body(answer):
    return json.loads(answer[1])


def test_reads(folder: Path):
    r, lines, _ = make(folder, text="saved in C:\\Users\\Kev\\save.sav\n<script>alert(1)</script>\n")
    expect(body(r.get(headers(), BASE + "hello"))["state"] == "ready", "hello answered")
    log = body(r.get(headers("coui://uiresources"), BASE + "log"))
    expect(log["state"] == "ok" and "C:\\Users\\<user>\\save.sav" in log["head"] and "Kev\\" not in log["head"],
           "the user name is hidden before the text leaves")
    expect(log["masked"] == 1 and log["readAt"] == "14:32:05" and log["cut"] == 0, "masked count and read time")
    expect("<script>alert(1)</script>" in log["head"], "page code in the log is sent as text, unchanged")
    unchanged = body(r.get(headers(), BASE + f"log?rev={log['revision']}"))
    expect(unchanged == {"marker": C["marker"], "version": 1, "state": "unchanged", "revision": log["revision"]},
           "same revision: not sent again")
    found = body(r.get(headers(), BASE + "conflicts"))
    expect(found["sections"]["keys"] == [{"name": "F5", "items": [{"mod": "A", "name": "Bind", "fixed": False},
                                                                   {"mod": "B", "name": "Bind", "fixed": False}],
                                          "more": 0}], "conflicts listed by section")
    expect(any(line.startswith("[LogsConflicts] LOG_SENT bytes=") for line in lines)
           and any("CONFLICTS_SENT failed=0 twice=0 files=0 commands=0 settings=0 keys=1 enabled_mods=2 bound_keys=3 "
                   "mod_commands=0 paks_read=2 unreadable_mods=0 unreadable_paks=0 log=read paks_folder=read partial=0 "
                   "cut=0 "
                   in line for line in lines), "reads logged, each count under its own name")
    expect(all("Kev" not in line and "Users" not in line and "save" not in line for line in lines),
           "no name, path or log text in our log lines")


def test_long_log(folder: Path):
    """A log over the bound: its start and its end are sent, the name hidden in both, the cut said in the copy."""
    filler = ("x" * 99 + "\n") * (C["log"]["maxBytes"] // 100 + 500)
    windows = FakeWindows()
    r, _lines, _ = make(folder, windows, text="start C:\\Users\\Kev\\a\n" + filler + "end C:\\Users\\Kev\\b\n")
    log = body(r.get(headers(), BASE + "log"))
    expect(log["cut"] > 0 and log["head"].startswith("start C:\\Users\\<user>\\a")
           and log["tail"].endswith("end C:\\Users\\<user>\\b\n") and log["masked"] == 2, "name hidden at both ends")
    r.post(headers(), BASE + "copy", b"")
    expect(f"\n[... {log['cut']} bytes cut by Logs & Conflicts ...]\n" in windows.copied[0]
           and "Kev\\" not in windows.copied[0], "the copy says where it is cut, and keeps the name hidden")


def test_cut_inside_paths(folder: Path):
    """A log of one long line, cut inside the home's path at both cuts: no part of the name is sent."""
    small = copy.deepcopy(C)
    small["log"].update(maxBytes=200, headBytes=40, maskMarginBytes=64)
    home = "C:\\Users\\Kev"
    text = "a" * 30 + home + "\\at_head " + "b" * 300 + home + "\\at_tail " + "c" * 145
    tail_start = len(text) - (200 - 40)
    expect(30 < 40 < 30 + len(home) and text.index(home, 40) < tail_start < text.index(home, 40) + len(home),
           "the cuts fall inside the two paths")
    r, _lines, parts = make(folder, text=text)
    r.constants = small
    log = body(r.get(headers(), BASE + "log"))
    expect(log["head"] == "a" * 30 + "C:\\Users\\<user>" and log["tail"].startswith("\\at_tail ")
           and "Kev" not in log["head"] + log["tail"] and log["masked"] == 1,
           "both cut paths masked whole, the cuts made again after them")


def test_cut_inside_a_character(folder: Path):
    """The head's cut falls inside the "\u00e9" of the user's name: the name is still masked whole (review)."""
    small = copy.deepcopy(C)
    small["log"].update(maxBytes=200, headBytes=40, maskMarginBytes=64)
    home = "C:\\Users\\K\u00e9vin"
    text = "a" * 29 + home + "\\at_head " + "b" * 400
    expect(text.encode("utf-8").index("\u00e9".encode("utf-8")) == 39, "the cut falls inside the name's \u00e9")
    r, _lines, parts = make(folder, text=text)
    r.constants = small
    parts["mask_patterns"] = masking.home_patterns([home])
    log = body(r.get(headers(), BASE + "log"))
    expect(log["head"] == "a" * 29 + "C:\\Users\\<user>" and "\ufffd" not in log["head"] and log["masked"] == 1,
           "the name masked whole, the cut made again after it")


def test_conflicts_bound(folder: Path):
    """The worst case the bounds allow, names of emoji (12 bytes a character in the answer), still fits the answer's
    bound: the list is cut instead (audit, review)."""
    long_name = "\U0001F600" * C["conflicts"]["maxName"]
    keys = [f"{long_name[:-3]}{index:03d}" for index in range(C["conflicts"]["maxKeysPerMod"])]
    many = [Mod(f"{long_name[:-3]}{index:03d}", keys) for index in range(C["conflicts"]["maxMods"])]
    for mod in many:
        for bind in mod.keybinds:
            bind.identifier = long_name
    r, logged, parts = make(folder)
    parts["mods"] = lambda: many
    status, raw = r.get(headers(), BASE + "conflicts")
    expect(any(line.startswith("[LogsConflicts] CONFLICTS_SENT") and " cut=1 " in line for line in logged),
           "the cut said in our log")
    found = json.loads(raw)
    lines = sum(2 + len(entry["items"]) + 1 for entry in found["sections"]["keys"])
    expect(status == 200 and found["cut"] and len(raw) <= C["http"]["maxConflictsResponseBytes"]
           and 0 < lines <= C["conflicts"]["maxListedLines"],
           f"128 mods on 64 common keys: a cut list within the bound ({len(raw)} bytes)")


def test_conflicts_too_big(folder: Path):
    """An answer over its bound is never sent, and COPY never copies it (review)."""
    r, _lines, parts = make(folder)
    use = {"mod": "x" * C["http"]["maxConflictsResponseBytes"], "name": "A", "fixed": False}
    huge = {"sections": {name: [] for name in C["conflicts"]["sections"]},
            "checked": {"mods": 1, "keys": 1, "commands": 0, "containers": 0},
            "unreadable": {"mods": 0, "containers": 0}, "log": "read", "paks": "read", "partial": False, "cut": False}
    huge["sections"]["keys"] = [{"name": "F5", "items": [use], "more": 0}]
    trace = {"failures": [], "modsMs": 0, "logMs": 0, "paksMs": 0}
    parts["conflicts"] = types.SimpleNamespace(gather=lambda _parts, _constants, _clock: (huge, trace))
    try:
        r.get(headers(), BASE + "conflicts")
        expect(False, "an answer over its bound is refused")
    except ValueError:
        pass
    expect(r.shown_conflicts is None
           and body(r.post(headers(), BASE + "copy-conflicts", b""))["code"] == "conflicts_not_read",
           "a list never sent is never copied")


def test_conflicts_copy(folder: Path):
    """COPY in the conflicts view copies the list the service last sent, never a text the page gives."""
    windows = FakeWindows()
    r, _lines, parts = make(folder, windows)
    expect(body(r.post(headers(), BASE + "copy-conflicts", b""))["code"] == "conflicts_not_read"
           and windows.copied == [], "nothing copied before the conflicts are shown")
    r.get(headers(), BASE + "conflicts")
    expect(body(r.post(headers(), BASE + "copy-conflicts", b""))["state"] == "ok" and windows.copied[0] ==
           "Logs & Conflicts 1.0.0 | conflicts between mods | checked at 14:32:05\n"
           "1 conflict(s) found between your mods.\n"
           "2 enabled mods, 3 keys, 0 console commands and 2 mod package files (.pak, .utoc) checked.\n"
           'KEYS USED BY SEVERAL MODS\nF5: A, action "Bind" | B, action "Bind"\n',
           "the conflicts copied as the page shows them in English, a title per section, one conflict per line")
    expect(r.post(headers(), BASE + "copy-conflicts", b'{"text":"x"}')[0] == 400 and len(windows.copied) == 1,
           "a body on the conflicts' COPY is refused")
    parts["mods"] = lambda: [Mod("A", ["F5"])]
    r.get(headers(), BASE + "conflicts")
    r.post(headers(), BASE + "copy-conflicts", b"")
    expect(windows.copied[-1].endswith("checked at 14:32:05\nNo conflict found between your mods.\n"
                                       "1 enabled mods, 1 keys, 0 console commands and 2 mod package files (.pak, "
                                       ".utoc) checked.\n"), "no conflict said in the copy")
    r.get(headers(), BASE + "log")
    r.post(headers(), BASE + "copy", b"")
    expect(windows.copied[-1].startswith("Logs & Conflicts 1.0.0 | unrealsdk.log"),
           "the log's COPY still copies the log")


def test_unreadable_paks_logged(folder: Path):
    """A container that cannot be read is named in our log once per listing, its name kept to plain signs."""
    r, lines, parts = make(folder)
    parts["paks"] = Paks(unreadable=1, failures=[("~mods/odd name\n=x_P.pak", "encrypted index")])
    r.get(headers(), BASE + "conflicts")
    expect("[LogsConflicts] PAK_UNREADABLE name=~mods_odd_name__x_P.pak reason=encrypted_index" in lines,
           "the container and the cause, nothing that reads as another field")
    expect(any(line.startswith("[LogsConflicts] CONFLICTS_SENT") and " unreadable_paks=1 " in line
               for line in lines), "the unreadable containers counted in the conflicts' line")
    parts["paks"] = Paks(unreadable=1, failures=[("a_P.pak", "x")], fresh=False)
    r.get(headers(), BASE + "conflicts")
    expect(not any("name=a_P.pak" in line for line in lines), "a listing already read is not logged again")
    parts["paks"] = Paks(unreadable=1, failures=[("n" * 100, "r" * 60)])
    r.get(headers(), BASE + "conflicts")
    expect(f"[LogsConflicts] PAK_UNREADABLE name={'n' * 80} reason={'r' * 48}" in lines,
           "a long name and cause cut to their bounds")
    parts["mods"] = lambda: [Mod(f"M{index}", []) for index in range(C["conflicts"]["maxMods"] + 1)]
    r.get(headers(), BASE + "conflicts")
    expect(any(line.startswith("[LogsConflicts] CONFLICTS_SENT") and " partial=1 cut=0 " in line for line in lines),
           "lists past their bounds said partial in our log, apart from the cut")
    parts["paks"] = Paks(unreadable=0, failures=[("b_P.pak", "hash_count out of bounds")])
    r.get(headers(), BASE + "conflicts")
    expect("[LogsConflicts] PAK_UNREADABLE name=b_P.pak reason=hash_count_out_of_bounds" in lines,
           "a hash that could not be read told with the container, though the container was read")


def test_actions(folder: Path):
    windows = FakeWindows()
    r, lines, parts = make(folder, windows)
    expect(body(r.post(headers(), BASE + "copy", b""))["code"] == "nothing_to_copy" and windows.copied == [],
           "nothing copied before the log is shown")
    r.get(headers(), BASE + "log")
    answer = body(r.post(headers(), BASE + "copy", b""))
    expect(answer["state"] == "ok" and windows.copied[0].startswith("Logs & Conflicts 1.0.0 | unrealsdk.log | "
                                                                    "read at 14:32:05 | 6 bytes\nhello\n"),
           "the shown text copied under its header")
    expect(r.post(headers(), BASE + "copy", b'{"text":"x"}')[0] == 400 and len(windows.copied) == 1,
           "a body on COPY is refused: the page cannot choose what is copied")
    expect(r.post(headers(), BASE + "copy", None)[0] == 413 and len(windows.copied) == 1,
           "a body too long is never taken for an empty one")
    expect(body(r.post(headers(), BASE + "open-folder", b""))["state"] == "ok" and windows.opened == [folder],
           "the folder found at start is opened")
    expect(r.post(headers(), BASE + "open-folder", b"C:\\Windows")[0] == 400 and windows.opened == [folder],
           "a folder sent by the page is refused")
    expect(r.post(headers("https://example.com"), BASE + "copy", b"")[0] == 403 and len(windows.copied) == 1,
           "a web page cannot copy")
    expect(r.get(headers(), BASE + "copy")[0] == 404, "an action is not a GET route")
    event = json.dumps({"marker": C["marker"], "event": "page_opened", "host": "pause"}).encode()
    expect(r.post(headers(), BASE + "event", event)[0] == 200 and lines[-1] == "[LogsConflicts] event=page_opened "
                                                                               "host=pause", "event logged")
    expect(r.post(headers(), BASE + "event", b"{}")[0] == 400, "malformed event refused")


def test_refusal_logged(folder: Path):
    r, lines, _ = make(folder)
    refused = Message()
    refused["Host"] = "evil.example:80"
    expect(r.get(refused, BASE + "hello")[0] == 403 and "[LogsConflicts] REFUSED reason=untrusted" in lines,
           "a refused request is written, without its headers")


def test_failures(folder: Path):
    windows = FakeWindows(copy_result=(False, 4, "open"), folder_result="failed_5")
    r, lines, parts = make(folder, windows)
    r.get(headers(), BASE + "log")
    expect(body(r.post(headers(), BASE + "copy", b""))["code"] == "clipboard_busy", "busy clipboard told")
    expect(lines[-2] == "[LogsConflicts] COPY_FAILED reason=open tries=4 error=5"
           and lines[-1].startswith("[LogsConflicts] LOG_BUDGET_REACHED kind=copy_failed"),
           "copy failure logged once, then the stop said")
    windows.copy_result = (False, 1, "alloc")
    expect(body(r.post(headers(), BASE + "copy", b""))["code"] == "clipboard_failed", "refused copy told apart")
    expect(body(r.post(headers(), BASE + "open-folder", b""))["code"] == "folder_failed", "folder failure told")
    windows.folder_result = "missing"
    r.post(headers(), BASE + "open-folder", b"")
    expect("[LogsConflicts] FOLDER_FAILED reason=failed_5" in lines and "[LogsConflicts] FOLDER_FAILED reason=missing"
           in lines, "the folder's failures counted by cause")
    parts["log_path"] = folder / "absent.log"
    expect(body(r.get(headers(), BASE + "log"))["code"] == "log_missing", "missing log told")
    for _ in range(C["http"]["maxEventLogs"] + 5):
        r.get(headers(), BASE + "log")
    expect(sum("LOG_FAILED" in line for line in lines) == C["http"]["maxFailedLogs"]
           and sum("LOG_BUDGET_REACHED kind=log_failed" in line for line in lines) == 1,
           "a repeated failure written once, then said once to stop")
    # A folder in the log's place: Windows refuses to open it as a file.
    parts["log_path"] = folder
    expect(body(r.get(headers(), BASE + "log"))["code"] == "log_refused"
           and "[LogsConflicts] LOG_FAILED reason=log_refused" in lines,
           "a failure of another cause still shows after the first one's budget")
    expect(any(line.startswith("[LogsConflicts] COPY_FAILED reason=alloc") for line in lines),
           "the clipboard's failures counted by step")


with tempfile.TemporaryDirectory() as temporary:
    for index, test in enumerate((test_reads, test_long_log, test_cut_inside_paths, test_cut_inside_a_character,
                                  test_conflicts_bound, test_conflicts_too_big, test_conflicts_copy,
                                  test_unreadable_paks_logged, test_actions,
                                  test_refusal_logged, test_failures)):
        folder = Path(temporary) / str(index)
        folder.mkdir()
        test(folder)
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
