"""Qualify files once before camera setup, independently of optional aiming exports."""
import ctypes

from .ads_preflight import Preflight

# Profile numbers in outils/sync_camera_builds.py's order: Steam 4845623, Epic, Steam 4906557 (2026-10-22).
BUILD_NAMES = {1: "Steam", 2: "Epic", 3: "Steam"}


class BuildPreflight(Preflight):
    def __init__(self, library, log):
        library.ads_verify_files.argtypes, library.ads_verify_files.restype = [], ctypes.c_int
        library.view_game_build.argtypes, library.view_game_build.restype = [], ctypes.c_uint
        super().__init__(library.ads_verify_files, log)
        self._build = library.view_game_build
        self._log_build = log
        self._build_reported = False

    def ready(self):
        if self.result() is not True:
            return False
        profile = self._build()
        name = BUILD_NAMES.get(profile) if type(profile) is int else None
        if not self._build_reported:
            self._build_reported = True
            self._log_build(f"camera build qualified store={name} profile={profile}" if name
                            else "camera build qualification refused")
        return name is not None
