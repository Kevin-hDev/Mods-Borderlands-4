# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of pak_overlaps.py on a Paks folder of containers built as the engine writes them (fixture_paks.py).
python test_pak_overlaps.py"""

import os
import re
import sys
import tempfile
import types
from pathlib import Path

import game_tools
import install_pak
import package_path  # noqa: F401
from logs_conflicts import pak_overlaps as o, protocol
from fixture_paks import digest, pak_flat, pak_v11, utoc

FAILURES = []
C = protocol.load_constants()
MAP = "OakGame/Content/uiresources/menu_bigmap/js/menu_bigmap.js"
PROMPT = "OakGame/Content/uiresources/prompts/js/user_prompt.js"
PAUSE = "OakGame/Content/uiresources/menu_pause/menu_pause.html"


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


def constants(**paks) -> dict:
    copied = dict(C, conflicts=dict(C["conflicts"], paks=dict(C["conflicts"]["paks"], **paks)))
    return copied


def bounded(**conflicts) -> dict:
    return dict(C, conflicts=dict(C["conflicts"], **conflicts))


def write(folder: Path, name: str, data: bytes) -> None:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_order_and_winner():
    expect(o.pak_order("mod.pak", "OakGame") == 3 and o.pak_order("mod_P.pak", "OakGame") == 103,
           "a container, and one named as a patch")
    expect(o.pak_order("mod_999_P.pak", "OakGame") == 100003 and o.pak_order("mod_1000_P.pak", "OakGame") == 100103,
           "a numbered patch: 100 x (N + 1) above")
    expect(o.pak_order("mod_0_P.pak", "OakGame") == 103 and o.pak_order("mod_x_P.pak", "OakGame") == 103,
           "a number below one, or none, counts as an unnumbered patch")
    expect(o.pak_order("mod_5_P.utoc", "OakGame") == 603 and o.pak_order("~mods/mod_5_p.PAK", "OakGame") == 603,
           "a .utoc takes its .pak's order; the ending in any case")
    expect(o.pak_order("OakGame-mod.pak", "OakGame") == 4 and o.pak_order("OakGameMod.pak", "OakGame") == 3,
           "a container named after the project, its name and a dash")
    expect(o.pak_order("oakgame-mod_P.pak", "OakGame") == 104 and o.pak_order("OAKGAME-x.utoc", "OakGame") == 4,
           "the project's name in any case, as FString::StartsWith compares by default")

    def holder(name, order, kind="pak"):
        return {"name": name, "order": order, "kind": kind}

    expect(o.winner([holder("a_P.pak", 103), holder("b.pak", 3)])["name"] == "a_P.pak", "the highest order")
    expect(o.winner([holder("a_P.pak", 103), holder("B_P.pak", 103)])["name"] == "B_P.pak",
           "at equal order, the highest name for legacy paks, in any case")
    expect(o.winner([holder("a_P.utoc", 103, "utoc"), holder("B_P.utoc", 103, "utoc")])["name"] == "a_P.utoc",
           "at equal order, the lowest name for IoStore")


def test_scan():
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        write(folder, "mod_a_P.pak", pak_v11([(MAP, b"A"), (PROMPT, b"same"), ("OakGame/a_only.js", b"a")]))
        write(folder, "~mods/mod_b_5_P.pak", pak_flat([(MAP, b"B"), (PROMPT, b"same")]))
        write(folder, "pakchunk0-Windows.pak", b"the game's own: never read")
        write(folder, "global.utoc", b"the game's own: never read")
        write(folder, "assets_P.utoc", utoc([("OakGame/Content/T_Rope.uasset", digest("rope"))]))
        write(folder, "assets_P.pak", pak_v11([]))
        write(folder, "lone_P.utoc", utoc([("OakGame/Content/T_Rope.uasset", digest("rope"))]))
        write(folder, "lone/other_P.utoc", b"never read: no .pak beside it")
        write(folder, "loose_P.pak", pak_v11([("OakGame/Content/T_Rope.uasset", b"rope")]))
        write(folder, "broken_P.pak", b"no footer here" * 8)
        write(folder, "a/b/c/d/e/deep_9_P.pak", pak_v11([(MAP, b"deep")]))
        write(folder, "notes.txt", b"not a container")
        found = o.PakScan(folder, C).find()
        expect(len(found["entries"]) == 1, f"one pair of mods in conflict ({found['entries']})")
        entry = found["entries"][0]
        expect(entry["containers"] == ["~mods/mod_b_5_P.pak", "mod_a_P.pak"]
               and entry["winner"] == entry["containers"][0],
               "the containers, the one served first, names relative to the Paks folder")
        expect(entry["count"] == 2 and entry["identical"] == 1 and entry["items"] == [MAP, PROMPT]
               and entry["more"] == 0, "files in common, identical ones counted by their stored hashes")
        expect(found["containers"] == 5 and found["unreadable"] == 1 and found["failures"] == [("broken_P.pak",
                                                                                                 "no pak footer")],
               "the game's containers and a .utoc without its .pak never read; a container that cannot be read is "
               "counted and named")
        expect(not any("lone" in name for item in found["entries"] for name in item["containers"]),
               "a .utoc without its .pak is never mounted, so never in conflict")
        expect(not found["missing"] and found["fresh"], "read now")
        expect(not any("deep" in name for item in found["entries"] for name in item["containers"]),
               "folders deeper than the bound are not walked")


def test_shared_menu():
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        write(folder, "logs-conflicts_1000_P.pak", pak_v11([(PAUSE, b"both entries")]))
        write(folder, "~mods/mod-settings_999_P.pak", pak_v11([(PAUSE, b"one entry")]))
        scan = o.PakScan(folder, C)
        expect(scan.find()["entries"] == [], "the shared menu file of our two menu mods is no conflict, wherever")
        write(folder, "hud_P.pak", pak_v11([(PAUSE, b"another menu")]))
        found = scan.find()
        expect([entry["containers"] for entry in found["entries"]] == [["logs-conflicts_1000_P.pak", "hud_P.pak"]],
               "a third mod on the menu file is shown, against the shared file's winner only")


def test_shared_menu_names():
    """The shared menu's names are written here by hand: they must stay those its two mods write."""
    shared = C["conflicts"]["paks"]["sharedMenu"]
    recipe, _builder = game_tools.menu_entries()
    menus = recipe.load_constants()
    expect(set(shared["paths"]) == {menu["path"] for menu in menus["menus"]} | {menus["scriptPath"]},
           "the shared files are the menus and the script the shared menu file writes")
    names = re.compile(shared["containers"], re.IGNORECASE)
    expect(names.match(install_pak.expected_pak_name()) and names.match(game_tools.mod_settings_pak()),
           "the two paks that carry the shared menu file, named as their mods name them")


