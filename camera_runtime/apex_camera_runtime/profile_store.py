"""The camera profiles' one file, shared by the three camera mods (Kevin, 2026-10-07: « les trois mods à la troisième
personne lisent les mêmes profils »). Only this module reads and writes it, from the one shared runtime (profiles.py).

Read tolerantly, written strictly (docs/third_person_fov/camera/2026-10-12-conception-profils-camera.md). A profile
that does not read is left out with a line in the log, and the file it came from is copied aside at the next save,
never overwritten: it holds hours of the player's tuning. Each change is written before memory takes it, so a save
that fails changes nothing. One profile's checks are profile_entry.py's.
"""

import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from . import profile_values
from .profile_entry import MAX_ID, Profile, Refused, checked_name, clash, normalized_keys, read, written

VERSION = 1
FILE_NAME = "camera_profiles.json"
# The first free one takes a file set aside; past the last, the store refuses to save rather than lose one.
ASIDE_NAMES = tuple(f"camera_profiles.unreadable{suffix}.json" for suffix in ("", *(f"-{n}" for n in range(2, 10))))
# Ten fit the PROFILS page (decisions of 2026-10-12).
MAX_PROFILES = 10


def default_path() -> Path:
    from mods_base import SETTINGS_DIR
    return Path(SETTINGS_DIR) / FILE_NAME


class Store:
    def __init__(self, path: Callable[[], Path] = default_path,
                 note: Callable[[str], None] = lambda _message: None) -> None:
        self._path, self.note = path, note
        self.profiles: tuple[Profile, ...] = ()
        self.active: int | None = None
        self.loaded = False
        # The file did not read whole: moved aside before the next save.
        self._aside = False
        # The file could not be opened at all: nothing is saved over it this session.
        self._blocked = False

    @property
    def writable(self) -> bool:
        """False once the file could not be opened: every save would fail this session (load)."""
        return not self._blocked

    def load(self) -> None:
        self.loaded = True
        try:
            path = self._path()
        except Exception as error:
            # No settings folder to be found: the profiles stay off this session, the camera goes on.
            self._blocked = True
            self.note(f"camera profiles: settings folder unavailable ({type(error).__name__})")
            return
        try:
            raw = path.read_bytes()
        except FileNotFoundError:
            return
        except OSError as error:
            self._blocked = True
            self.note(f"camera profiles: file unreadable, nothing saved this session ({type(error).__name__})")
            return
        try:
            # utf-8-sig: a text editor may put a byte order mark first when the player saves the file by hand.
            data = json.loads(raw.decode("utf-8-sig"))
        except (ValueError, RecursionError):
            data = None
        if type(data) is not dict or type(data.get("profiles")) is not list:
            self._aside = True
            self.note("camera profiles: file unreadable, set aside at the next save")
            return
        if data.get("version") != VERSION:
            self._aside = True
            self.note("camera profiles: unknown file version, set aside at the next save")
        entries = data["profiles"]
        if len(entries) > MAX_PROFILES:
            self._aside = True
            self.note(f"camera profiles: more than {MAX_PROFILES}, the first kept")
        profiles = []
        for entry in entries[:MAX_PROFILES]:
            try:
                profile = read(entry)
                clash(profiles, profile)
            except ValueError as error:
                self._aside = True
                self.note(f"camera profiles: one left out ({error})")
                continue
            profiles.append(profile)
        self.profiles = tuple(profiles)
        active = data.get("active")
        self.active = active if type(active) is int and self.profile(active) is not None else None

    def profile(self, ident) -> Profile | None:
        return next((profile for profile in self.profiles if profile.ident == ident), None)

    def put(self, ident: int | None, name, values: profile_values.Values, keyboard=None, controller=None, *,
            activate: bool = False) -> Profile:
        """A new profile (ident None) or a changed one; activate also switches it on, in the same write."""
        if ident is None:
            if len(self.profiles) >= MAX_PROFILES:
                raise Refused("profiles_full")
            ident = max((profile.ident for profile in self.profiles), default=0) + 1
            if ident > MAX_ID:
                # Only after a file edited by hand: the smallest free one, which the next load reads back.
                ident = next(number for number in range(1, MAX_ID + 1) if self.profile(number) is None)
        elif self.profile(ident) is None:
            raise Refused("profile_unknown")
        values = profile_values.make(**asdict(values))
        profile = Profile(ident, checked_name(name), values, *normalized_keys(keyboard, controller))
        clash([other for other in self.profiles if other.ident != ident], profile)
        kept = [profile if other.ident == ident else other for other in self.profiles]
        if all(other.ident != ident for other in self.profiles):
            kept.append(profile)
        self._commit(tuple(kept), ident if activate else self.active)
        return profile

    def delete(self, ident: int) -> None:
        if self.profile(ident) is None:
            raise Refused("profile_unknown")
        self._commit(tuple(profile for profile in self.profiles if profile.ident != ident),
                     None if self.active == ident else self.active)

    def activate(self, ident: int | None) -> None:
        if ident is not None and self.profile(ident) is None:
            raise Refused("profile_unknown")
        self._commit(self.profiles, ident)

    def _commit(self, profiles: tuple, active: int | None) -> None:
        if self._blocked:
            raise OSError("camera profiles file unreadable this session")
        path = self._path()
        if self._aside and path.exists():
            self._set_aside(path)
        text = json.dumps({"version": VERSION, "active": active, "profiles": [written(item) for item in profiles]},
                          ensure_ascii=False, indent=1) + "\n"
        temp = path.with_name(path.name + ".tmp")
        try:
            temp.write_bytes(text.encode("utf-8"))
            os.replace(temp, path)
        except OSError:
            temp.unlink(missing_ok=True)
            raise
        self._aside = False
        self.profiles, self.active = profiles, active

    def _set_aside(self, path: Path) -> None:
        target = next((path.with_name(name) for name in ASIDE_NAMES if not path.with_name(name).exists()), None)
        if target is None:
            raise OSError("camera profiles: no free name to set the unreadable file aside")
        # Copied, not moved: the file stays until the new one replaces it, so a failed write loses nothing.
        try:
            shutil.copyfile(path, target)
        except OSError:
            target.unlink(missing_ok=True)
            raise
        self._aside = False
        self.note(f"camera profiles: unreadable file set aside as {target.name}")
