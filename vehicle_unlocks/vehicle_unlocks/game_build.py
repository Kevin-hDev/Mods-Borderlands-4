"""Which supported game build runs this process, chosen once from the main module's own header.

Twin of vehicle_unlocks/game_build.py: that shared package also ships in Vehicle Driving, which cannot import Save
Editor. test_game_build.py keeps the two files identical.
"""
import ctypes
import struct

STEAM_4845623 = "steam_4845623"
STEAM_4906557 = "steam_4906557"
# SizeOfImage of each supported Borderlands4.exe. The Steam update of 2026-10-22 gave 4906557; 4845623 stays for the
# players who went back to it (same decision as Third Person & FOV that day, Kevin's procedure on Nexus).
IMAGE_SIZES = {STEAM_4845623: 834191360, STEAM_4906557: 652288000}
NEWEST = STEAM_4906557
MAX_HEADER_OFFSET = 4096


def image_size(read, base):
    """SizeOfImage of the PE64 module at `base`; ValueError when the header is not one."""
    dos = read(base, 64)
    offset = struct.unpack_from("<I", dos, 0x3C)[0]
    if dos[:2] != b"MZ" or not 64 <= offset <= MAX_HEADER_OFFSET:
        raise ValueError("Invalid header")
    pe = read(base + offset, 128)
    if pe[:6] != b"PE\0\0\x64\x86" or struct.unpack_from("<H", pe, 24)[0] != 0x20B:
        raise ValueError("Unsupported image")
    return struct.unpack_from("<I", pe, 80)[0]


def _running_size():
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel.GetModuleHandleW.restype = wintypes.HMODULE
    base = kernel.GetModuleHandleW(None)
    if not base:
        raise OSError("Module unavailable")
    # The main module's header stays mapped for the whole life of the process.
    return image_size(ctypes.string_at, base)


def detect(size=None):
    """The build whose size matches, else the newest: every feature then checks that size and refuses."""
    if size is None:
        try:
            size = _running_size()
        except Exception:
            # Outside a readable game (tests): the newest contract, whose own size check refuses this process.
            return NEWEST
    return next((build for build, known in IMAGE_SIZES.items() if known == size), NEWEST)


CURRENT = detect()
IMAGE_SIZE = IMAGE_SIZES[CURRENT]