def test_kinds_and_ties():
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        write(folder, "x_P.utoc", utoc([("OakGame/Content/A.uasset", digest("a"))]))
        write(folder, "x_P.pak", pak_v11([]))
        write(folder, "y_P.pak", pak_v11([("OakGame/Content/A.uasset", b"a")]))
        expect(o.PakScan(folder, C).find()["entries"] == [], "a .pak and a .utoc are never compared")
        write(folder, "b_P.utoc", utoc([("OakGame/Content/A.uasset", digest("a"))]))
        write(folder, "b_P.pak", pak_v11([]))
        write(folder, "c_P.pak", pak_v11([("OakGame/Content/A.uasset", b"other")]))
        found = {entry["winner"]: entry for entry in o.PakScan(folder, C).find()["entries"]}
        expect(sorted(found) == ["b_P.utoc", "y_P.pak"], f"ties broken by kind ({sorted(found)})")
        expect(found["b_P.utoc"]["identical"] == 1 and found["y_P.pak"]["identical"] == 0,
               "identical by the chunk's hash, different by the pak's")
        expect([entry["winner"] for entry in o.PakScan(folder, C).find()["entries"]] == ["y_P.pak", "b_P.utoc"],
               "files that differ first: identical copies change nothing in game")


def test_unsure_and_alone():
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        write(folder, "one_P.pak", pak_v11([(MAP, b"same"), (MAP, b"again")]))
        expect(o.PakScan(folder, C).find()["entries"] == [], "one container holding a file twice is no conflict")
        write(folder, "two_P.pak", pak_v11([(MAP, b"same")], wrong_size={MAP}))
        write(folder, "one_P.pak", pak_v11([(MAP, b"same")], wrong_size={MAP}))
        found = o.PakScan(folder, C).find()
        expect(found["entries"][0]["identical"] == 0, "files whose hashes cannot be read are never called identical")
        expect(found["failures"] == [],
               f"an entry that does not match its index is unsure, not a failed read ({found['failures']})")
        write(folder, "one_P.pak", pak_v11([(MAP, b"same"), (PROMPT, b"same")], outside={MAP}))
        write(folder, "two_P.pak", pak_v11([(MAP, b"same"), (PROMPT, b"same")]))
        found = o.PakScan(folder, C).find()
        expect(found["entries"][0]["identical"] == 1 and found["unreadable"] == 0,
               "a hash that cannot be read leaves its file different, the other files and the container read")
        expect(found["failures"] == [("one_P.pak", "hash_read outside the file or beyond the index bound")],
               f"the first hash a container cannot give, told once ({found['failures']})")


