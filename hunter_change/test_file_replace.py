"""A file written whole: the target replaced by the bytes, created when absent, the temporary file gone; the bytes
forced onto the disk, whole, before the rename; a failed rename, forcing or write raised, the target unchanged and the
temporary file removed."""

import os
import sys
import tempfile
from pathlib import Path

import sdk_stubs

sdk_stubs.install()

from hunter_change import file_replace  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def raises(action) -> bool:
    try:
        action()
    except OSError:
        return True
    return False


def refused(*_args) -> None:
    raise PermissionError("held")


folder = Path(tempfile.mkdtemp())
target = folder / "file.json"
temporary = target.with_name(target.name + file_replace.TEMPORARY_SUFFIX)

file_replace.replace(target, b"first")
check("created when absent, the temporary file gone", target.read_bytes() == b"first" and not temporary.exists())
file_replace.replace(target, b"second")
check("the target replaced by the bytes", target.read_bytes() == b"second" and not temporary.exists())

steps: list[str] = []
sizes: list[int] = []
real_fsync, real_replace = os.fsync, os.replace


def forced(number: int) -> None:
    steps.append("fsync")
    sizes.append(os.fstat(number).st_size)
    real_fsync(number)


def renamed(source, destination) -> None:
    steps.append("replace")
    real_replace(source, destination)


os.fsync, os.replace = forced, renamed
file_replace.replace(target, b"third")
os.fsync, os.replace = real_fsync, real_replace
check("the bytes forced onto the disk, whole, before the rename",
      steps == ["fsync", "replace"] and sizes == [len(b"third")] and target.read_bytes() == b"third")

os.replace = refused
failed = raises(lambda: file_replace.replace(target, b"fourth"))
os.replace = real_replace
check("a failed rename raised, the target unchanged and the temporary file removed",
      failed and target.read_bytes() == b"third" and not temporary.exists())

os.fsync = refused
failed = raises(lambda: file_replace.replace(target, b"fifth"))
os.fsync = real_fsync
check("a failed forcing raised, the target unchanged and the temporary file removed",
      failed and target.read_bytes() == b"third" and not temporary.exists())

# A folder of its own: a temporary file that another case failed to remove must not stop this one.
blocked = folder / "blocked" / "file.json"
blocked.parent.mkdir()
blocked.write_bytes(b"kept")
blocked.with_name(blocked.name + file_replace.TEMPORARY_SUFFIX).mkdir()
check("a failed write raised, the target unchanged",
      raises(lambda: file_replace.replace(blocked, b"sixth")) and blocked.read_bytes() == b"kept")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
