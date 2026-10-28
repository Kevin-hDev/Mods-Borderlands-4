"""The camera profiles' one entry point (docs/third_person_fov/camera/2026-10-12-conception-profils-camera.md).

The shared runtime holds one (shared.py), so the three camera mods' menus and the camera itself all reach the same
profiles, the same draft and the same keys through it. What the camera shows is the draft while the profile window is
open, else the profile switched on, else the mod's own settings (profile_overlay.py).
"""

from . import profile_values
from .profile_draft import Draft
from .profile_keys import ProfileKeys
from .profile_overlay import ProfiledSettings
from .profile_entry import Profile, Refused, checked_keys
from .profile_store import Store


class Profiles:
    def __init__(self, store: Store, keys: ProfileKeys) -> None:
        self.store, self.keys = store, keys
        self.draft: Draft | None = None
        # Counts the changes of what the camera shows; the runtime writes the FOV at once when it moves (runtime.py).
        self.revision = 0
        self._synced = 0

    def ready(self) -> Store:
        """The file is read at the first use, a frame or a menu, not while the mods load."""
        if not self.store.loaded:
            self.store.load()
        return self.store

    def shown(self) -> profile_values.Values | None:
        if self.draft is not None:
            return self.draft.values
        store = self.ready()
        profile = store.profile(store.active) if store.active is not None else None
        return None if profile is None else profile.values

    def distance(self, chosen: int) -> int:
        return chosen if self.draft is None else self.draft.distance(chosen)

    def wrap(self, settings) -> ProfiledSettings:
        return ProfiledSettings(settings, self)

    def available(self) -> bool:
        """Whether a profile can be saved this session; the menu hides the profiles otherwise (decisions of
        2026-10-12: invisible rather than broken)."""
        return self.ready().writable

    def free_name(self, word: str) -> str:
        """« word n » with the smallest n no profile's name has: a new profile's name, in the menu's language."""
        taken = {profile.name.casefold() for profile in self.ready().profiles}
        number = 1
        while f"{word} {number}".casefold() in taken:
            number += 1
        return f"{word} {number}"

    def open_new(self, name: str, settings, shown_fov) -> None:
        """The window for a new profile, starting from what the camera shows: the profile switched on, else the
        elected mod's settings with the FOV on screen (fov.py, FovEngine.seen)."""
        self.draft = Draft(self.shown() or profile_values.from_camera(settings, shown_fov), name)
        self._moved()

    def open_edit(self, ident: int) -> None:
        profile = self.ready().profile(ident)
        if profile is None:
            raise Refused("profile_unknown")
        self.draft = Draft(profile.values, profile.name, profile.keyboard, profile.controller, editing=ident)
        self._moved()

    def change(self, field: str, value) -> None:
        self._draft().change(field, value)
        self._moved()

    def rename(self, name: str) -> None:
        """The name as typed so far: SAVE checks it, so a name is never refused halfway through its typing."""
        self._draft().name = name

    def set_keys(self, keyboard: str | None, controller: str | None) -> None:
        """The draft's two keys, None for none; Refused, and the draft unchanged, for a key another profile has or
        one of the other device."""
        draft = self._draft()
        draft.keyboard, draft.controller = checked_keys(keyboard, controller, self.ready().profiles, draft.editing)

    def cancel(self) -> None:
        self.draft = None
        self._moved()

    def save(self) -> Profile:
        """Writes the draft and switches its profile on in the same write, so the camera does not jump; a refusal
        keeps the window open with the player's draft."""
        draft = self._draft()
        profile = self.ready().put(draft.editing, draft.name, draft.values, draft.keyboard, draft.controller,
                                   activate=True)
        self.draft = None
        self._moved()
        return profile

    def toggle(self, ident: int) -> None:
        """Switches a profile on, or back to the mod's own settings when it is the one on."""
        store = self.ready()
        store.activate(None if store.active == ident else ident)
        self._moved()

    def delete(self, ident: int) -> None:
        self.ready().delete(ident)
        self._moved()

    def sync(self, pc) -> bool:
        """Each frame: a profile's key switches it, unless the window or a draft is open. True when what the camera
        shows changed since the last frame."""
        if self.draft is None:
            ident = self.keys.pressed(pc, self.ready().profiles)
            if ident is not None:
                try:
                    self.toggle(ident)
                except OSError as error:
                    # Written before shown: a save that failed leaves the camera as it was.
                    self.store.note(f"camera profile key: save failed ({type(error).__name__})")
        else:
            self.keys.pause()
        moved, self._synced = self.revision != self._synced, self.revision
        return moved

    def _draft(self) -> Draft:
        if self.draft is None:
            raise Refused("no_draft")
        return self.draft

    def _moved(self) -> None:
        self.revision += 1


def make() -> Profiles:
    """The runtime's profiles (shared.py), writing to the SDK's log as the other units do; nothing is read yet."""
    from .sniper_zoom import game_modules
    return Profiles(Store(note=lambda message: game_modules()[1](message)), ProfileKeys(game_modules))