def test_names_and_failures():
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        paths = ["OakGame/Content/c.txt", "OakGame/Content/a.txt", "OakGame/Content/B.txt"]
        write(folder, "lower_P.pak", pak_v11([(path, b"x") for path in paths]))
        write(folder, "Upper_2_P.PAK", pak_v11([(path, b"y") for path in paths]))
        found = o.PakScan(folder, C).find()["entries"]
        expect(len(found) == 1 and found[0]["containers"] == ["Upper_2_P.PAK", "lower_P.pak"],
               "a container's ending in any case")
        expect(found[0]["items"] == ["OakGame/Content/a.txt", "OakGame/Content/B.txt", "OakGame/Content/c.txt"],
               "files sorted whatever their case")

        def refuse(path, mode):
            if Path(path).name == "lower_P.pak":
                raise PermissionError(13, "denied", r"C:\Users\Jane\lower_P.pak")
            return open(path, mode)

        scan = o.PakScan(folder, C, opener=refuse).find()
        expect(scan["failures"] == [("lower_P.pak", "PermissionError")],
               "a container Windows refuses: named by the error's kind, never its text, which holds a path")
        opened = []

        def once(path, mode):
            opened.append(Path(path).name)
            if opened.count("lower_P.pak") > 1 and Path(path).name == "lower_P.pak":
                raise PermissionError(13, "denied", r"C:\Users\Jane\lower_P.pak")
            return open(path, mode)

        later = o.PakScan(folder, C, opener=once).find()
        expect(later["failures"] == [("lower_P.pak", "hash_PermissionError")] and later["unreadable"] == 0
               and len(later["entries"]) == 1, "a container refused between its listing and its hashes: told, listed")


def test_bounded_names():
    """One entry alone could pass the answer's bound: its containers are bounded as its files are."""
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        long_name = "a_very_long_folder_name_for_a_mod/" * 3
        for at in range(3):
            write(folder, f"{long_name}copy{at}_P.pak", pak_v11([(MAP, b"x")]))
        entry = o.PakScan(folder, bounded(maxItems=2)).find()["entries"][0]
        expect(entry["containers"] == [f"{long_name}copy2_P.pak", f"{long_name}copy0_P.pak"]
               and entry["moreContainers"] == 1 and entry["winner"] == entry["containers"][0]
               and entry["items"] == [MAP],
               f"containers past the bound counted; names and paths kept whole, conflicts.py cuts them ({entry})")
        whole = o.PakScan(folder, C).find()["entries"][0]
        expect(whole["moreContainers"] == 0 and len(whole["containers"]) == 3, "within the bound, every container")


class Entry:
    def __init__(self, real, refused):
        self.real, self.refused = real, refused
        self.name, self.path = real.name, real.path

    def is_dir(self, follow_symlinks=True):
        return self.real.is_dir(follow_symlinks=follow_symlinks)

    def stat(self, follow_symlinks=True):
        if self.name in self.refused:
            raise FileNotFoundError(2, "gone", self.path)
        return self.real.stat(follow_symlinks=follow_symlinks)


