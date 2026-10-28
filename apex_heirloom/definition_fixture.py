"""The Jakobs knife's definition, cosmetics/heirloom/jakobs_knife/heirloom.json: the one place its hold, pose, lists,
model and look are written, which some tests compare the mod with.

It stays in the private workshop, its reasons written in French for Kevin. The public copy has no such folder: there,
those checks print SKIP and every other check runs (2026-09-27, Apex Heirloom's first public release).
"""

import json
import pathlib

_FOLDERS = pathlib.Path(__file__).resolve().parents
# None when the copy sits too near a drive's root to have the workshop's folders above it (review of 2026-09-27).
PATH = _FOLDERS[2] / "jakobs_knife" / "heirloom.json" if len(_FOLDERS) > 2 else None


def load() -> dict | None:
    return json.loads(PATH.read_text(encoding="utf-8")) if PATH is not None and PATH.is_file() else None


def skip(label: str) -> None:
    print(f"SKIP  | {label} (no heirloom.json in this copy)")
