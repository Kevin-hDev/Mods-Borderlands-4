"""A file Windows or OneDrive holds an instant: the one place that waits for it.

OneDrive, the antivirus or the game itself can keep a save open for a moment, and reading or writing it then fails
with an OSError that says nothing about the file itself. Such a failure is tried again a few times, briefly, since the
game waits meanwhile; any other error is the file's own answer and is raised at once.
"""

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

# Three tries, 0.1 then 0.2 s apart: at most 0.3 s of freeze. Kevin accepts that short freeze, 2026-09-28: "a short
# freeze is normal, a long one or a crash risk is not".
PAUSES_S = (0.1, 0.2)


def patiently(action: Callable[[], T], sleep: Callable[[float], object] = time.sleep) -> T:
    """What action() returns, tried again after each pause while it raises OSError; the last OSError raised."""
    for pause in PAUSES_S:
        try:
            return action()
        except OSError:
            sleep(pause)
    return action()
