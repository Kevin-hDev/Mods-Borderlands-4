"""The dynamic camera reads sprinting, ground, crouch, speed and aiming; a player not built yet gives no sample."""

import pathlib
import sys
from types import SimpleNamespace as NS

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.player_sample import read  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def pc(sprinting=True, mode="EMovementMode.MOVE_Walking", velocity=(600.0, 800.0, 0.0), wants=False,
       state="NotZoomed", move=None, crouched=False):
    movement = NS(bIsSprinting=sprinting, MovementMode=mode, Velocity=NS(X=velocity[0], Y=velocity[1], Z=velocity[2]),
                  IsPerformingControlledMove=lambda: move is not None,
                  ControlledMoveReplicationData=NS(ControlledMove=move))
    return NS(OakCharacter=NS(CharacterMovement=movement, ZoomState=NS(bWantsToZoom=wants, State=NS(name=state)),
                              bIsCrouched=crouched))


sample = read(pc())
check("sprinting on the ground at 1000",
      sample.sprinting and not sample.in_air and not sample.driven and sample.speed == 1000.0 and not sample.aiming)
check("a fall's speed counts: the grapple's pull is speed the player feels",
      read(pc(velocity=(0.0, 0.0, -1500.0))).speed == 1500.0)
check("a jump or the grapple: Falling", read(pc(mode="EMovementMode.MOVE_Falling")).in_air is True)
check("a climb is not the air", read(pc(mode="EMovementMode.MOVE_Custom")).in_air is False)
slide = read(pc(move=NS(Name="Move_Slide")))
check("a slide is a move the game drives, named Move_Slide", slide.driven is True and slide.sliding is True)
dash = read(pc(move=NS(Name="Move_Dash")))
check("a dash is driven, not a slide", dash.driven is True and dash.sliding is False)
check("a stale copy is not read when the game says no move runs",
      read(pc(move=None)).sliding is False)
check("wanting to aim counts at once", read(pc(wants=True)).aiming)
check("zoomed in without the button counts too", read(pc(state="ZoomedIn")).aiming)
check("a speed the game gives as not a number reads as stopped",
      read(pc(velocity=(float("nan"), 0.0, 0.0))).speed == 0.0)
check("crouched, as the game says", read(pc(crouched=True)).crouched and not read(pc()).crouched)
climb = read(pc(velocity=(300.0, 400.0, 1200.0)))
check("the speed in three axes, and on the flat for the framing",
      climb.velocity == (300.0, 400.0, 1200.0) and climb.flat_speed == 500.0 and climb.speed == 1300.0)
check("a speed not a number reads as stopped on every axis",
      read(pc(velocity=(float("nan"), 0.0, 0.0))).velocity == (0.0, 0.0, 0.0))
check("no controller, no sample", read(None) is None)
check("no character (vehicle, loading), no sample", read(NS(OakCharacter=None)) is None)
check("a character not built yet, no sample", read(NS(OakCharacter=NS())) is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
