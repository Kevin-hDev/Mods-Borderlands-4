"""Tests the memory calls for real, on this process: a read, a write, and a bad address failing instead of crashing."""

import ctypes
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


sdk_stubs.install()

from omni_sprint import memory  # noqa: E402

block = ctypes.create_string_buffer(struct.pack("<ff", 60.0, 0.6))
address = ctypes.addressof(block)
check("bytes are read", memory.read(address, 8) == struct.pack("<ff", 60.0, 0.6))
check("a float is read", memory.read_float(address) == 60.0)
check("a float is written", memory.write_float(address, 180.0) and struct.unpack("<f", block.raw[:4])[0] == 180.0)
check("the value next to it is untouched", abs(struct.unpack("<f", block.raw[4:8])[0] - 0.6) < 1e-6)
check("a bad address reads nothing instead of crashing", memory.read(0x10, 4) is None and memory.read_float(0x10) is None)
check("a bad address refuses the write instead of crashing", memory.write_float(0x10, 1.0) is False)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
