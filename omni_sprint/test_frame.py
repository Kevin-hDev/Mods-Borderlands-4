"""Tests the clock: a check twice a second, a new character searched, the limit kept open, failures once, stop."""

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


state = sdk_stubs.install()

from omni_sprint import animation, camera, definition, frame, limit, memory, report  # noqa: E402

fake = sdk_stubs.FakeMemory()
sdk_stubs.patch_memory(memory, fake)
BASE = sdk_stubs.BASE
COMPONENT, OTHER_COMPONENT, EMPTY_COMPONENT = BASE + 0x1000, BASE + 0x6000, BASE + 0xB000
SIREN, EXO = BASE + 0x20000, BASE + 0x21000
fake.put_definition(SIREN, definition.KNOWN)
fake.put_definition(EXO, definition.KNOWN)
fake.put_pointer(COMPONENT + 0x1CF0, SIREN)
fake.put_pointer(OTHER_COMPONENT + 0x1CF0, EXO)
MS = 1_000_000
now = 1_000 * MS


def angle(address: int) -> float:
    return fake.get_float(address + 580)


def step(ms: int = 500) -> None:
    global now
    now += ms * MS
    frame.on_frame(now)


frame.reset()
step()
check("without a player nothing happens", state["misc"] == [] and fake.writes == 0)

state["pc"] = sdk_stubs.player(COMPONENT)
step()
check("the character's definition is opened at the first check", angle(SIREN) == 180.0)
check("where it was found is logged", any("found at" in line and "+0x1cf0" in line for line in state["misc"]))
check("the type is read once", state["type_finds"] == 1)
fake.put_float(SIREN + 580, 60.0)
step(100)
check("a tick before the next check does nothing", angle(SIREN) == 60.0)
step(400)
check("a limit the game put back is opened again at the next check", angle(SIREN) == 180.0)
check("the type is still read once", state["type_finds"] == 1)

state["pc"] = sdk_stubs.player(OTHER_COMPONENT)
step()
check("a new character's definition is opened too", angle(EXO) == 180.0)

LATE_COMPONENT = BASE + 0x10000
state["pc"] = sdk_stubs.player(LATE_COMPONENT)
step()
check("a character whose definition is not ready yet gets no warning at once",
      not any("no movement definition" in line for line in state["warnings"]))
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
state["pc"] = sdk_stubs.player(EMPTY_COMPONENT)
for _ in range(3000):
    step(100)
gaps = [(later - earlier) // MS for earlier, later in zip(searches, searches[1:])]
check("searches wait longer and longer between tries", gaps[:5] == [500, 1000, 2000, 4000, 8000])
check("the wait stops growing at its ceiling", max(gaps) == frame.RETRY_MAX_NS // MS)
check("the search stops after its last try", len(searches) == frame.MAX_TRIES)
check("a character without a definition is given up on and reported once",
      len([line for line in state["warnings"] if "no movement definition" in line]) == 1)
definition.find = real_find

state["pc"] = sdk_stubs.player(COMPONENT)
step()
fake.put_float(SIREN + sdk_stubs.OFFSETS["LadderFriction"], 2.0)
writes = fake.writes
step()
check("a definition no longer recognised is not written", fake.writes == writes)
check("and it is looked for again", any("looking for it again" in line for line in state["misc"]))
fake.put_float(SIREN + sdk_stubs.OFFSETS["LadderFriction"], 8.0)
step()
check("found again, it stays open", angle(SIREN) == 180.0)

check("stopping puts both definitions back", frame.stop() == (2, 0) and angle(SIREN) == 60.0 and angle(EXO) == 60.0)

frame.reset()
fake.refuse_writes = True
step()
step()
check("a refused write is reported once", len([line for line in state["errors"] if "write refused" in line]) == 1)
fake.refuse_writes = False
frame.stop()

frame.reset()
state["types"] = []
state["type_finds"] = 0
step()
step()
check("a changed type is reported once and nothing is written",
      len([line for line in state["errors"] if "type has changed" in line]) == 1 and angle(SIREN) == 60.0)
check("and it is not looked up again at each check", state["type_finds"] == 1)
state["types"] = [sdk_stubs.movement_type()]
frame.stop()

report.reset()
frame.reset()
state["pc"] = object()
frame.tick(object(), None, None, None)
check("a player without a character does nothing", state["errors"] == [] or all("skipped" not in e for e in state["errors"]))

seen_animation = []
original_animation_inspect = animation.inspect
original_animation_update = animation.update
animation.inspect = lambda obj: (False, object(), obj)
animation.update = lambda current, _now: seen_animation.append(current[2])
frame.tick(object(), None, None, None)
check("the clock also forwards body callbacks to the animation owner", len(seen_animation) == 1)
animation.inspect = original_animation_inspect
animation.update = original_animation_update

player_body, camera_frames = object(), []
original_camera = camera.on_frame
animation.inspect = lambda obj: (obj is player_body, object(), obj)
animation.update = lambda _current, _now: None
camera.on_frame = lambda now: camera_frames.append(now)
frame.tick(object(), None, None, None)
frame.tick(player_body, None, None, None)
frame.tick(None, None, None, None)
frame.tick(None, None, None, None)
check("enemy animation callbacks do not update the camera",
      len(camera_frames) == 2)
camera.on_frame = original_camera
animation.inspect = original_animation_inspect
animation.update = original_animation_update

continued = []
original_frame_check = frame.on_frame
animation.inspect = lambda _obj: (True, object(), object())
animation.update = lambda _frame, _now: (_ for _ in ()).throw(RuntimeError('bad animation'))
frame.on_frame = lambda now: continued.append(now)
camera_frames.clear()
camera.on_frame = lambda value: camera_frames.append(value)
frame.tick(object(), None, None, None)
check("an animation error does not interrupt the sprint limit or freeze the camera",
      len(continued) == 1 and len(camera_frames) == 1)
animation.inspect = original_animation_inspect
animation.update = original_animation_update
camera.on_frame = original_camera
frame.on_frame = original_frame_check

original_camera = camera.on_frame
camera.on_frame = lambda now: (_ for _ in ()).throw(RuntimeError("bad camera"))
continued.clear()
frame.on_frame = lambda now: continued.append(now)
animation.inspect = lambda obj: (True, object(), obj)
animation.update = lambda _current, _now: None
frame.tick(object(), None, None, None)
frame.tick(object(), None, None, None)
check("a camera error does not interrupt the sprint limit, and is written once",
      len(continued) == 2 and len([line for line in state["errors"] if "camera check was skipped" in line]) == 1)
camera.on_frame = original_camera
animation.inspect = original_animation_inspect
animation.update = original_animation_update
frame.on_frame = original_frame_check


class Broken:
    @property
    def OakCharacter(self) -> object:
        raise RuntimeError("controller gone")


state["pc"] = Broken()
frame.reset()
frame.tick(object(), None, None, None)
frame.reset()
frame.tick(object(), None, None, None)
check("an error in a check is written once and the game goes on",
      len([line for line in state["errors"] if "] a check was skipped" in line]) == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
