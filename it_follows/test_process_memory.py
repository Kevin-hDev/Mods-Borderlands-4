"""Tests the game's own memory read and written by the system (it_follows/process_memory.py), on this process: a
buffer read back as it is, written then read, a write of its whole size; an address that is not mapped read as None
and written as False, without a crash; sizes out of bounds and the address 0 refused; the image's start found."""

import ctypes
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import process_memory  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    memory = process_memory.ProcessMemory()
    check("the image's start found", memory.base > 0)
    buffer = ctypes.create_string_buffer(b"0123456789abcdef", 16)
    address = ctypes.addressof(buffer)
    check("a buffer read back as it is", memory.read(address, 16) == b"0123456789abcdef")
    check("written then read", memory.write(address + 4, b"WXYZ") and buffer.raw[:16] == b"0123WXYZ89abcdef")
    check("an address not mapped read as None and written as False",
          memory.read(8, 8) is None and memory.write(8, b"\x00") is False)
    check("the address 0 and sizes out of bounds refused", memory.read(0, 8) is None and memory.read(address, 0) is None
          and memory.read(address, process_memory.MAX_BYTES + 1) is None and memory.write(address, b"") is False)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
