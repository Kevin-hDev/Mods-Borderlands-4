"""Validated ctypes boundary and extraction for the native camera bridge."""

import ctypes
import hashlib
import hmac
import math
import os
import pathlib
import pkgutil
import re
import secrets
from typing import Any, Callable

from .generated_ads import VIEW_ABI, VIEW_UPDATE_SLOT as UPDATE_SLOT, VIEW_UPDATE_RVA, ViewConfig as Config, ViewStats as Stats

ABI_VERSION = VIEW_ABI
EXPECTED_UPDATE_RVA = VIEW_UPDATE_RVA
MAX_LIBRARY_BYTES = 2_000_000
_FILE_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,80}\.dll$")
LIBRARY_NAME = f"apex_camera_view_v{VIEW_ABI}.dll"
HASH_NAME = f"apex_camera_view_v{VIEW_ABI}.sha256"


def make_config() -> Config:
    # The native camera adds no shoulder of its own: the game places it with its collision (shoulder_offset.py).
    return Config(ABI_VERSION, 0, UPDATE_SLOT, 0, EXPECTED_UPDATE_RVA, 0.0, 0.0)


def install_library(payload: bytes, folder: pathlib.Path, name: str, expected_sha256: str) -> pathlib.Path:
    if (not isinstance(payload, bytes) or not 2 <= len(payload) <= MAX_LIBRARY_BYTES
            or not payload.startswith(b"MZ") or not _FILE_NAME.fullmatch(name)):
        raise ValueError("invalid native camera library")
    digest = hashlib.sha256(payload).hexdigest()
    if not hmac.compare_digest(digest, expected_sha256.lower()):
        raise ValueError("invalid native camera library")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    if target.is_file() and hmac.compare_digest(hashlib.sha256(target.read_bytes()).hexdigest(), digest):
        return target
    temporary = folder / f".{name}.{secrets.token_hex(8)}.tmp"
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return target


def load_packaged_library(folder: pathlib.Path, get_data: Callable | None = None,
                          loader: Callable | None = None, *,
                          library_name: str = LIBRARY_NAME, hash_name: str = HASH_NAME) -> Any:
    read = get_data or (lambda name: pkgutil.get_data(__package__, f"assets/{name}"))
    payload, raw_hash = read(library_name), read(hash_name)
    if payload is None or raw_hash is None:
        raise RuntimeError("native camera asset missing")
    try:
        expected = raw_hash.decode("ascii")
    except (AttributeError, UnicodeDecodeError) as error:
        raise ValueError("invalid native camera hash") from error
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        raise ValueError("invalid native camera hash")
    path = install_library(payload, pathlib.Path(folder), library_name, expected)
    return (loader or (lambda item: ctypes.CDLL(str(item))))(path)


class Bridge:
    def __init__(self, library: Any) -> None:
        self.library = library
        library.view_update_rva.argtypes = []
        library.view_update_rva.restype = ctypes.c_uint64
        library.view_start.argtypes = [ctypes.c_void_p, ctypes.POINTER(Config)]
        library.view_start.restype = ctypes.c_int
        library.view_stop.argtypes, library.view_stop.restype = [], ctypes.c_int
        library.view_set_suspended.argtypes = [ctypes.c_uint32]
        library.view_set_suspended.restype = ctypes.c_int
        library.view_stats.argtypes = [ctypes.POINTER(Stats)]
        library.view_stats.restype = ctypes.c_int
        for name, arguments in (('view_set_climb_suspended', [ctypes.c_uint32]),
                                ('view_set_offset_suspended', [ctypes.c_uint32, ctypes.c_double])):
            function = getattr(library, name, None)
            if function is not None:
                function.argtypes, function.restype = arguments, ctypes.c_int

    def start(self, manager: Any) -> bool:
        try:
            address = int(manager._get_address())
        except (AttributeError, TypeError, ValueError, OverflowError):
            return False
        config = make_config()
        if address <= 0:
            return False
        target = self.library.view_update_rva()
        if type(target) is not int or not 0 < target < (1 << 32):
            raise RuntimeError("Native camera build unavailable")
        config.expected_rva = target
        status = self.library.view_start(address, ctypes.byref(config))
        if status:
            raise RuntimeError(f"native camera start refused ({status})")
        return True

    def stop(self) -> None:
        status = self.library.view_stop()
        if status:
            raise RuntimeError(f"native camera stop refused ({status})")

    def suspend_climb(self, suspended: bool) -> None:
        if type(suspended) is not bool:
            raise ValueError('Invalid climbing suspension')
        if self.library.view_set_climb_suspended(int(suspended)):
            raise RuntimeError('Camera climbing transition refused')

    def suspend_offset(self, suspended: bool, seconds: float) -> None:
        from .transition_catalog import SHOULDER_SECONDS_MAX
        if (type(suspended) is not bool or type(seconds) not in (int, float)
                or not math.isfinite(seconds) or not 0 <= seconds <= SHOULDER_SECONDS_MAX):
            raise ValueError('Invalid camera offset transition')
        if self.library.view_set_offset_suspended(int(suspended), float(seconds)):
            raise RuntimeError('Camera offset transition refused')

    def suspend(self, suspended: bool) -> None:
        status = self.library.view_set_suspended(1 if suspended else 0)
        if status:
            raise RuntimeError(f"native camera suspension refused ({status})")

    def stats(self) -> Stats:
        result = Stats()
        if self.library.view_stats(ctypes.byref(result)):
            raise RuntimeError("native camera stats unavailable")
        return result
