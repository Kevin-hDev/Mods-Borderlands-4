"""Tests the limit: opened at 180 with its first value kept, opened again, put back only where still recognised."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sprint_memory_fixtures as fixtures  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


fixtures.install_types({})

from apex_camera_runtime import movement_definition as definition  # noqa: E402
from apex_camera_runtime import sprint_limit as limit  # noqa: E402

fake = fixtures.FakeMemory()
fixtures.patch(fake)
limits = limit.Limits()
shape = definition.layout()
SIREN = fixtures.BASE + 0x20000
EXO = fixtures.BASE + 0x21000
fake.put_definition(SIREN, definition.KNOWN)
fake.put_definition(EXO, definition.KNOWN)


def angle(address: int) -> float:
    return fake.get_float(address + 580)


line = limits.hold(SIREN, shape)
check("the limit is opened to 180", angle(SIREN) == 180.0)
check("the opening is logged with the game's value", line is not None and "game limit 60" in line)
writes = fake.writes
check("an open limit is left as it is", limits.hold(SIREN, shape) is None and fake.writes == writes)

fake.put_float(SIREN + 580, 60.0)
line = limits.hold(SIREN, shape)
check("a limit the game put back is opened again, and it says so", angle(SIREN) == 180.0 and "opened again" in line)

fake.put_float(EXO + 580, 180.0)
check("a limit already at 180 is not written", limits.hold(EXO, shape) is None)

check("putting back restores both definitions", limits.put_back(shape) == (2, 0))
check("the first value found is put back", angle(SIREN) == 60.0)
check("a limit found at 180 gets the game files' 60", angle(EXO) == 60.0)
check("putting back twice does nothing", limits.put_back(shape) == (0, 0))

limits.hold(SIREN, shape)
limits.hold(EXO, shape)
fake.put_float(EXO + fixtures.OFFSETS["LadderFriction"], 3.0)
check("a definition no longer recognised is left alone", limits.put_back(shape) == (1, 1) and angle(EXO) == 180.0)
fake.put_float(EXO + fixtures.OFFSETS["LadderFriction"], 8.0)
fake.put_float(EXO + 580, 60.0)

limits.hold(SIREN, shape)
fake.put_float(SIREN + 580, 90.0)
check("a limit another hand changed is left alone", limits.put_back(shape) == (0, 1) and angle(SIREN) == 90.0)
fake.put_float(SIREN + 580, 60.0)

limits.hold(SIREN, shape)
check("without a layout nothing is written back", limits.put_back(None) == (0, 1) and angle(SIREN) == 180.0)
fake.put_float(SIREN + 580, 60.0)

fake.put_float(SIREN + fixtures.OFFSETS["MaxLadderAscendSpeed"], 1.0)
try:
    limits.hold(SIREN, shape)
    check("a definition no longer recognised is lost, not written", False)
except limit.Lost:
    check("a definition no longer recognised is lost, not written", angle(SIREN) == 60.0)
fake.put_float(SIREN + fixtures.OFFSETS["MaxLadderAscendSpeed"], 300.0)

fake.refuse_writes = True
try:
    limits.hold(SIREN, shape)
    check("a refused write is reported", False)
except limit.NotOpened as exc:
    check("a refused write is reported", "write refused" in str(exc))
fake.refuse_writes = False
limits.put_back(shape)

limits.hold(SIREN, shape)
check("lowered for a dash, the game's value comes back", limits.lower(SIREN, shape) and angle(SIREN) == 60.0)
check("lowered twice, the second does nothing", not limits.lower(SIREN, shape) and angle(SIREN) == 60.0)
check("reopened, 180 again", limits.reopen(SIREN, shape) and angle(SIREN) == 180.0)
check("reopened twice, the second does nothing", not limits.reopen(SIREN, shape))
check("a definition never opened is never lowered", not limits.lower(EXO, shape) and angle(EXO) == 60.0)
fake.put_float(SIREN + fixtures.OFFSETS["LadderFriction"], 3.0)
check("a definition no longer recognised is not lowered", not limits.lower(SIREN, shape) and angle(SIREN) == 180.0)
fake.put_float(SIREN + fixtures.OFFSETS["LadderFriction"], 8.0)
fake.put_float(SIREN + 580, 90.0)
check("a limit another hand changed is neither lowered nor reopened",
      not limits.lower(SIREN, shape) and not limits.reopen(SIREN, shape) and angle(SIREN) == 90.0)
fake.put_float(SIREN + 580, 180.0)
limits.lower(SIREN, shape)
writes = fake.writes
check("putting back while lowered counts it put back, nothing more written",
      limits.put_back(shape) == (1, 0) and angle(SIREN) == 60.0 and fake.writes == writes)

limit.MAX_OPENED = 1
limits.hold(SIREN, shape)
try:
    limits.hold(EXO, shape)
    check("past the bound, a new definition is not opened", False)
except limit.NotOpened:
    check("past the bound, a new definition is not opened", angle(EXO) == 60.0)
limits.put_back(shape)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
