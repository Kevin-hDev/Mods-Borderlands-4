"""When the shared third-person unit is built: as soon as the elected mod runs, first person included.

Built only on the first switch, it kept that switch waiting about 2 s: the game files' check took 1.7 s of it in the
trial of 2026-10-10 (Kevin: « ça met dans les 2 secondes »). Building it does not move the camera: the view only
changes once third person, Orbit or a pending entry asks for it.
"""

from typing import Any, Callable


class SetupGate:
    def __init__(self) -> None:
        self.owner: str | None = None
        # A failure while the view is asked for is reported once; turning the view off and on tries again.
        self.failed = False
        # A failure before the view is asked for stays silent: the next request tries once more and reports it.
        self.early_failed = False

    def forget(self, owner: str) -> None:
        if self.owner == owner:
            self.owner, self.failed, self.early_failed = None, False, False

    def prepare(self, runtime: Any, owner: str, wanted: bool, setup: Callable[[Any], Any]) -> Exception | None:
        if self.owner != owner:
            self.owner, self.failed, self.early_failed = owner, False, False
        if not wanted:
            self.failed = False
            if runtime.third_person is None and not self.early_failed:
                try:
                    setup(runtime)
                except Exception:
                    self.early_failed = True
            return None
        if runtime.third_person is not None or self.failed:
            return None
        try:
            setup(runtime)
        except Exception as error:
            # No silent retry after a reported failure: only the player's next request tries again.
            self.failed = self.early_failed = True
            return error
        return None
