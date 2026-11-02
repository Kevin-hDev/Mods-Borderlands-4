# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Game files that the containers of two mods or more both replace, and which copy the engine serves (conception,
section 5, « Les paquets »). The game's own containers are never read. The result is kept while the folder's listing
stays the same: the paks cannot change under a running game, and a listing costs about a millisecond."""

import os
import re
import struct

from . import pak_iostore, pak_legacy
from .pak_reading import ContainerFile, Unreadable

# IPlatformFilePak.cpp, GetPakOrderFromPakFilePath (UE 5.5.4): containers under the project's content folder.
ORDER_IN_CONTENT = 3
ORDER_PROJECT_NAMED = 4
PATCH_STEP = 100
PATCH_NUMBER = re.compile(r"_([0-9]+)_p\.pak$", re.IGNORECASE)
READ_ERRORS = (Unreadable, OSError, struct.error, UnicodeDecodeError, ValueError, OverflowError)


def pak_order(name: str, project: str) -> int:
    """The engine's order for a container, its path relative to the Paks folder; a .utoc takes its .pak's. The
    project's name is compared in any case, as FString::StartsWith does by default."""
    pak = name[:-5] + ".pak" if name.lower().endswith(".utoc") else name
    order = ORDER_PROJECT_NAMED if pak.lower().startswith(project.lower() + "-") else ORDER_IN_CONTENT
    if pak.lower().endswith("_p.pak"):
        match = PATCH_NUMBER.search(pak)
        number = int(match.group(1)) if match else 0
        # A number of 0, or none, gives the unnumbered patch's 100, as the engine does.
        order += PATCH_STEP * (number + 1)
    return order


def winner(holders: list) -> dict:
    """The holder the engine serves. Highest order first; at equal order, legacy paks keep the mount order (names
    sorted downwards: the highest wins), IoStore the container mounted last (the lowest name wins). FilePackageStore.cpp
    and IoDispatcherFileBackend.cpp, UE 5.5.4, not verified in game."""
    top = max(holder["order"] for holder in holders)
    tied = [holder for holder in holders if holder["order"] == top]
    pick = max if tied[0]["kind"] == "pak" else min
    return pick(tied, key=lambda holder: holder["name"].lower())


def cause(error: Exception) -> str:
    """What the log says of a read that failed: our own cause, or the error's kind, never its text, which holds a path."""
    return str(error) if isinstance(error, Unreadable) else type(error).__name__


