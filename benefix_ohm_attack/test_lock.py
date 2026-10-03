"""Tests the lock: the beam takes the enemy it has touched long enough, stays on it while the aim strays, and lets
go when the aim strays too far, when the enemy dies or leaves, or when something stands in the way."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import aim, lock  # noqa: E402

fails: list[str] = []
EYE = (0.0, 0.0, 50.0)


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(found, wanted):
    return all(abs(a - b) < 1e-6 for a, b in zip(found, wanted))


def frame(passed: float = 0.05, delay: float = 0.2, angle: float = 30.0):
    """One frame of a shot: the aim of the moment, then what the lock makes of it."""
    return lock.follow(pc, character, aim.look(pc, character, 5000.0), passed, delay, angle)


def frames(seconds: float, **kwargs):
    found = None
    for _ in range(round(seconds / 0.05)):
        found = frame(**kwargs)
    return found


def lines(since: int) -> list[str]:
    return [line.removeprefix("[Benefix Ohm Attack] ") for line in state["log"][since:] if "lock" in line]


def scene(*things):
    """A new shot in a new world, the camera looking straight ahead."""
    lock.forget()
    state["look"] = (0.0, 0.0)
    sdk_stubs.world(state, *things)


pc, character = sdk_stubs.player(state)
psycho = sdk_stubs.Actor("Char_Psycho_4", (1000.0, 0.0, 50.0))
scene((psycho, 40.0))
check("with nothing aimed at there is no target", lock.follow(pc, character, aim.Aim(anchor=(5000.0, 0.0, 50.0)), 0.05, 0.2, 30.0) is None
      and not lock.held())
logged = len(state["log"])
first = frame()
check("an enemy just touched is the target, not locked yet: the beam ends where the aim meets him",
      first.enemy is psycho and near(first.point, (960.0, 0.0, 50.0)) and first.locked is False and not lock.held()
      and first.species == "Char_Psycho" and first.distance == 960.0)
check("he is not locked before the contact has lasted its time", frames(0.15).locked is False)
taken = frame()
check("he is once it has: two tenths of a second by default", taken.locked is True and lock.held() and taken.enemy is psycho)
check("the log says who was locked and how far, once", lines(logged) == ["lock on Char_Psycho at 10 m"])

state["look"] = (0.0, 10.0)
check("the aim strays: the thin ray no longer meets him", aim.look(pc, character, 5000.0).enemy is None)
kept = frame()
check("the lock holds: the target is still him, at the spot of his body the beam was on",
      kept is not None and kept.enemy is psycho and kept.locked and near(kept.point, (960.0, 0.0, 50.0)))
check("the target says how far the aim has strayed from him: ten degrees, none when he was taken",
      abs(kept.strayed - 10.0) < 1e-6 and taken.strayed == 0.0 and first.strayed == 0.0)
psycho.at = (1000.0, 300.0, 80.0)
moved = frame()
check("he moves: the spot moves with him", near(moved.point, (960.0, 300.0, 80.0)))
check("the target's distance is the camera's to that spot", abs(moved.distance - 1006.2) < 0.1)
check("what the ray to him met is kept for the hits: his own answer, of this frame",
      moved.hit is not None and aim.hit_actor(moved.hit) is psycho and moved.hit is not taken.hit)
psycho.at = (1000.0, 0.0, 50.0)

state["look"] = (0.0, 29.0)
check("29 degrees away the lock still holds", frame().locked)
state["look"] = (0.0, 31.0)
lost = frame()
check("31 degrees away it lets go: nothing is aimed at, there is no target", lost is None and not lock.held())
check("the log says why, once", lines(logged)[-1] == "lock lost: aim 31 degrees away" and len(lines(logged)) == 2)
state["look"] = (0.0, 0.0)
check("coming back on him is a new contact: not locked at once", frame().locked is False)
check("locked again after its time", frames(0.2).locked)
state["look"] = (0.0, 31.0)
frame()
check("each shot says its first lock and its first loss only", len(lines(logged)) == 2)

scene((psycho, 40.0))
frames(0.25)
state["look"] = (10.0, 10.0)
check("the angle is the whole one between the aim and him, up and down as well as sideways: 10 up and 10 aside "
      "is 14 degrees, under a limit of 15", frame(angle=15.0).locked)
state["look"] = (12.0, 12.0)
check("12 and 12 is 17, over it", frame(angle=15.0) is None)

scene((psycho, 40.0))
logged = len(state["log"])
frames(0.25)
check("a new shot says its own first lock", lines(logged) == ["lock on Char_Psycho at 10 m"])
psycho.HealthState.bCurrentlyDead = True
state["look"] = (0.0, 5.0)
check("the enemy dies: the lock lets go", frame() is None and lines(logged)[-1] == "lock lost: the enemy died")
state["look"] = (0.0, 0.0)
corpse = frames(0.5)
check("a dead one aimed at is met as before the lock, and never locked", corpse.enemy is psycho and not corpse.locked)
psycho.HealthState.bCurrentlyDead = False

scene((psycho, 40.0))
logged = len(state["log"])
frames(0.25)
state["gone"].add(id(psycho))
check("the enemy leaves the world: the lock lets go",
      frame() is None and lines(logged)[-1] == "lock lost: the enemy left the world")
state["gone"].discard(id(psycho))

wall = sdk_stubs.Actor("StaticMeshActor_1", (500.0, 400.0, 50.0))
scene((psycho, 40.0), (wall, 30.0))
logged = len(state["log"])
frames(0.25)
state["look"] = (0.0, 10.0)
check("a wall beside the way to him changes nothing", frame().locked)
wall.at = (500.0, 0.0, 50.0)
check("a wall on the way to him breaks the lock",
      frame() is None and lines(logged)[-1] == "lock lost: something stands in the way")
wall.at = (2000.0, 0.0, 50.0)
state["look"] = (0.0, 0.0)
frames(0.25)
state["look"] = (0.0, 10.0)
check("a wall behind him does not", frame().locked)
shield = sdk_stubs.Actor("ShieldBubble_1", (940.0, 0.0, 50.0))
scene((psycho, 40.0))
frames(0.25)
sdk_stubs.world(state, (psycho, 40.0), (shield, 10.0))
state["look"] = (0.0, 10.0)
check("nor does a thing met a hand's width before the spot: it is on him", frame().locked)

familiar = sdk_stubs.Actor("Char_DarkSiren_PhaseFamiliar_2", (1000.0, 0.0, 50.0))
state["attitudes"][id(familiar)] = sdk_stubs.ETeamAttitude.friendly
scene((familiar, 40.0))
asked = len(state["attitude_calls"])
friend = frames(0.5)
check("a friend is never locked: the beam ends on it as before", friend.enemy is familiar and not friend.locked
      and not lock.held())
check("the game is asked once per contact, not at every frame", len(state["attitude_calls"]) == asked + 1)

brute = sdk_stubs.Actor("Char_Brute_9", (1000.0, 500.0, 50.0))
scene((psycho, 40.0), (brute, 40.0))
frames(0.25)
state["look"] = (0.0, 26.565)
check("locked on one, the aim comes on another: the first stays the target for the time of a contact",
      frame().enemy is psycho and frames(0.1).enemy is psycho)
state["look"] = (0.0, 10.0)
frame()
state["look"] = (0.0, 26.565)
check("a contact cut short starts over", frames(0.15).enemy is psycho)
switched = frames(0.1)
check("held long enough, the lock moves to the one aimed at", switched.enemy is brute and switched.locked
      and near(switched.point, aim.look(pc, character, 5000.0).anchor))

scene((psycho, 40.0), (brute, 40.0))
frames(0.15)
state["look"] = (0.0, 26.565)
jumped = frames(0.1)
check("before the lock, the aim jumps from one enemy to another with no gap: the second one's contact starts at "
      "nothing, he is not locked on the first one's time", jumped.enemy is brute and jumped.locked is False)
check("he is after his own two tenths of a second", frames(0.15).locked)

scene((psycho, 40.0))
check("a contact time of zero locks at the first touch", frame(delay=0.0).locked)
scene((psycho, 40.0))
frames(0.15)
state["look"] = (0.0, 10.0)
frame()
state["look"] = (0.0, 0.0)
check("before the lock, a contact cut short starts over too", frames(0.15).locked is False and frames(0.1).locked)

scene((psycho, 40.0))
aimed = aim.look(pc, character, 5000.0)
check("without the lock the target is the aim's own, enemy or nobody",
      lock.plain(aimed) == lock.Target(psycho, aimed.anchor, aimed.hit, "Char_Psycho", 960.0, False)
      and lock.plain(aim.Aim(anchor=(5000.0, 0.0, 50.0))) is None)
psycho.K2_GetActorLocation = lambda: None
check("an enemy that cannot be placed is not locked: the beam ends on him as before", not frames(0.5).locked)
del psycho.K2_GetActorLocation

scene((psycho, 40.0))
frames(0.25)
world_line = state["line"]


def broken(start, end):
    """The camera's own ray still answers; the ray to the locked enemy, shorter, fails."""
    if end[0] < 4000.0:
        raise RuntimeError("the game refuses this ray")
    return world_line(start, end)


state["line"] = broken
errors = len(state["errors"])
failed = frame()
check("a lock that fails does not take the shot down: the target is the aim's own, said once",
      failed.enemy is psycho and failed.locked is False and not lock.held() and len(state["errors"]) == errors + 1)
state["line"] = world_line
check("and nothing is locked again", not frames(0.5).locked and len(state["errors"]) == errors + 1)
lock.restart()
check("until the mod is switched on anew", frames(0.25).locked)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