class Listing:
    def __init__(self, entries):
        self.entries = entries

    def __enter__(self):
        return iter(self.entries)

    def __exit__(self, *_error):
        return False


def test_listing_failures():
    """A subfolder Windows refuses to list, or a container gone between the listing and its date, is counted as
    unreadable and named; only the Paks folder itself said missing (review, 2 November 2026)."""
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        write(folder, "one_P.pak", pak_v11([(MAP, b"1")]))
        write(folder, "two_P.pak", pak_v11([(MAP, b"2")]))
        write(folder, "gone_P.pak", pak_v11([(MAP, b"3")]))
        write(folder, "locked/three_P.pak", pak_v11([(MAP, b"4")]))
        real = os.scandir

        def scandir(path):
            if Path(path).name == "locked":
                raise PermissionError(13, "denied", str(path))
            with real(path) as listed:
                return Listing([Entry(entry, {"gone_P.pak"}) for entry in listed])

        o.os = types.SimpleNamespace(scandir=scandir)
        try:
            found = o.PakScan(folder, C).find()
        finally:
            o.os = os
        expect(not found["missing"] and found["containers"] == 2 and found["unreadable"] == 2
               and found["failures"] == [("gone_P.pak", "FileNotFoundError"), ("locked/", "PermissionError")],
               f"what could not be listed counted and named, the rest read ({found})")
        expect([entry["containers"] for entry in found["entries"]] == [["two_P.pak", "one_P.pak"]],
               "the containers listed are compared")
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        write(folder, "one_P.pak", pak_v11([(MAP, b"1")]))
        (folder / "locked").mkdir()
        scan = o.PakScan(folder, C)
        o.os = types.SimpleNamespace(scandir=scandir)
        try:
            first = scan.find()
        finally:
            o.os = os
        again = scan.find()
        expect(first["unreadable"] == 1 and again["fresh"] and again["unreadable"] == 0,
               "a subfolder Windows lets list again is read anew, though no container changed")


def test_bounds_and_cache():
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        files = [(f"OakGame/Content/f{index:02}.js", b"x") for index in range(20)]
        write(folder, "one_P.pak", pak_v11(files))
        write(folder, "two_2_P.pak", pak_v11(files))
        scan = o.PakScan(folder, C)
        entry = scan.find()["entries"][0]
        expect(len(entry["items"]) == C["conflicts"]["maxItems"] and entry["more"] == 20 - C["conflicts"]["maxItems"]
               and entry["count"] == 20, "an entry keeps its bound of lines, and counts the rest")
        expect(scan.find()["fresh"] is False, "kept while the listing is the same")
        write(folder, "three_P.pak", pak_v11([("OakGame/Content/other.js", b"y")]))
        expect(scan.find()["fresh"] is True, "read again when the listing changes")
        os.utime(folder / "three_P.pak", ns=(1, 1))
        expect(scan.find()["fresh"] is True, "read again when a container's date changes")
        few = o.PakScan(folder, constants(maxContainers=2)).find()
        expect(few["containers"] == 2 and few["failures"] == [("two_2_P.pak", "not_read")] and few["unreadable"] == 1,
               "containers past the bound are counted as not read")
        budget = o.PakScan(folder, constants(maxFiles=25)).find()
        expect(budget["containers"] == 2 and budget["unreadable"] == 1,
               "past the bound of files, a container is not read")
        spent = o.PakScan(folder, constants(maxFiles=20)).find()
        expect(spent["containers"] == 1
               and spent["failures"] == [("three_P.pak", "files_bound"), ("two_2_P.pak", "files_bound")],
               f"the bound of files spent, the containers left are said not read for it ({spent['failures']})")
    expect(o.PakScan(None, C).find()["missing"] and o.PakScan(Path(name), C).find()["missing"],
           "no folder, or one that is gone: said missing")


for test in (test_order_and_winner, test_scan, test_shared_menu, test_shared_menu_names, test_kinds_and_ties,
             test_unsure_and_alone, test_names_and_failures, test_bounded_names, test_listing_failures,
             test_bounds_and_cache):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
