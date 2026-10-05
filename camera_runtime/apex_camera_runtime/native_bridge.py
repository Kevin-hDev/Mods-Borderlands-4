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

from .constants import THIRD_PERSON_UP
from .generated_limits import SHOULDER_MAX_OFFSET
from .generated_ads import VIEW_ABI, VIEW_UPDATE_SLOT as UPDATE_SLOT, VIEW_UPDATE_RVA, ViewConfig as Config, ViewStats as Stats

ABI_VERSION = VIEW_ABI
EXPECTED_UPDATE_RVA = VIEW_UPDATE_RVA
MAX_LIBRARY_BYTES = 2_000_000
_FILE_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,80}\.dll$")
MAX_RIGHT = SHOULDER_MAX_OFFSET
LIBRARY_NAME = f"apex_camera_view_v{VIEW_ABI}.dll"
HASH_NAME = f"apex_camera_view_v{VIEW_ABI}.sha256"


def make_config(right: float) -> Config:
    if (isinstance(right, bool) or not isinstance(right, (int, float))
            or not math.isfinite(right) or abs(right) > MAX_RIGHT):
        raise ValueError("invalid shoulder offset")
    return Config(ABI_VERSION, 0, UPDATE_SLOT, 0, EXPECTED_UPDATE_RVA,
                  float(right), THIRD_PERSON_UP)


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
        library.view_start.argtypes = [ctypes.c_void_p, ctypes.POINTER(Config)]
        library.view_start.restype = ctypes.c_int
        library.view_stop.argtypes, library.view_stop.restype = [], ctypes.c_int
        library.view_set_suspended.argtypes = [ctypes.c_uint32]
        library.view_set_suspended.restype = ctypes.c_int
        library.view_set_right.argtypes = [ctypes.c_double]
        library.view_set_right.restype = ctypes.c_bool
        library.view_stats.argtypes = [ctypes.POINTER(Stats)]
        library.view_stats.restype = ctypes.c_int

    def start(self, manager: Any, right: float) -> bool:
        try:
            address = int(manager._get_address())
            config = make_config(right)
        except (AttributeError, TypeError, ValueError, OverflowError):
            return False
        if address <= 0:
            return False
        status = self.library.view_start(address, ctypes.byref(config))
        if status:
            raise RuntimeError(f"native camera start refused ({status})")
        return True

    def set_right(self, right: float) -> bool:
        if (isinstance(right, bool) or not isinstance(right, (int, float))
                or not math.isfinite(right) or abs(right) > MAX_RIGHT):
            return False
        return bool(self.library.view_set_right(float(right)))

    def stop(self) -> None:
        status = self.library.view_stop()
        if status:
            raise RuntimeError(f"native camera stop refused ({status})")

    def suspend(self, suspended: bool) -> None:
        status = self.library.view_set_suspended(1 if suspended else 0)
        if status:
            raise RuntimeError(f"native camera suspension refused ({status})")

    def stats(self) -> Stats:
        result = Stats()
        if self.library.view_stats(ctypes.byref(result)):
            raise RuntimeError("native camera stats unavailable")
        return result
