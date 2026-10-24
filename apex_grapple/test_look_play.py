"""Tests look_play.py with the game replaced by fakes, on Vex: her pistol, holster and ropes built once; through the
eyes, the rope waits below the screen until the arm is in, then leaves from the arms' pistol, and at the end the hook
comes back when the rope would show, or the rope leaves the screen with the arm and goes; from behind, the pistol in
her hand until the hook is back in it, then in its holster; the holster kept or not; a new character, Loveless, in
her own holster."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import (look_assets, look_eye, look_gun, look_muzzle, look_play, look_settings,  # noqa: E402
                          look_shots)
import sdk_objects  # noqa: E402
import look_fixture  # noqa: E402
import vex_fixture  # noqa: E402

fails: list[str] = []
S = 1_000_000_000
ANCHOR = (2000.0, 0.0, 170.0)


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a, b, within=1e-6) -> bool:
    return a is not None and all(abs(x - y) <= within for x, y in zip(a, b))


def seen(gun: look_gun.Gun) -> set[str]:
    return set(gun.seen)


def run(start_s: float, until_s: float, end_s: float | None = None, catch_s: float | None = None) -> None:
    """Frames at 60 a second; the hook bites at catch_s, the pull pulls and ends at end_s."""
    caught = None if catch_s is None else round(catch_s * 60)
    ended = None if end_s is None else round(end_s * 60)
    for frame in range(round(start_s * 60), round(until_s * 60) + 1):
        now = frame * S // 60
        if frame == caught:
            look_play.catch(character, now, 1830.0, 600.0, 2500.0)
        if caught is not None and caught < frame < (ended or 0):
            look_play.pulled((1500.0, 0.0, 0.0), (2500.0, 0.0, 0.0))
        if frame == ended:
            look_play.end(character, now)
        look_play.tick(character, now)


record = look_fixture.install(state)
vex_fixture.install(state)
character = look_fixture.dress(sdk_stubs.FakeCharacter(), record)
arms, body = vex_fixture.dress(state, character)
clock = vex_fixture.camera(state, character)
pc = state["pc"]

look_play.prepare(character)
look_play.prepare(character)
gun = look_play._gun
check("her pistol, holster and two ropes built once", look_play.ready() and len(record["pieces"]) == 4 + 140)
look_play.start(character, ANCHOR, 1 * S, 0.4)
waiting = look_muzzle.waiting(pc, look_assets.MUZZLE_IN_CM)
check("through the eyes, the shot's rope leaves from below the screen while the arm comes in",
      near(look_shots.hand(), waiting) and look_play.busy())
run(1.0, 1.2)
check("the arms' pistol hidden until the arm's gesture has faded in", seen(gun) == set()
      and near(look_shots.hand(), waiting))
run(1.25, 1.3)
from_pistol = look_muzzle.from_arms(pc, look_muzzle.on_piece(gun.pieces[look_gun.ARMS_PISTOL],
                                                             look_assets.PIECES["pistol_arms"]["muzzle_cm"]))
check("then shown, the rope from its muzzle as the world shows it", seen(gun) == {look_gun.ARMS_PISTOL}
      and near(look_shots.hand(), from_pistol))
run(1.3 + 1.0 / 60.0, 3.5, end_s=2.0, catch_s=1.4)
check("the point stayed on screen: the hook came back while the arm went out, the shot over",
      not look_play.busy() and seen(gun) == set() and not look_shots.busy())
clock["now"] = 20.0
look_play.tick(character, 20 * S)
clock["now"] = 20.01
character.location = sdk_objects.vector(40.0, 0.0, 0.0)
pc.PlayerCameraManager.CameraCachePrivate.Timestamp = 20.0
check("each frame, shot or not, notes where Vex is: the next frame's camera, filled before she moved, moves with "
      "her", near(look_eye.camera(pc)[0], (40.0, 0.0, 170.0)))
character.location = sdk_objects.vector(0.0, 0.0, 0.0)
pc.PlayerCameraManager.CameraCachePrivate.Timestamp = -1.0

# 2026-10-24 review: through the eyes, a frame of a shot read the whole camera again for the muzzle, twice while the arm
# came in, though the frame had just noted where Vex was.
reads = {"camera": 0, "clock": 0}
manager = pc.PlayerCameraManager
real_where = manager.GetCameraLocation
manager.GetCameraLocation = lambda: (reads.__setitem__("camera", reads["camera"] + 1), real_where())[1]
statics = state["extra_classes"]["GameplayStatics"].ClassDefaultObject
real_clock = statics.GetTimeSeconds
statics.GetTimeSeconds = lambda who: (reads.__setitem__("clock", reads["clock"] + 1), real_clock(who))[1]
look_play.start(character, ANCHOR, 30 * S, 0.4)
reads.update(camera=0, clock=0)
look_play.tick(character, 30 * S + S // 60)
check("while the arm comes in, a frame reads the camera once for the view and once for the muzzle, the clock once",
      reads == {"camera": 2, "clock": 1})
run(30.0 + 2.0 / 60.0, 30.29)
reads.update(camera=0, clock=0)
look_play.tick(character, 30 * S + 3 * S // 10)
check("from the arms' pistol, the clock once too", seen(gun) == {look_gun.ARMS_PISTOL} and reads["clock"] == 1)
run(30.3 + 1.0 / 60.0, 32.5, end_s=31.0, catch_s=30.4)
manager.GetCameraLocation, statics.GetTimeSeconds = real_where, real_clock
check("and the shot ends as before", not look_play.busy())

vex_fixture.camera(state, character, yaw=90.0)
pc = state["pc"]
look_play.start(character, ANCHOR, 4 * S, 0.4)
run(4.0, 4.5, catch_s=4.4)
place = next(one for one in look_shots._places if one.shot is not None)
run(4.5 + 1.0 / 60.0, 5.0, end_s=5.0)
check("the point off screen: the rope stays hooked as the arm leaves", look_play._shot.leaving and place.hook.visible)
frame = round(5.0 * 60)
while look_play._shot is not None and look_play._shot.leaving:
    frame += 1
    look_play.tick(character, frame * S // 60)
check("the frame the arm is out, still off screen: rope and hook gone at once, never coming back",
      place.shot is None and not place.hook.visible and look_fixture.shown(place.rope.strands[0][0]) == 0
      and any("leaves the screen with the arm" in line for line in state["misc"]))
run(frame / 60.0 + 1.0 / 60.0, 6.0)
check("then the shot is over", not look_play.busy())

vex_fixture.camera(state, character, third=True)
pc = state["pc"]
run(6.0, 6.1)
check("from behind, between shots: the pistol in its holster", seen(gun) == {look_gun.HOLSTER, look_gun.HOLSTERED})
look_play.start(character, ANCHOR, 7 * S, 0.4)
check("from behind, the rope from the pistol in her hand",
      near(look_shots.hand(), look_muzzle.on_piece(gun.pieces[look_gun.BODY_PISTOL],
                                                   look_assets.PIECES["pistol_body"]["muzzle_cm"])))
run(7.0, 7.9, end_s=7.9, catch_s=7.4)
check("in her hand while the hook is out", seen(gun) == {look_gun.HOLSTER, look_gun.BODY_PISTOL})
rope = look_play._shot.rope
frame = round(7.9 * 60)
while look_shots.holds(rope):
    frame += 1
    look_play.tick(character, frame * S // 60)
check("the frame the hook is back in it, the arm still folding: the pistol back in its holster",
      look_play.busy() and seen(gun) == {look_gun.HOLSTER, look_gun.HOLSTERED})
run(frame / 60.0 + 1.0 / 60.0, 9.5)
check("then the shot is over, the pistol still in its holster", not look_play.busy()
      and seen(gun) == {look_gun.HOLSTER, look_gun.HOLSTERED})
look_settings.holster.value = look_settings.WITHOUT
run(9.6, 9.6)
check("without the holster: nothing on her hip", seen(gun) == set())
look_settings.holster.value = look_settings.WITH
character.Mesh.GestaltMeshParts = [types.SimpleNamespace(Name=part) for part in vex_fixture.COAT]
run(9.7, 9.7)
check("in her long coat: no holster and no pistol on her hip, hidden under it", seen(gun) == set())
look_play.start(character, ANCHOR, 10 * S, 0.4)
run(10.0, 10.3)
check("and still the pistol in her hand at a shot", seen(gun) == {look_gun.BODY_PISTOL})
run(10.3 + 1.0 / 60.0, 12.0, end_s=10.5, catch_s=10.4)
character.Mesh.GestaltMeshParts = [types.SimpleNamespace(Name=part) for part in vex_fixture.PREMIUM]
run(12.1, 12.1)
check("back in her Premium outfit, the holster shows again", seen(gun) == {look_gun.HOLSTER, look_gun.HOLSTERED})

old = list(record["pieces"])
newcomer = look_fixture.dress(sdk_stubs.FakeCharacter(), record)
vex_fixture.dress(state, newcomer, definition="Char_CorpoHacker")
look_play.prepare(newcomer)
check("a new character, Loveless: the old pieces removed, new ones built on her, her own holster",
      all(made.called("K2_DestroyComponent") for made in old[:4]) and len(record["pieces"]) == len(old) + 4 + 140
      and look_play._gun is not gun and look_fixture.mesh_of(look_play._gun.pieces[look_gun.HOLSTER])
      == look_assets.PIECES["holster_corpohacker"]["mesh"])
look_play.reset()
check("reset: every gesture stopped and every piece removed", not look_play.built()
      and all(made.called("K2_DestroyComponent") for made in record["pieces"][len(old):len(old) + 4]))
said = sum("outfit:" in line for line in state["misc"])
look_play.tick(newcomer, 13 * S)
check("after a reset, the outfit is said again in the log, though unchanged",
      sum("outfit:" in line for line in state["misc"]) == said + 1)

# 2026-10-24 review: through the eyes, rope away, every frame read the character's place twice: once for the camera of
# the next frame, once to tell the first person from the third.
vex_fixture.camera(state, newcomer)
places: list[int] = []
newcomer.K2_GetActorLocation = lambda: (places.append(1), newcomer.location)[1]
look_play.tick(newcomer, 14 * S)
check("through the eyes with the rope away, a frame reads the character's place once", len(places) == 1)
del newcomer.K2_GetActorLocation

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
