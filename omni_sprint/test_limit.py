"""Tests the limit: opened at 180 with its first value kept, opened again, put back only where still recognised."""

import pathlib
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

from omni_sprint import definition, limit, memory  # noqa: E402

fake = sdk_stubs.FakeMemory()
sdk_stubs.patch_memory(memory, fake)
shape = definition.layout()
SIREN = sdk_stubs.BASE + 0x20000
EXO = sdk_stubs.BASE + 0x21000
fake.put_definition(SIREN, definition.KNOWN)
fake.put_definition(EXO, definition.KNOWN)


def angle(address: int) -> float:
    return fake.get_float(address + 580)


line = limit.hold(SIREN, shape)
check("the limit is opened to 180", angle(SIREN) == 180.0)
check("the opening is logged with the game's value", line is not None and "game limit 60" in line)
writes = fake.writes
check("an open limit is left as it is", limit.hold(SIREN, shape) is None and fake.writes == writes)

fake.put_float(SIREN + 580, 60.0)
line = limit.hold(SIREN, shape)
check("a limit the game put back is opened again, and it says so", angle(SIREN) == 180.0 and "opened again" in line)

fake.put_float(EXO + 580, 180.0)
check("a limit already at 180 is not written", limit.hold(EXO, shape) is None)

check("putting back restores both definitions", limit.put_back(shape) == (2, 0))
check("the first value found is put back", angle(SIREN) == 60.0)
check("a limit found at 180 gets the game files' 60", angle(EXO) == 60.0)
check("putting back twice does nothing", limit.put_back(shape) == (0, 0))

limit.hold(SIREN, shape)
limit.hold(EXO, shape)
fake.put_float(EXO + sdk_stubs.OFFSETS["LadderFriction"], 3.0)
check("a definition no longer recognised is left alone", limit.put_back(shape) == (1, 1) and angle(EXO) == 180.0)
fake.put_float(EXO + sdk_stubs.OFFSETS["LadderFriction"], 8.0)
fake.put_float(EXO + 580, 60.0)

limit.hold(SIREN, shape)
fake.put_float(SIREN + 580, 90.0)
check("a limit another hand changed is left alone", limit.put_back(shape) == (0, 1) and angle(SIREN) == 90.0)
fake.put_float(SIREN + 580, 60.0)

limit.hold(SIREN, shape)
check("without a layout nothing is written back", limit.put_back(None) == (0, 1) and angle(SIREN) == 180.0)
fake.put_float(SIREN + 580, 60.0)

fake.put_float(SIREN + sdk_stubs.OFFSETS["MaxLadderAscendSpeed"], 1.0)
try:
    limit.hold(SIREN, shape)
    check("a definition no longer recognised is lost, not written", False)
except limit.Lost:
    check("a definition no longer recognised is lost, not written", angle(SIREN) == 60.0)
fake.put_float(SIREN + sdk_stubs.OFFSETS["MaxLadderAscendSpeed"], 300.0)

fake.refuse_writes = True
try:
    limit.hold(SIREN, shape)
    check("a refused write is reported", False)
except limit.NotOpened as exc:
    check("a refused write is reported", "write refused" in str(exc))
fake.refuse_writes = False
limit.put_back(shape)

limit.MAX_OPENED = 1
limit.hold(SIREN, shape)
try:
    limit.hold(EXO, shape)
    check("past the bound, a new definition is not opened", False)
except limit.NotOpened:
    check("past the bound, a new definition is not opened", angle(EXO) == 60.0)
limit.put_back(shape)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
