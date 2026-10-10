"""The optic zoom key (second list n° 6, Kevin 2026-10-09): while a weapon aims at the shoulder with two or more
ticked zooms, each new press goes to the next one (ads_optic.py). Named for the sniper rifle, its first weapon: the
name keeps the players' saved keys.

Read each frame on the game's key states, as Free Look's keys are (free_look.py): its default keys are Free Look's,
which stops while aiming on foot, so the same key zooms while aiming and turns the camera otherwise. A key already
down when the aim starts waits for its release: only a new press zooms. One failure stops the key for the session,
the aim keeps its zoom.
"""

from typing import Any, Callable

# Bounded: two zoom keys, and a few more if the player changes them during the session.
MAX_KEYS = 8
# Frames between an aim start or a zoom change and its view's line in the log, once the view has settled: trial 1 of
# every weapon's optics (2026-10-10) saw a pistol's x3 look like its x2 and an assault rifle's x3 zoom past its x4.
REPORT_FRAMES = 20


class SniperZoom:
    def __init__(self, load: Callable) -> None:
        """load() gives (make_key, log), asked at the first press: the runtime exists before the game's modules can
        be read, as in the camera mods' tests."""
        self.load = load
        self.game = None
        self.keys: dict = {}
        self.was_down = True
        self.failed = False
        self.was_active = False
        self.report_in = 0
        self.report_failed = False

    def sync(self, settings: Any, pc: Any, controller: Any) -> None:
        ads = getattr(controller, "ads", None)
        optic = getattr(ads, "optic", None)
        read = getattr(settings, "sniper_zoom_keys", None)
        if self.failed or pc is None or optic is None or not optic.active or not callable(read):
            self.was_down, self.was_active, self.report_in = True, False, 0
            return
        try:
            if self.game is None:
                self.game = self.load()
            if not self.was_active:
                self.was_active, self.report_in = True, REPORT_FRAMES
            down = any(name is not None and bool(pc.IsInputKeyDown(self._key(name))) for name in read())
            if down and not self.was_down:
                zoom = optic.next(ads.native)
                if zoom is not None:
                    self.game[1](f"optic zoom x{zoom}")
                    self.report_in = REPORT_FRAMES
            self.was_down = down
        except Exception as error:
            self.failed = True
            if self.game is not None:
                self.game[1](f"sniper zoom key stopped for the session: {type(error).__name__}")
            return
        if self.report_in:
            self.report_in -= 1
            if not self.report_in:
                self._report(pc, ads, optic.zoom)

    def _report(self, pc: Any, ads: Any, zoom: int | None) -> None:
        """The view the .dll wrote for this zoom and the one the game shows; a failure stops the line alone."""
        if self.report_failed:
            return
        try:
            stats = ads.native.stats()
            shown = float(pc.PlayerCameraManager.GetFOVAngle())
            self.game[1](f"optic view x{zoom}: base {stats.fov_before:.1f}, ours {stats.fov_after:.1f} "
                         f"(scale {stats.zoom_scale:.3f}), shown {shown:.1f}")
        except Exception as error:
            self.report_failed = True
            self.game[1](f"optic view line stopped for the session: {type(error).__name__}")

    def _key(self, name: str) -> Any:
        key = self.keys.get(name)
        if key is None:
            if len(self.keys) >= MAX_KEYS:
                self.keys.clear()
            key = self.keys[name] = self.game[0](name)
        return key

    def stop(self) -> None:
        self.was_down = True


def game_modules() -> tuple:
    import unrealsdk
    from unrealsdk import logging
    return (lambda name: unrealsdk.make_struct("Key", KeyName=name),
            lambda message: logging.info(f"[Camera Runtime] {message}"))
