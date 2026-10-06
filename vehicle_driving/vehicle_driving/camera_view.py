"""The camera view at the wheel: writes the camera manager's offset each frame, and takes back only its own value
(spec section 3.8).

The game sets CameraLocationOffset back to 0 each frame and adds its own value to ours (verified in game, trials 2 to
4): once the mod stops writing, nothing stays.
"""

import math
from typing import Any

from unrealsdk.unreal import WeakPointer

from . import camera_geometry as geometry, settings

TOLERANCE = 0.001
# Far beyond any view: an offset this large means a wrong target, and the part stops rather than throw the camera.
MAX_OFFSET = 2000.0
# A summary line every 5 seconds a view writes, as the grip's: the validation reads the reticle's clearance in it.
SUMMARY_NS = 5_000_000_000


def _same(values: tuple, targets: tuple) -> bool:
    return all(math.isclose(value, target, abs_tol=TOLERANCE) for value, target in zip(values, targets))


def _read(offset: Any) -> tuple[float, float, float]:
    return float(offset.X), float(offset.Y), float(offset.Z)


class CameraView:
    def __init__(self) -> None:
        self._written: tuple | None = None
        self._applied = geometry.ZERO
        # The manager last written to, held weakly: writing into an object the game destroyed can crash it.
        self._manager: WeakPointer | None = None
        self._view: str | None = None
        self._summary_ns = 0
        self._frames = self._measured = 0
        self._below_total = 0.0

    def step(self, now_ns: int, vehicle: Any, manager: Any, view: str, custom: tuple) -> list[str]:
        """Writes this frame's offset for the view; returns a summary line when one is due."""
        if (manager is None or view == settings.DEFAULT_VIEW
                or (view == settings.CUSTOM_VIEW and _same(custom, geometry.ZERO))):
            return self.release()
        offset = manager.CameraModeState.CameraLocationOffset
        # Still ours: the game has not drawn the camera since our last write, so it carries the offset before it.
        if self._written is not None and not _same(_read(offset), self._written):
            self._applied = self._written
        seen = geometry.sighting(vehicle, manager)
        if view == settings.CUSTOM_VIEW:
            wanted = tuple(custom)
        elif seen is not None:
            wanted = geometry.zoomed(seen, self._applied, settings.VIEW_SHARES[view])
        else:
            # The driver unreadable for a frame: keep the last offset; before the first write, write nothing.
            wanted = self._written
        if wanted is None:
            return []
        if max(abs(value) for value in wanted) > MAX_OFFSET:
            raise ValueError(f"camera offset {wanted} beyond {MAX_OFFSET:g}")
        offset.X, offset.Y, offset.Z = wanted
        if not _same(_read(offset), wanted):
            raise RuntimeError("the game refused the camera offset")
        self._written = wanted
        self._manager = WeakPointer(manager)
        return self._count(now_ns, view, seen)

    def release(self) -> list[str]:
        """Stops writing, and sets the offset back to 0 if it still holds our value; returns a line if that failed.

        The game sets it back each frame anyway: this only spares the last frame.
        """
        written = self._written
        manager = self._manager() if self._manager is not None else None
        self._written, self._applied, self._manager, self._view = None, geometry.ZERO, None, None
        if written is None or manager is None:
            return []
        try:
            offset = manager.CameraModeState.CameraLocationOffset
            if _same(_read(offset), written):
                offset.X, offset.Y, offset.Z = geometry.ZERO
        except Exception as exc:
            return [f"camera offset not taken back: {exc!r}"]
        return []

    def _count(self, now_ns: int, view: str, seen: tuple | None) -> list[str]:
        if view != self._view:
            self._view, self._frames, self._measured, self._below_total = view, 0, 0, 0.0
            self._summary_ns = now_ns + SUMMARY_NS
        self._frames += 1
        if seen is not None:
            self._measured += 1
            self._below_total += geometry.below_reticle(seen)
        if now_ns < self._summary_ns:
            return []
        mean = self._below_total / self._measured if self._measured else 0.0
        line = f"camera view={view} frames={self._frames} target_below_mean={mean:.1f}"
        self._frames, self._measured, self._below_total = 0, 0, 0.0
        self._summary_ns = now_ns + SUMMARY_NS
        return [line]
