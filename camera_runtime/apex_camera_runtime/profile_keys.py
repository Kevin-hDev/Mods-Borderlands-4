"""The camera profiles' keys, read each frame on the game's key states, as the optic zoom key is (sniper_zoom.py).

The profiles are shared by the three camera mods and their number changes, where the SDK's keybinds are declared once
per mod when it loads (docs/third_person_fov/camera/2026-10-12-conception-profils-camera.md). Like the camera
commands, a key is never taken from the game.
"""

from typing import Any, Callable

# Twenty keys at most are in use (ten profiles, two devices); the cache starts over past this.
MAX_KEYS = 64


class ProfileKeys:
    def __init__(self, load: Callable) -> None:
        """load() gives (make_key, log), asked once a profile has a key: the runtime exists before the game's
        modules can be read, as in the camera mods' tests."""
        self.load = load
        self.game = None
        self.keys: dict = {}
        # The keys down at the last reading; None until a first reading, so a key held then waits for its release.
        self.down: set | None = None
        self.failed = False

    def pressed(self, pc: Any, profiles: tuple) -> int | None:
        """The identifier of the profile whose key went down since the last reading, else None."""
        owners = {name: profile.ident for profile in profiles
                  for name in (profile.keyboard, profile.controller) if name is not None}
        if self.failed or pc is None or not owners:
            self.down = None
            return None
        try:
            if self.game is None:
                self.game = self.load()
            down = {name for name in owners if bool(pc.IsInputKeyDown(self._key(name)))}
        except Exception as error:
            # The keys stop for the session, with one line; the camera itself goes on.
            self.failed, self.down = True, None
            if self.game is not None:
                self.game[1](f"profile keys stopped for the session: {type(error).__name__}")
            return None
        fresh = sorted(down - self.down) if self.down is not None else []
        self.down = down
        return owners[fresh[0]] if fresh else None

    def pause(self) -> None:
        """While the profile window or the menu is open: the next reading waits for the keys held then."""
        self.down = None

    def _key(self, name: str) -> Any:
        key = self.keys.get(name)
        if key is None:
            if len(self.keys) >= MAX_KEYS:
                self.keys.clear()
            key = self.keys[name] = self.game[0](name)
        return key
