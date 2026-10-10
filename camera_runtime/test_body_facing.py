"""Tests the body facing its run: capped turns on every side, slides included, from where the game left the body, back
to the camera when the hunter aims or glides and then handed back, faster to the crosshair while he acts, turned where
he stopped while he stands, and at 180 degrees the run behind the sides left to the game, with a margin. Ported from the trial's tests (2026-10-09)."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import body_facing  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def vector(x: float, y: float) -> types.SimpleNamespace:
    return types.SimpleNamespace(X=x, Y=y, Z=0.0)


class Player:
    """A character the unit can turn: the yaw it is given is the one it then reports."""

    def __init__(self) -> None:
        self.yaw, self.view_yaw = 0.0, 0.0
        self.set_calls: list[tuple] = []
        self.ZoomState = types.SimpleNamespace(bWantsToZoom=False, State=types.SimpleNamespace(name="NotZoomed"))
        self.CharacterMovement = types.SimpleNamespace(MovementMode=1, Velocity=vector(0.0, 0.0))
        self.Controller = types.SimpleNamespace(GetControlRotation=lambda: types.SimpleNamespace(Yaw=self.view_yaw))

    def K2_GetActorRotation(self) -> types.SimpleNamespace:
        return types.SimpleNamespace(Pitch=0.0, Yaw=self.yaw, Roll=0.0)

    def K2_SetActorRotation(self, rotation, teleport) -> bool:
        self.set_calls.append((round(rotation.Yaw, 3), teleport))
        self.yaw = rotation.Yaw
        return True


class FakePose:
    def __init__(self) -> None:
        self.applied: list[tuple] = []
        self.restored = 0

    def apply(self, anim, offset, run_vs_body) -> None:
        self.applied.append((round(offset, 3), None if run_vs_body is None else round(run_vs_body, 3)))

    def restore(self, anim) -> None:
        self.restored += 1


def rotator(pitch, yaw, roll):
    return types.SimpleNamespace(Pitch=pitch, Yaw=yaw, Roll=roll)


turned = body_facing.turned
check("a step toward the goal is capped", turned(0.0, -90.0, 30.0) == -30.0)
check("the goal is reached when close enough", turned(-80.0, -90.0, 30.0) == -90.0)
check("the short way round, across the back", turned(170.0, -170.0, 10.0) == 180.0)
check("from left to right, through the front", turned(-90.0, 90.0, 60.0) == -30.0)

FRAME = 10_000_000  # 10 ms: 7.2 degrees at 720 degrees a second, 14.4 at 1440
anim = types.SimpleNamespace(bIsGliding=False)
player, pose = Player(), FakePose()
movement = player.CharacterMovement
facing = body_facing.BodyFacing(rotator)
check("standing still, the body is left to the game",
      facing.step(player, anim, pose, False, True, 0) is False and player.set_calls == [])
movement.Velocity = vector(0.0, -50.0)
check("too slow, the body is left to the game", facing.step(player, anim, pose, False, True, FRAME) is False)
check("left to the game, the animation is left alone", pose.applied == [])

# The game had already turned the body 30 degrees right of the view, as it does in sprint.
player.view_yaw, player.yaw = 10.0, 40.0
movement.Velocity = vector(0.0, -621.0)  # world yaw 270: 100 degrees left of the view
check("running left, it turns from where the game left the body",
      facing.step(player, anim, pose, False, True, 2 * FRAME) is True and player.set_calls == [(32.8, False)])
check("the legs are given the run seen from the turned body", pose.applied == [(22.8, -122.8)])
PAUSE = 2 * FRAME + 10**9
facing.step(player, anim, pose, False, True, PAUSE)
check("a long pause turns it by a capped step only", abs(facing.offset + 49.2) < 1e-9)
for frame in range(1, 10):
    facing.step(player, anim, pose, False, True, PAUSE + frame * FRAME)
check("the next frames turn it until it faces the run", player.yaw == 270.0 and facing.offset == -100.0)
check("facing the run, the legs run straight ahead", pose.applied[-1] == (-100.0, 0.0))

AIM = 2 * 10**9
player.view_yaw = 0.0
facing.step(player, anim, pose, False, True, AIM)
check("the body follows a turned view", facing.offset == -90.0 and player.yaw == 270.0)
player.ZoomState.bWantsToZoom = True
facing.step(player, anim, pose, False, True, AIM + FRAME)
check("aiming, the body turns back toward the camera", abs(facing.offset + 82.8) < 1e-9)
check("turning back, the legs are the game's", pose.applied[-1] == (-82.8, None))
player.ZoomState.bWantsToZoom = False
player.ZoomState.State = types.SimpleNamespace(name="ZoomedIn")
movement.Velocity = vector(0.0, 0.0)
for frame in range(2, 40):
    facing.step(player, anim, pose, False, True, AIM + frame * FRAME)
check("once it faces the camera, it is handed back and the chest's twist given back",
      not facing.holding and player.yaw == 0.0 and pose.restored == 1)
count = len(player.set_calls)
check("handed back, nothing more is turned",
      facing.step(player, anim, pose, False, True, 3 * 10**9) is False and len(player.set_calls) == count)

player.ZoomState.State = types.SimpleNamespace(name="NotZoomed")
movement.Velocity = vector(0.0, 621.0)
anim.bIsGliding = True
check("gliding, the body is the game's", facing.step(player, anim, pose, False, True, 4 * 10**9) is False)
anim.bIsGliding = False
movement.MovementMode = 6
check("climbing or any other mode, the body is the game's",
      facing.step(player, anim, pose, False, True, 4 * 10**9) is False)
movement.MovementMode = 3
check("in the air, the body faces the run", facing.step(player, anim, pose, False, True, 4 * 10**9 + FRAME) is True)
movement.MovementMode = 1
player.Controller = None
count = len(player.set_calls)
check("without a controller for a moment, nothing is turned",
      facing.step(player, anim, pose, False, True, 4 * 10**9 + 2 * FRAME) is True and len(player.set_calls) == count)
player.Controller = types.SimpleNamespace(GetControlRotation=lambda: types.SimpleNamespace(Yaw=player.view_yaw))

# Actions: the body runs straight back, then the hunter fires.
player.view_yaw, player.yaw = 0.0, 0.0
movement.Velocity = vector(-621.0, 0.0)  # world yaw 180
facing, pose = body_facing.BodyFacing(rotator), FakePose()
START = 10 * 10**9
for frame in range(30):
    facing.step(player, anim, pose, False, True, START + frame * FRAME)
check("running back at 360 degrees, the body faces back", facing.offset == 180.0)
facing.step(player, anim, pose, True, True, START + 30 * FRAME)
check("acting, the body turns back to the crosshair at the action rate", abs(abs(facing.offset) - 165.6) < 1e-9)
check("acting, the legs are the game's", pose.applied[-1][1] is None)
facing.step(player, anim, pose, False, True, START + 31 * FRAME)
check("the action over, the body turns back to the run at the run rate", abs(facing.offset + 172.8) < 1e-9)

# 180 degrees: a run behind the sides is the game's backward run.
facing, pose = body_facing.BodyFacing(rotator), FakePose()
player.yaw = 0.0
START = 20 * 10**9
check("at 180 degrees, running straight back leaves the body to the game",
      facing.step(player, anim, pose, False, False, START) is False and pose.applied == [])
movement.Velocity = vector(-439.0, 439.0)  # world yaw 135: back right diagonal
check("and so does a back diagonal", facing.step(player, anim, pose, False, False, START + FRAME) is False)
movement.Velocity = vector(0.0, 621.0)  # 90: right
facing.step(player, anim, pose, False, False, START + 2 * FRAME)
check("a side run turns the body", facing.holding and abs(facing.offset - 7.2) < 1e-9)
for frame in range(3, 30):
    facing.step(player, anim, pose, False, False, START + frame * FRAME)
movement.Velocity = vector(-212.0, 583.0)  # about 110: still a side run
facing.step(player, anim, pose, False, False, START + 30 * FRAME)
check("a run a little behind the side still turns the body", facing.offset > 90.0)
movement.Velocity = vector(-264.0, 562.0)  # about 115: past the limit, inside the margin
facing.step(player, anim, pose, False, False, START + 31 * FRAME)
check("past the limit by less than the margin, the side holds", not facing.behind)
movement.Velocity = vector(-389.0, 484.0)  # about 129: past the margin
facing.step(player, anim, pose, False, False, START + 32 * FRAME)
check("past the margin, the run is behind: the body turns back to the camera",
      facing.behind and pose.applied[-1][1] is None)
movement.Velocity = vector(-264.0, 562.0)  # about 115 again
facing.step(player, anim, pose, False, False, START + 33 * FRAME)
check("coming back inside the margin keeps it behind, so the body never swings", facing.behind)
movement.Velocity = vector(-130.0, 607.0)  # about 102
facing.step(player, anim, pose, False, False, START + 34 * FRAME)
check("well before the limit, it is a side run again", not facing.behind)
facing.release(anim, pose)
check("released, the body and the margin are forgotten",
      not facing.holding and not facing.behind and pose.restored == 1)

# Stopping: the hunter stays turned where he stopped (Kevin, 2026-10-09).
facing, pose = body_facing.BodyFacing(rotator), FakePose()
player.view_yaw, player.yaw = 0.0, 0.0
movement.Velocity = vector(0.0, -621.0)  # world yaw 270: left
START = 30 * 10**9
for frame in range(20):
    facing.step(player, anim, pose, False, True, START + frame * FRAME)
check("running left, the body faces left", facing.offset == -90.0)
movement.Velocity = vector(0.0, 0.0)
for frame in range(20, 40):
    facing.step(player, anim, pose, False, True, START + frame * FRAME)
check("stopped, the body stays turned left", facing.holding and facing.offset == -90.0 and player.yaw == 270.0)
check("standing, the legs are the game's", pose.applied[-1] == (-90.0, None))
player.view_yaw = 60.0
facing.step(player, anim, pose, False, True, START + 40 * FRAME)
check("the camera turning around him leaves the body where it stopped",
      player.yaw == 270.0 and facing.offset == -150.0)
facing.step(player, anim, pose, True, True, START + 41 * FRAME)
check("firing, it turns back to the crosshair at the action rate", abs(facing.offset + 135.6) < 1e-9)
for frame in range(42, 60):
    facing.step(player, anim, pose, True, True, START + frame * FRAME)
check("facing the crosshair, it is the game's again", not facing.holding and pose.restored == 1)
check("the shot over, standing still facing the camera stays the game's",
      facing.step(player, anim, pose, False, True, START + 60 * FRAME) is False and facing.kept_yaw is None)

player.view_yaw, player.yaw = 0.0, 0.0
movement.Velocity = vector(-621.0, 0.0)  # world yaw 180: straight back
for frame in range(61, 90):
    facing.step(player, anim, pose, False, True, START + frame * FRAME)
movement.Velocity = vector(0.0, 0.0)
facing.step(player, anim, pose, False, True, START + 90 * FRAME)
check("stopped after running back, he faces the camera", facing.offset == 180.0 and player.yaw == 180.0)
movement.Velocity = vector(621.0, 0.0)  # forward
facing.step(player, anim, pose, False, True, START + 91 * FRAME)
check("running again, the body turns toward the new run at the run rate",
      facing.kept_yaw is None and abs(abs(facing.offset) - 172.8) < 1e-9)
for frame in range(92, 120):
    facing.step(player, anim, pose, False, True, START + frame * FRAME)
movement.Velocity = vector(0.0, 0.0)
check("stopped after running forward, the body is the game's",
      facing.step(player, anim, pose, False, True, START + 120 * FRAME) is False)

movement.Velocity = vector(0.0, 621.0)  # right
for frame in range(121, 140):
    facing.step(player, anim, pose, False, True, START + frame * FRAME)
movement.Velocity = vector(0.0, 0.0)
facing.step(player, anim, pose, False, True, START + 140 * FRAME)
player.ZoomState.bWantsToZoom = True
facing.step(player, anim, pose, False, True, START + 141 * FRAME)
check("aiming while standing turns the body back to the camera", abs(facing.offset - 82.8) < 1e-9)
player.ZoomState.bWantsToZoom = False
facing.release(anim, pose)
check("released, the kept direction is forgotten", facing.kept_yaw is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
