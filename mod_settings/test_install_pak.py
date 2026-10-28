# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of install_pak.py in a temporary folder, never the game's. python test_install_pak.py"""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

import install_pak as ins

FAILURES = []


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


def raises(action):
    try:
        action()
    except ins.InstallError:
        return True
    return False


with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    build, game = root / "build", root / "Paks"
    build.mkdir()
    game.mkdir()
    built = build / "sample_999_P.pak"
    built.write_bytes(b"built bytes")
    expected = hashlib.sha256(b"built bytes").hexdigest().upper()
    target = game / "sample_999_P.pak"

    check("absent at first", ins.state(target, expected) == "absent")
    check("installs", ins.install(built, target, expected) == "installed" and target.read_bytes() == b"built bytes")
    check("no partial left", not (game / "sample_999_P.pak.partial").exists())
    check("second install is a no-op", ins.install(built, target, expected) == "already installed")
    check("removes", ins.remove(target, expected) == "removed" and not target.exists())
    check("second removal is a no-op", ins.remove(target, expected) == "already absent")

    target.write_bytes(b"someone else's pak")
    check("foreign file not overwritten", raises(lambda: ins.install(built, target, expected)))
    check("foreign file not deleted", raises(lambda: ins.remove(target, expected)) and target.exists())
    target.unlink()

    target.write_bytes(b"older build")
    older = {hashlib.sha256(b"older build").hexdigest().upper()}
    check("earlier build seen", ins.state(target, expected, older) == "earlier")
    check("earlier build replaced", ins.install(built, target, expected, older) == "replaced an earlier build"
          and target.read_bytes() == b"built bytes")
    target.write_bytes(b"older build")
    check("earlier build removable", ins.remove(target, expected, older) == "removed" and not target.exists())

    # main: the manifest must match the built bytes, and nothing moves while the game runs. The game folders come
    # from deploy_sdkmods.py in use; here two stand-ins, the default one holding the paks folder above.
    constants = {"pak": {"name": built.name, "paksFolder": "Paks"}, "version": 1}
    other_game = root / "other"
    (other_game / "Paks").mkdir(parents=True)
    games = ({"main": str(root), "other": str(other_game)}, "main")
    manifest = build / "manifest.json"
    manifest.write_text(json.dumps({"pak": built.name, "pakSha256": expected}), encoding="utf-8")
    ins.MANIFEST = manifest
    ins.pak_recipe.load_constants = lambda: constants

    def run(*argv, game_on=False):
        return ins.main(list(argv), running=lambda: game_on, games=games)

    check("game running refuses install", raises(lambda: run("--installer", game_on=True)) and not target.exists())
    check("a check of an absent pak fails", run("--verifier", game_on=True) == 1)
    check("game closed installs in the default game", run("--installer") == 0 and target.exists())
    check("a check of the installed pak passes, game open too", run("--verifier", game_on=True) == 0)
    check("another game copy chosen by --jeu", run("--installer", "--jeu", "other") == 0
          and (other_game / "Paks" / built.name).read_bytes() == b"built bytes")
    check("an unknown game copy refused", run("--installer", "--jeu", "nowhere") == 2)
    check("game running refuses removal", raises(lambda: run("--retirer", game_on=True)) and target.exists())
    check("game closed removes", run("--retirer") == 0 and not target.exists())
    target.write_bytes(b"someone else's pak")
    check("a check of a foreign file fails", run("--verifier") == 1)
    target.unlink()
    check("unknown option refused", run("--tout") == 2)
    built.write_bytes(b"rebuilt without manifest")
    check("stale manifest refused", raises(lambda: run("--installer")) and not target.exists())

    # The history of builds: the first builds' plain list is still read; an unreadable file is said, never trusted.
    history = build / "history.json"
    history.write_text(json.dumps(list(older)), encoding="utf-8")
    check("earlier builds of the first format read", ins.earlier_builds() == older)
    history.write_text("{oops", encoding="utf-8")
    check("an unreadable history gives no earlier build", ins.earlier_builds() == set())

print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
sys.exit(1 if FAILURES else 0)
