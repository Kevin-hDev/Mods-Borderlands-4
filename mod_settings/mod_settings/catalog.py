# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The mods' settings as the page shows them, read from the SDK's own objects. Pure: the SDK reaches it through a
source (mods(), kind_of(option), plain(text), writable(mod)), so the tests drive it with plain objects.

build() returns the model sent to the page and the table that turns a page's id back into its option. Each mod
says itself what it shows (Mod.iter_display_options, as the SDK's console menu reads it). Every list is bounded
(constants "catalog"): a mod with thousands of options cannot grow the page or the message without limit."""

import math

VALUE_KINDS = ("slider", "toggle", "stepper", "dropdown", "keybind")
# What clean_change returns for a refused value: None is a real value there (a cleared key).
REFUSED = object()


class Entry:
    """One row the page may act on: what it is, its option, its mod, and the bounds its values must respect."""

    __slots__ = ("kind", "option", "mod", "writable", "meta", "role", "model")

    def __init__(self, kind, option, mod, writable, meta, role, model):
        self.kind = kind
        self.option = option
        self.mod = mod
        self.writable = writable
        self.meta = meta
        self.role = role
        self.model = model


class Counts:
    def __init__(self):
        self.mods = 0
        self.entries = 0
        self.unsupported = 0
        self.truncated = 0
        self.failed_mods = 0
        self.widest_page = 0


def decimals(step: float, integer: bool, limit: int) -> int:
    if integer:
        return 0
    text = f"{step:.{limit}f}".rstrip("0")
    return min(limit, len(text.split(".")[1])) if "." in text else 0


class Builder:
    def __init__(self, constants: dict, source):
        self.bounds = constants["catalog"]
        self.source = source
        self.table = {}
        self.counts = Counts()

    def text(self, value) -> str:
        plain = self.source.plain(value if isinstance(value, str) else "")
        return " ".join(plain.split())[: self.bounds["maxLabel"]]

    def paragraph(self, value) -> str:
        """A description as plain text: its line breaks kept (the SDK turns <br> into one), blank lines collapsed
        to one, bounded."""
        plain = self.source.plain(value if isinstance(value, str) else "")
        lines = []
        for line in plain.split("\n"):
            clean = " ".join(line.split())
            if clean or (lines and lines[-1]):
                lines.append(clean)
        return "\n".join(lines).strip()[: self.bounds["maxDescription"]]

    def described(self, row: dict, option) -> dict:
        """The row with what the page shows beside it: the option's description, and its title when it is not
        the row's label (the SDK copies the label there by default)."""
        description = self.paragraph(getattr(option, "description", ""))
        if description:
            row["description"] = description
        title = self.text(getattr(option, "description_title", None) or "")
        if title and title != row["label"]:
            row["descriptionTitle"] = title
        return row

    def build(self) -> dict:
        mods = []
        for index, mod in enumerate(self.source.mods()):
            if index >= self.bounds["maxMods"]:
                self.counts.truncated += 1
                break
            mods.append(self.mod(f"m{index}", mod))
        self.counts.mods = len(mods)
        return {"mods": mods}

    def mod(self, mod_id: str, mod) -> dict:
        writable = bool(self.source.writable(mod))
        described = {"id": mod_id, "name": self.text(mod.name), "writable": writable, "entries": []}
        for key, value in (("description", self.paragraph(getattr(mod, "description", ""))),
                           ("version", self.text(getattr(mod, "version", ""))),
                           ("author", self.text(getattr(mod, "author", "")))):
            if value:
                described[key] = value
        self.table[mod_id] = Entry("mod", None, mod, writable, {}, "mod", described)
        serial = [0]
        page = described["entries"]
        if not getattr(mod, "enabling_locked", True):
            # No label: the page writes "Enabled" in the game's language (logic.js, texts "enabledLabel").
            row = {"kind": "toggle", "id": f"{mod_id}_on", "value": bool(mod.is_enabled)}
            self.add(page, row, Entry("toggle", None, mod, writable, {}, "enabled", row))
        try:
            for option in mod.iter_display_options():
                self.walk(option, mod, mod_id, writable, page, 0, serial)
        except Exception:
            # A mod whose own listing fails is shown with what it gave so far, and counted.
            self.counts.failed_mods += 1
            described["failed"] = True
        return described

    def add(self, page: list, row: dict, entry) -> bool:
        if len(page) >= self.bounds["maxEntriesPerPage"] or self.counts.entries >= self.bounds["maxEntries"]:
            self.counts.truncated += 1
            return False
        page.append(row)
        self.counts.entries += 1
        self.counts.widest_page = max(self.counts.widest_page, len(page))
        if entry is not None:
            self.table[row["id"]] = entry
        return True

    def walk(self, option, mod, mod_id, writable, page, depth, serial) -> None:
        if getattr(option, "is_hidden", False):
            return
        kind = self.source.kind_of(option)
        if kind is None:
            self.counts.unsupported += 1
            return
        label = self.text(getattr(option, "display_name", ""))
        if kind == "title":
            if self.add(page, {"kind": "title", "label": label}, None):
                for child in option.children:
                    self.walk(child, mod, mod_id, writable, page, depth, serial)
            return
        serial[0] += 1
        row_id = f"{mod_id}_{serial[0]}"
        if kind == "nested":
            if depth + 1 > self.bounds["maxDepth"]:
                self.counts.truncated += 1
                return
            row = self.described({"kind": "nested", "id": row_id, "label": label, "entries": []}, option)
            if self.add(page, row, Entry("nested", option, mod, writable, {}, "nested", row)):
                for child in option.children:
                    self.walk(child, mod, mod_id, writable, row["entries"], depth + 1, serial)
            return
        row, meta = self.value_row(kind, option, row_id, label)
        if row is not None:
            self.add(page, self.described(row, option), Entry(kind, option, mod, writable, meta, "option", row))

    def value_row(self, kind, option, row_id, label):
        row = {"kind": kind, "id": row_id, "label": label}
        if kind == "button":
            return row, {}
        value = option.value
        if kind == "slider":
            low, high, step = float(option.min_value), float(option.max_value), float(option.step)
            integer = bool(option.is_integer)
            if not all(math.isfinite(number) for number in (low, high, step, float(value))) or low >= high:
                self.counts.unsupported += 1
                return None, None
            places = decimals(step, integer, self.bounds["maxDecimals"])
            default = float(getattr(option, "default_value", value))
            row.update(min=low, max=high, step=step, decimals=places, value=min(high, max(low, float(value))),
                       default=min(high, max(low, default)) if math.isfinite(default) else low)
            return row, {"min": low, "max": high, "integer": integer}
        if kind == "toggle":
            row["value"] = bool(value)
            for name, attribute in (("trueText", "true_text"), ("falseText", "false_text")):
                if isinstance(getattr(option, attribute, None), str):
                    row[name] = self.text(getattr(option, attribute))
            return row, {}
        if kind in ("stepper", "dropdown"):
            choices = list(option.choices)
            # A longer list is left out whole: cut, it would hide choices and could show a wrong current value.
            if not choices or len(choices) > self.bounds["maxChoices"] \
                    or not all(isinstance(choice, str) for choice in choices):
                self.counts.unsupported += 1
                return None, None
            row["items"] = [self.text(choice) for choice in choices]
            row["value"] = choices.index(value) if value in choices else 0
            return row, {"choices": choices}
        row["value"] = value if isinstance(value, str) and value else None
        row["rebindable"] = bool(getattr(option, "is_rebindable", True))
        return row, {"rebindable": row["rebindable"]}


def build(constants: dict, source):
    """(model, table, counts): model is JSON-ready, table maps each id to its Entry."""
    builder = Builder(constants, source)
    model = builder.build()
    return model, builder.table, builder.counts


def clean_change(entry: Entry, value, keys: dict):
    """The option's new value for a page's value, or REFUSED when the row cannot take it. The page sends
    indexes for choices and the engine's key name (or null) for a key. An integer slider gets an int, as the SDK
    gives it when it loads a saved value (SliderOption._from_json)."""
    kind = entry.kind
    if kind == "slider":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return REFUSED
        meta = entry.meta
        # The bounds refuse NaN and infinities; math.isfinite would raise on an int too big for a float.
        if not meta["min"] - 1e-9 <= value <= meta["max"] + 1e-9:
            return REFUSED
        clamped = min(meta["max"], max(meta["min"], float(value)))
        return round(clamped) if meta["integer"] else clamped
    if kind == "toggle":
        return value if isinstance(value, bool) else REFUSED
    if kind in ("stepper", "dropdown"):
        choices = entry.meta["choices"]
        valid = isinstance(value, int) and not isinstance(value, bool) and 0 <= value < len(choices)
        return choices[value] if valid else REFUSED
    if kind == "keybind":
        if not entry.meta["rebindable"]:
            return REFUSED
        return value if value is None or (isinstance(value, str) and value in keys) else REFUSED
    return REFUSED
