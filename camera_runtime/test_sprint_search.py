"""Tests the sprint keeper: a check twice a second, a new character searched, the limit kept open while asked and put
back when no longer asked, failures said once, stop. Moved from Omni Sprint's test_frame.py on 2026-10-09."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sprint_memory_fixtures as fixtures  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state: dict = {}
fixtures.install_types(state)

from apex_camera_runtime import movement_definition as definition  # noqa: E402
from apex_camera_runtime import sprint_search  # noqa: E402

fake = fixtures.FakeMemory()
fixtures.patch(fake)
BASE = fixtures.BASE
COMPONENT, OTHER_COMPONENT, EMPTY_COMPONENT = BASE + 0x1000, BASE + 0x6000, BASE + 0xB000
SIREN, EXO = BASE + 0x20000, BASE + 0x21000
fake.put_definition(SIREN, definition.KNOWN)
fake.put_definition(EXO, definition.KNOWN)
fake.put_pointer(COMPONENT + 0x1CF0, SIREN)
fake.put_pointer(OTHER_COMPONENT + 0x1CF0, EXO)
MS = 1_000_000
now = 1_000 * MS
lines: list[str] = []
keeper = sprint_search.SprintKeeper(lines.append)
pc = None
wanted = True


def player(component: int) -> object:
    movement = types.SimpleNamespace(_get_address=lambda: component)
    return types.SimpleNamespace(OakCharacter=types.SimpleNamespace(CharacterMovement=movement))


def angle(address: int) -> float:
    return fake.get_float(address + 580)


def step(ms: int = 500) -> None:
    global now
    now += ms * MS
    keeper.update(pc, wanted, now)


step()
check("without a player nothing happens", lines == [] and fake.writes == 0)

pc = player(COMPONENT)
step()
check("the character's definition is opened at the first check", angle(SIREN) == 180.0)
check("where it was found is logged", any("found at" in line and "+0x1cf0" in line for line in lines))
check("the type is read once", state["type_finds"] == 1)
fake.put_float(SIREN + 580, 60.0)
step(100)
check("a call before the next check does nothing", angle(SIREN) == 60.0)
step(400)
check("a limit the game put back is opened again at the next check", angle(SIREN) == 180.0)

wanted = False
step()
check("no longer asked, the limit is put back and it says so",
      angle(SIREN) == 60.0 and "game sprint limit put back in 1 movement definition(s)" in lines[-1])
wanted = True
step()
check("asked again, it opens again", angle(SIREN) == 180.0)

pc = player(OTHER_COMPONENT)
step()
check("a new character's definition is opened too", angle(EXO) == 180.0)

LATE_COMPONENT = BASE + 0x10000
pc = player(LATE_COMPONENT)
step()
check("a character whose definition is not ready yet gets no line at once",
      not any("no movement definition" in line for line in lines))
fake.put_pointer(LATE_COMPONENT + 0x1CF0, SIREN)
fake.put_float(SIREN + 580, 60.0)
step()
check("the same character is searched again, and opened once its definition is ready (2026-09-19, 13:39)",
      angle(SIREN) == 180.0)

searches: list[int] = []
real_find = definition.find


def counted_find(component: int, shape: object) -> object:
    searches.append(now)
    return real_find(component, shape)


definition.find = counted_find
pc = player(EMPTY_COMPONENT)
for _ in range(3000):
    step(100)
gaps = [(later - earlier) // MS for earlier, later in zip(searches, searches[1:])]
check("searches wait longer and longer between tries", gaps[:5] == [500, 1000, 2000, 4000, 8000])
check("the wait stops growing at its ceiling", max(gaps) == sprint_search.RETRY_MAX_NS // MS)
check("the search stops after its last try", len(searches) == sprint_search.MAX_TRIES)
check("a character without a definition is given up on and said once",
      len([line for line in lines if "no movement definition" in line]) == 1)
definition.find = real_find

pc = player(COMPONENT)
step()
fake.put_float(SIREN + fixtures.OFFSETS["LadderFriction"], 2.0)
writes = fake.writes
step()
check("a definition no longer recognised is not written", fake.writes == writes)
check("and it is looked for again", any("looking for it again" in line for line in lines))
fake.put_float(SIREN + fixtures.OFFSETS["LadderFriction"], 8.0)
step()
check("found again, it stays open", angle(SIREN) == 180.0)

said = len(lines)
check("lowered for a dash: the game's limit back, nothing said", keeper.lower(now, 700 * MS)
      and angle(SIREN) == 60.0 and len(lines) == said)
check("lowered again before it reopens: refused", not keeper.lower(now, 700 * MS))
step()
check("the next check leaves it lowered, nothing said", angle(SIREN) == 60.0 and len(lines) == said)
keeper.reopen_if_due(now)
check("not due yet, it stays lowered", angle(SIREN) == 60.0)
now += 200 * MS
keeper.reopen_if_due(now)
check("due, it opens at once, nothing said", angle(SIREN) == 180.0 and len(lines) == said
      and keeper.lowered_until == 0)
keeper.reopen_if_due(now)
check("reopened, the next frames write nothing", angle(SIREN) == 180.0)
keeper.lower(now, 700 * MS)
wanted = False
step()
check("no longer asked while lowered: counted put back, the game's value kept",
      angle(SIREN) == 60.0 and angle(EXO) == 60.0 and keeper.lowered_until == 0
      and "put back in 2 movement definition(s)" in lines[-1])
wanted = True
step()
check("asked again after, it opens again", angle(SIREN) == 180.0)
pc = player(OTHER_COMPONENT)
step()
pc = player(COMPONENT)
step()
check("a keeper without a definition never lowers", not sprint_search.SprintKeeper(lines.append).lower(now, 1))

check("stopping puts both definitions back", keeper.stop() == (2, 0) and angle(SIREN) == 60.0 and angle(EXO) == 60.0)
check("stopping with nothing opened does nothing", keeper.stop() == (0, 0))

fake.refuse_writes = True
step()
step()
check("a refused write is said once", len([line for line in lines if "write refused" in line]) == 1)
fake.refuse_writes = False
keeper.stop()

state["types"] = []
state["type_finds"] = 0
step()
step()
check("a changed type is said once and nothing is written",
      len([line for line in lines if "type has changed" in line]) == 1 and angle(SIREN) == 60.0)
check("and it is not looked up again at each check", state["type_finds"] == 1)
state["types"] = [fixtures.movement_type()]
keeper.stop()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