class PakScan:
    def __init__(self, folder, constants: dict, opener=open):
        self.folder = folder
        self.limits = constants["conflicts"]["paks"]
        self.most_items = constants["conflicts"]["maxItems"]
        self.opener = opener
        self.base = re.compile(self.limits["basePattern"], re.IGNORECASE)
        shared = self.limits["sharedMenu"]
        self.shared_names = re.compile(shared["containers"], re.IGNORECASE)
        self.shared_paths = {path.lower() for path in shared["paths"]}
        self.kept = (None, None)

    def listing(self) -> tuple:
        """([(name, full path, size, modified)] of the mods' containers, names relative to the Paks folder; [(folder,
        cause)] of the subfolders that could not be listed). Raises OSError when the Paks folder itself cannot."""
        found, unlisted, stack = [], [], [(self.folder, "", 0)]
        while stack:
            folder, prefix, depth = stack.pop()
            try:
                with os.scandir(folder) as listed:
                    entries = list(listed)
            except OSError as error:
                if not prefix:
                    raise
                unlisted.append((prefix, cause(error)))
                continue
            for entry in entries:
                name = prefix + entry.name
                if entry.is_dir(follow_symlinks=False):
                    if depth < self.limits["maxDepth"]:
                        stack.append((entry.path, name + "/", depth + 1))
                elif entry.name.lower().endswith((".pak", ".utoc")) and not self.base.match(entry.name):
                    try:
                        info = entry.stat(follow_symlinks=False)
                    except OSError as error:
                        unlisted.append((name, cause(error)))
                        continue
                    found.append((name, entry.path, info.st_size, info.st_mtime_ns))
        # The engine mounts a .utoc with its .pak only (FPakPlatformFile::Mount): alone, it is never served.
        paks = {name.lower() for name, *_rest in found if name.lower().endswith(".pak")}
        mounted = [item for item in found if not item[0].lower().endswith(".utoc") or item[0][:-5].lower() + ".pak"
                   in paks]
        return sorted(mounted), sorted(unlisted)

    def find(self) -> dict:
        """{'entries', 'containers', 'unreadable', 'missing', 'failures', 'fresh'}; entries as conflicts.py lists
        them. fresh: read now rather than kept, so a failure is written to the log once per listing."""
        missing = {"entries": [], "containers": 0, "unreadable": 0, "missing": True, "failures": [], "fresh": False}
        if self.folder is None:
            return missing
        try:
            listing, unlisted = self.listing()
        except OSError:
            return missing
        key = (tuple((name, size, modified) for name, _path, size, modified in listing), tuple(unlisted))
        fresh = self.kept[0] != key
        if fresh:
            self.kept = (key, self.scan(listing, unlisted))
        return {**self.kept[1], "fresh": fresh}

    def scan(self, listing: list, unlisted: list) -> dict:
        most = self.limits["maxContainers"]
        holders, read, failures, budget = {}, 0, list(unlisted), self.limits["maxFiles"]
        for name, path, _size, _modified in listing[:most]:
            if budget <= 0:
                failures.append((name, "files_bound"))
                continue
            kind = "utoc" if name.lower().endswith(".utoc") else "pak"
            try:
                files = self.read(path, kind, budget)
            except READ_ERRORS as error:
                failures.append((name, cause(error)))
                continue
            read += 1
            budget -= len(files)
            holder = {"name": name, "path": path, "kind": kind, "order": pak_order(name, self.limits["project"])}
            for file_path, locator in files:
                holders.setdefault((kind, file_path.lower()), []).append((holder, file_path, locator))
        failures.extend((name, "not_read") for name, *_rest in listing[most:])
        entries, unhashed = self.entries(holders)
        # A hash that could not be read leaves its file not called identical: told in the log, not counted unread.
        return {"entries": entries, "containers": read, "unreadable": len(failures), "missing": False,
                "failures": failures + unhashed}

    def read(self, path, kind: str, budget: int) -> list:
        container = ContainerFile(path, self.limits, self.opener)
        try:
            module = pak_iostore if kind == "utoc" else pak_legacy
            return module.read_files(container, budget)
        finally:
            container.close()

    def overlapping(self, holders: dict) -> list:
        """[(file path, [(holder, locator)])] held by two containers or more, the shared menu counting as one."""
        found = []
        for (_kind, lower), held in holders.items():
            if lower in self.shared_paths:
                shared = [item for item in held if self.shared_names.match(item[0]["name"].rsplit("/", 1)[-1])]
                if len(shared) > 1:
                    first = winner([item[0] for item in shared])
                    others = {id(item[0]) for item in shared if item[0] is not first}
                    held = [item for item in held if id(item[0]) not in others]
            if len({id(item[0]) for item in held}) >= 2:
                found.append((held[0][1], [(item[0], item[2]) for item in held]))
        return found

    def hashes(self, overlapping: list) -> tuple:
        """((container name, file path) -> stored hash, read only for the files in common; [(container, cause)]: the
        first hash each container could not give, each file read apart so one bad entry spoils no other."""
        wanted, found, failures = {}, {}, []
        for file_path, held in overlapping:
            for holder, locator in held:
                wanted.setdefault(holder["name"], (holder, []))[1].append((file_path, locator))
        for name, (holder, files) in wanted.items():
            if holder["kind"] == "utoc":
                # A .utoc's file list already holds each chunk's hash: nothing to open.
                found.update(((name, file_path), locator) for file_path, locator in files)
                continue
            try:
                container = ContainerFile(holder["path"], self.limits, self.opener)
            except OSError as error:
                failures.append((name, "hash_" + cause(error)))
                continue
            first = None
            try:
                for file_path, locator in files:
                    try:
                        stored = pak_legacy.stored_hash(container, locator)
                    except READ_ERRORS as error:
                        first = first or "hash_" + cause(error)
                        continue
                    found[(name, file_path)] = stored
            finally:
                container.close()
            if first:
                failures.append((name, first))
        return found, failures

    def entries(self, holders: dict) -> tuple:
        """(entries, [(container, cause)] of the hashes that could not be read)."""
        overlapping = self.overlapping(holders)
        stored, failures = self.hashes(overlapping)
        groups = {}
        for file_path, held in overlapping:
            first = winner([holder for holder, _locator in held])
            names = tuple([first["name"]] + sorted({holder["name"] for holder, _ in held} - {first["name"]}))
            group = groups.setdefault(names, {"paths": [], "identical": 0})
            group["paths"].append(file_path)
            hashes = {stored.get((holder["name"], file_path)) for holder, _locator in held}
            group["identical"] += int(len(hashes) == 1 and None not in hashes)
        entries = []
        for names, group in groups.items():
            paths = sorted(group["paths"], key=str.lower)
            # As many containers as items: one entry alone could pass the answer's bound. Names and paths are cut by
            # conflicts.py, once masked.
            entries.append({"containers": list(names[:self.most_items]),
                            "moreContainers": max(0, len(names) - self.most_items), "winner": names[0],
                            "count": len(paths), "identical": group["identical"], "items": paths[:self.most_items],
                            "more": max(0, len(paths) - self.most_items)})
        # Files that differ first: identical copies change nothing in game.
        return sorted(entries, key=lambda entry: (entry["identical"] == entry["count"], entry["containers"])), failures
