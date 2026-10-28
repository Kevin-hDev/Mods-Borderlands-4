# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of catalog.py on the SDK's own option classes (fixture_sdk.py). python test_catalog.py"""

import copy
import json
import sys
import threading
from pathlib import Path

import package_path  # noqa: F401  (before the package's modules)
import fixture_sdk
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


def world(constants=BASE):
    sdk = fixture_sdk.sdk()
    test_mod = fixture_test_mod.build(sdk, constants, sdk.folder, lambda _: None, threading.get_native_id())
    sdk.register_mod(test_mod)
    return sdk, test_mod


def find(entries, label):
    for row in entries:
        if row.get("label") == label:
            return row
        found = find(row.get("entries", []), label)
        if found:
            return found
    return None


def test_test_mod():
    sdk, test_mod = world()
    model, table, counts = catalog.build(BASE, sdk_source.SdkSource(sdk, lambda: None))
    mod = model["mods"][0]
    check("one mod, writable", len(model["mods"]) == 1 and mod["writable"] is True and mod["name"] == "Sample Mod")
    kinds = [row["kind"] for row in mod["entries"]]
    check("enabled row first, its label left to the page", mod["entries"][0] == {"kind": "toggle", "id": "m0_on",
                                                                              "value": False})
    check("groups as titles, inline", kinds[1:3] == ["title", "title"])
    check("every kind shown", {"slider", "toggle", "stepper", "dropdown", "keybind", "button", "nested"} <= set(kinds))
    fraction = find(mod["entries"], "Fraction")
    check("float slider keeps its step's decimals", fraction["decimals"] == 1 and fraction["step"] == 0.1)
    check("integer slider has no decimals", find(mod["entries"], "Whole number")["decimals"] == 0)
    arrows = find(mod["entries"], "Arrows")
    check("choices sent with the index of the value", arrows["items"] == ["Low", "Medium", "High", "Ultra"]
          and arrows["value"] == 1)
    nested = find(mod["entries"], "More settings")
    check("nested page holds its rows", [row["label"] for row in nested["entries"]] == ["Inner switch", "Inner number"])
    check("each id in the table", all(row_id in table for row_id in ("m0", "m0_on", arrows["id"], nested["id"])))
    check("ids follow the constants", all(protocol.is_id(row_id, BASE) for row_id in table))
    check("counts", counts.mods == 1 and counts.unsupported == 0 and counts.failed_mods == 0)
    check("model is JSON", json.loads(json.dumps(model)) == model)


def test_real_mods_locked_and_bounded():
    sdk, test_mod = world()
    options = sdk

    class Custom(options.BaseOption):
        def __init__(self, identifier):
            self.identifier = identifier
            self.is_hidden = False
            self.display_name = identifier

        def _to_json(self):
            return ...

        def _from_json(self, value):
            pass

    deep = options.BoolOption("deepest", True)
    for level in range(6):
        deep = options.NestedOption(f"level{level}", [deep])
    real = sdk.Mod(name="<font color='#ff0000'>Real</font> mod", options=[
        options.SliderOption("speed", 2.0, 0.0, 10.0, step=0.5, is_integer=False),
        options.BoolOption("hidden", True, is_hidden=True),
        Custom("custom"),
        options.DropdownOption("empty", "x", ["x"]),
        options.KeybindOption("unbound", None),
        deep,
    ])
    locked = sdk.Mod(name="Locked", enabling_locked=True, options=[options.BoolOption("b", True)])
    broken = sdk.Mod(name="Broken")
    broken.listing_fails = True
    own = sdk.Mod(name="Mod Settings")
    for mod in (real, locked, broken, own):
        sdk.register_mod(mod)
    model, table, counts = catalog.build(BASE, sdk_source.SdkSource(sdk, lambda: own))
    shown = {mod["name"]: mod for mod in model["mods"]}
    check("html removed from names", "Real mod" in shown)
    check("other mods writable", shown["Real mod"]["writable"] is True and table["m1_on"].writable is True)
    check("Mod Settings itself locked", shown["Mod Settings"]["writable"] is False
          and table["m4_on"].writable is False)
    check("hidden option not shown", find(shown["Real mod"]["entries"], "hidden") is None)
    check("unknown option type counted, not shown", counts.unsupported == 1 and find(shown["Real mod"]["entries"], "custom") is None)
    check("unbound key sent as null", find(shown["Real mod"]["entries"], "unbound")["value"] is None)
    check("nesting cut at its depth", counts.truncated >= 1 and find(shown["Real mod"]["entries"], "deepest") is None)
    check("no enabled row when locked", all(not row.get("id", "").endswith("_on")
                                            for row in shown["Locked"]["entries"]))
    check("a failing listing is marked and counted", shown["Broken"].get("failed") is True and counts.failed_mods == 1)


