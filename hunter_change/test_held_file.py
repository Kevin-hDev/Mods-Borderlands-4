"""A file held an instant: free at once, one try and no pause; held twice then free, its result after the two pauses;
held three times, the last error raised after the two pauses; any other error raised at once, never tried again."""

import sys

import sdk_stubs

sdk_stubs.install()

from hunter_change import held_file  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def held(times: int, error: type[Exception] = PermissionError):
    """An action that fails `times` times with its own error, then gives "read"; its tries counted."""
    tries: list[int] = []

    def action() -> str:
        tries.append(len(tries) + 1)
        if len(tries) <= times:
            raise error(f"held, try {len(tries)}")
        return "read"

    return action, tries


pauses: list[float] = []
action, tries = held(0)
check("free at once: one try, no pause",
      held_file.patiently(action, sleep=pauses.append) == "read" and tries == [1] and pauses == [])

action, tries = held(2)
check("held twice then free: its result after the two pauses",
      held_file.patiently(action, sleep=pauses.append) == "read" and tries == [1, 2, 3] and pauses == [0.1, 0.2])

pauses.clear()
action, tries = held(3)
try:
    held_file.patiently(action, sleep=pauses.append)
    raised = None
except OSError as error:
    raised = error
check("held three times: the last error raised after the two pauses",
      isinstance(raised, PermissionError) and str(raised) == "held, try 3" and tries == [1, 2, 3]
      and pauses == [0.1, 0.2])

pauses.clear()
action, tries = held(1, ValueError)
try:
    held_file.patiently(action, sleep=pauses.append)
    raised = None
except ValueError as error:
    raised = error
check("any other error raised at once, never tried again", raised is not None and tries == [1] and pauses == [])
check("three tries at most, 0.1 then 0.2 s apart", held_file.PAUSES_S == (0.1, 0.2))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
