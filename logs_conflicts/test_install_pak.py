# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of install_pak.py on files in a temporary folder. python test_install_pak.py"""

import sys
import tempfile
from pathlib import Path

import install_pak as i

FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


def refused(action, label):
    try:
        action()
        expect(False, f"refused: {label}")
    except i.InstallError:
        pass


with tempfile.TemporaryDirectory() as folder:
    built, target = Path(folder) / "built.pak", Path(folder) / "game.pak"
    built.write_bytes(b"new")
    expected = i.sha256(built)
    earlier_file = Path(folder) / "old.pak"
    earlier_file.write_bytes(b"old")
    earlier = {i.sha256(earlier_file)}
    expect(i.state(target, expected) == "absent", "absent before install")
    expect(i.install(built, target, expected) == "installed" and target.read_bytes() == b"new", "installed")
    expect(i.install(built, target, expected) == "already installed", "second install changes nothing")
    target.write_bytes(b"old")
    expect(i.install(built, target, expected, earlier) == "replaced an earlier build", "earlier build replaced")
    target.write_bytes(b"someone else's")
    refused(lambda: i.install(built, target, expected, earlier), "install over a foreign file")
    refused(lambda: i.remove(target, expected, earlier), "remove a foreign file")
    expect(target.read_bytes() == b"someone else's", "foreign file untouched")
    target.write_bytes(b"new")
    expect(i.remove(target, expected) == "removed" and not target.exists(), "removed")
    expect(i.remove(target, expected) == "already absent", "second removal changes nothing")
    expect(not list(Path(folder).glob("*.partial")), "no partial copy left")

games = {"neuf": r"W:\Game", "epic": r"U:\Other"}
expect(i.parse(["--verifier"], games, "neuf") == ("--verifier", r"W:\Game"), "default game")
expect(i.parse(["--installer", "--jeu", "epic"], games, "neuf") == ("--installer", r"U:\Other"), "named game")
for argv in ([], ["--bad"], ["--installer", "--jeu", "nope"], ["--installer", "epic"]):
    expect(i.parse(argv, games, "neuf") is None, f"command refused: {argv}")
refused(lambda: i.plan("logs-conflicts_1000_P.pak", {"pak": "other_P.pak", "pakSha256": "x"}, r"W:\Game"),
        "a manifest naming another pak")
expect(i.main(["--bad"], games=(games, "neuf"), name="x_P.pak") == 2, "unknown option refused")
expect(i.expected_pak_name() == "logs-conflicts_1000_P.pak", "pak name from the shared menu file's version")

print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
