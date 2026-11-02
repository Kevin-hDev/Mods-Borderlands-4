# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of build_history.py in a temporary folder. python test_build_history.py"""

import json
import sys
import tempfile
from pathlib import Path

import build_history

FAILURES = []


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "history.json"
    check("no file: no build, no note", build_history.read(path) == ([], None))
    check("first build remembered", build_history.remember(path, "AAA") is None
          and build_history.read(path) == (["AAA"], None))
    written = json.loads(path.read_text(encoding="utf-8"))
    check("written with its version", written == {"version": build_history.VERSION, "hashes": ["AAA"]})
    build_history.remember(path, "AAA")
    check("the same build once", build_history.read(path)[0] == ["AAA"])
    check("no temporary file left", not (Path(folder) / "history.json.tmp").exists())

    path.write_text(json.dumps(["OLD1", "OLD2"]), encoding="utf-8")
    check("the first builds' plain list is read", build_history.read(path) == (["OLD1", "OLD2"], None))
    build_history.remember(path, "NEW")
    check("and kept when a build is added", build_history.read(path)[0] == ["OLD1", "OLD2", "NEW"])

    path.write_text('{"version": 1, "hash', encoding="utf-8")
    hashes, note = build_history.read(path)
    check("a cut file gives no build and says why", hashes == [] and "unreadable" in note)
    check("remembering over it says so, and writes a whole file", "unreadable" in build_history.remember(path, "B")
          and build_history.read(path) == (["B"], None))
    path.write_text(json.dumps({"version": 1, "hashes": [1, 2]}), encoding="utf-8")
    check("hashes that are not text refused", build_history.read(path)[0] == [])

    for index in range(build_history.MAX_BUILDS + 5):
        build_history.remember(path, f"H{index}")
    hashes = build_history.read(path)[0]
    check("bounded to the last builds", len(hashes) == build_history.MAX_BUILDS and hashes[-1] ==
          f"H{build_history.MAX_BUILDS + 4}")

print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
sys.exit(1 if FAILURES else 0)
