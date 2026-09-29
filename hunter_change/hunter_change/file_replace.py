"""A file written whole: the one place that does it, for every file the mod writes.

The bytes go to a temporary file next to the target, are forced onto the disk, then the temporary file is renamed over
the target, so the disk holds the old file whole or the new one whole. Forced first, since Windows' disk journal
records the rename and not the bytes: after a power cut, a file renamed too early can read back as zeros. The
temporary file is named here and nowhere else: a name chosen by the caller could be the target itself or a backup,
which a failure would then empty or delete.
"""

import contextlib
import os
from pathlib import Path

TEMPORARY_SUFFIX = ".tmp"


def replace(target: Path, data: bytes) -> None:
    """Raises OSError when the target is not replaced, and removes the temporary file it leaves, when it can."""
    temporary = target.with_name(target.name + TEMPORARY_SUFFIX)
    try:
        with open(temporary, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, target)
    except OSError:
        with contextlib.suppress(OSError):
            temporary.unlink(missing_ok=True)
        raise
