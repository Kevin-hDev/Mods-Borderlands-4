"""Python ABI and safe extraction for the production native camera bridge."""

import ctypes
import hashlib
import pathlib
import sys
import tempfile
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import native_bridge as bridge  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Function:
    def __init__(self, result=0):
        self.result = result
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return self.result


config = bridge.make_config()
check("the production ABI has no probe deadline",
      (config.abi, config.duration_ms, config.slot_index, config.expected_rva)
      == (4, 0, 264, 0x3CD4832))
check("the validated framing is the single configured value", (config.right, config.up) == (48.4, 5.0))
check("the ABI layouts are fixed", ctypes.sizeof(config) == 40 and ctypes.sizeof(bridge.Stats) == 96)

start, stop, suspend, stats = Function(), Function(), Function(), Function()
library = types.SimpleNamespace(view_start=start, view_stop=stop,
                                view_set_suspended=suspend, view_stats=stats)
api = bridge.Bridge(library)
manager = types.SimpleNamespace(_get_address=lambda: 0x12345678)
api.start(manager)
api.suspend(True)
api.stop()
check("the wrapper passes the exact manager and suspension state",
      start.calls[0][0] == 0x12345678 and suspend.calls[0][0] == 1 and len(stop.calls) == 1)

payload = b"MZ" + bytes(range(64))
digest = hashlib.sha256(payload).hexdigest()
temporary = tempfile.TemporaryDirectory(prefix="camera_bridge_")
target = pathlib.Path(temporary.name)
path = bridge.install_library(payload, target, "camera_v4.dll", digest)
check("a verified PE payload is written", path.read_bytes() == payload)
same = bridge.install_library(payload, target, "camera_v4.dll", digest)
check("an identical installed library is reused", same == path and same.read_bytes() == payload)
for label, bad_payload, bad_hash in (
    ("a non-PE payload is refused", b"not a dll", hashlib.sha256(b"not a dll").hexdigest()),
    ("a hash mismatch is refused", payload, "0" * 64),
    ("an oversized payload is refused", b"MZ" + b"x" * (2_000_000 + 1), "0" * 64),
):
    try:
        bridge.install_library(bad_payload, target, "bad.dll", bad_hash)
        check(label, False)
    except ValueError:
        check(label, not (target / "bad.dll").exists())

loaded = []


def packaged(name):
    return payload if name.endswith(".dll") else digest.encode("ascii")


library = object()
found = bridge.load_packaged_library(target, packaged, lambda path: loaded.append(path) or library)
check("the packaged asset is verified before loading", found is library and loaded[0].read_bytes() == payload)

package_reads = []
original_get_data, original_package = bridge.pkgutil.get_data, bridge.__package__
bridge.__package__ = "apex_movement.apex_camera_runtime"
bridge.pkgutil.get_data = lambda package, name: package_reads.append(package) or packaged(name)
try:
    nested_temporary = tempfile.TemporaryDirectory(prefix="nested_camera_bridge_")
    nested_target = pathlib.Path(nested_temporary.name)
    bridge.load_packaged_library(nested_target, loader=lambda _path: library)
finally:
    bridge.pkgutil.get_data, bridge.__package__ = original_get_data, original_package
check("the asset is read from the runtime's actual packaged location",
      package_reads == ["apex_movement.apex_camera_runtime"] * 2)
nested_temporary.cleanup()
temporary.cleanup()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
