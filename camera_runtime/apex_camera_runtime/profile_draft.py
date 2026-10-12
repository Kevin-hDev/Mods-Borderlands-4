"""The profile window's draft (decisions of 2026-10-12): every change shows in game at once, the window waits while the
player closes the menu to look, and only SAVE writes it.

It lives in the shared runtime (profiles.py), never on disk: a draft is not a choice, and the game closing with the
window open leaves the camera as it was.
"""

from dataclasses import dataclass

from . import profile_values
from .camera_distance import CLOSE, FAR


@dataclass
class Draft:
    values: profile_values.Values
    name: str
    keyboard: str | None = None
    controller: str | None = None
    # The profile MODIFY opened, None for a new one.
    editing: int | None = None
    # CLOSE or FAR while the player tunes that distance: on the normal distance its slider would show nothing.
    preview: int | None = None
    # The distance the player's key had chosen when the preview began, read at the camera's next frame.
    preview_from: int | None = None

    def change(self, field: str, value) -> None:
        self.values = profile_values.changed(self.values, field, value)
        if field in ("close", "far"):
            self.preview, self.preview_from = (CLOSE if field == "close" else FAR), None

    def distance(self, chosen: int) -> int:
        """The distance to show: the one being tuned, until the player's distance key picks another."""
        if self.preview is not None and self.preview_from is None:
            self.preview_from = chosen
        if self.preview is not None and chosen != self.preview_from:
            self.preview = None
        return chosen if self.preview is None else self.preview