def test_bounds():
    constants = copy.deepcopy(BASE)
    constants["catalog"].update(maxMods=2, maxEntriesPerPage=3, maxLabel=5)
    sdk, test_mod = world(constants)
    for index in range(3):
        sdk.register_mod(sdk.Mod(name=f"Extra mod {index}"))
    model, _table, counts = catalog.build(constants, sdk_source.SdkSource(sdk, lambda: None))
    check("mods bounded", len(model["mods"]) == 2 and counts.truncated >= 2)
    check("rows per page bounded", len(model["mods"][0]["entries"]) == 3)
    check("labels bounded", all(len(row.get("label", "")) <= 5 for row in model["mods"][0]["entries"]))
    # A list longer than the bound, cut, showed its first choice when the value was further down (review).
    long_choices = [f"Choice {index}" for index in range(BASE["catalog"]["maxChoices"] + 1)]
    sdk, _test_mod = world()
    sdk.register_mod(sdk.Mod(name="Long list", options=[
        sdk.DropdownOption("long", long_choices[-1], long_choices),
        sdk.DropdownOption("short", "b", ["a", "b"])]))
    model, _table, counts = catalog.build(BASE, sdk_source.SdkSource(sdk, lambda: None))
    listed = model["mods"][1]["entries"]
    check("a list longer than the bound is left out whole, and counted",
          find(listed, "long") is None and counts.unsupported == 1)
    check("a list within the bound is shown with its value", find(listed, "short")["value"] == 1)


def test_descriptions():
    sdk, test_mod = world()
    other = sdk.Mod(name="Described", version="2.1", author="Someone", description="<b>Bold</b> &amp; text<br><br><br>End",
                    options=[sdk.BoolOption("plain", True, description="  spaced   words  ")])
    sdk.register_mod(other)
    model, _table, _counts = catalog.build(BASE, sdk_source.SdkSource(sdk, lambda: None))
    mod, described = model["mods"]
    check("mod description as plain text, its line break kept", mod["description"] ==
          "A sample mod: each kind of setting, and pages laid out as tabs.\nEvery row can change.")
    check("mod version and author", mod["version"] == "1.0" and mod["author"] == "Sample author")
    check("markup removed, blank lines collapsed to one", described["description"] == "Bold & text\n\nEnd")
    whole = find(mod["entries"], "Whole number")
    check("row description sent", whole["description"] == "A whole number from 0 to 100, in steps of 5.")
    check("title not sent when it is the label", "descriptionTitle" not in whole)
    check("own title sent", find(mod["entries"], "Switch")["descriptionTitle"] == "Switch title")
    check("empty description not sent", "description" not in find(mod["entries"], "Fraction"))
    check("page description sent", find(mod["entries"], "Pages")["description"].startswith("A page with pages"))
    check("spaces of a description collapsed", find(described["entries"], "plain")["description"] == "spaced words")
    tight = copy.deepcopy(BASE)
    tight["catalog"]["maxDescription"] = 8
    bounded, _table, _counts = catalog.build(tight, sdk_source.SdkSource(sdk, lambda: None))
    check("descriptions bounded", all(len(entry.get("description", "")) <= 8 for entry in bounded["mods"])
          and len(find(bounded["mods"][0]["entries"], "Whole number")["description"]) == 8)


def test_clean_change():
    sdk, test_mod = world()
    _model, table, _counts = catalog.build(BASE, sdk_source.SdkSource(sdk, lambda: None))
    keys = BASE["capture"]["keys"]
    by_label = {entry.model.get("label"): entry for entry in table.values() if entry.model is not None and "label" in entry.model}
    clean = catalog.clean_change
    refused = catalog.REFUSED
    whole, fraction = by_label["Whole number"], by_label["Fraction"]
    check("integer slider gives an int", clean(whole, 55.4, keys) == 55 and isinstance(clean(whole, 55.4, keys), int))
    check("float slider keeps its value", clean(fraction, 1.3, keys) == 1.3)
    check("slider out of range refused", clean(whole, 101, keys) is refused and clean(whole, float("nan"), keys) is refused)
    check("slider bool refused", clean(whole, True, keys) is refused)
    check("slider int too big for a float refused, no error", clean(whole, 10 ** 400, keys) is refused
          and clean(fraction, float("inf"), keys) is refused)
    check("toggle takes bools only", clean(by_label["Switch"], True, keys) is True and clean(by_label["Switch"], 1, keys) is refused)
    check("index to choice", clean(by_label["Arrows"], 2, keys) == "High" and clean(by_label["List"], 4, keys) is refused)
    check("key from the catalogue, or cleared", clean(by_label["Key"], "K", keys) == "K"
          and clean(by_label["Key"], None, keys) is None and clean(by_label["Key"], "Nope", keys) is refused)
    check("a button takes no value", clean(by_label["Button"], 1, keys) is refused)


def main():
    test_test_mod()
    test_real_mods_locked_and_bounded()
    test_bounds()
    test_descriptions()
    test_clean_change()
    print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


main()
