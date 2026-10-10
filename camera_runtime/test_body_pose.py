"""Tests the pose of the turned body: the run given to the legs, the chest's twist kept up to 90 degrees and gone at
135, read from what the game left when the hold starts, and given back whole."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import body_pose  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("the twist is whole up to 90 degrees", body_pose.twist_alpha(-90.0) == 1.0)
check("half gone halfway to 135", body_pose.twist_alpha(112.5) == 0.5)
check("gone from 135", body_pose.twist_alpha(-170.0) == 0.0)

anim = types.SimpleNamespace(Direction=12.0, GbxAnimGraphNode_Rotation_AimOffset_1=types.SimpleNamespace(ALPHA=1.0))
for name in body_pose.AIM_NODES:
    setattr(anim, name, types.SimpleNamespace(ALPHA=0.8))
pose = body_pose.Pose()
pose.apply(anim, 112.5, -3.0)
check("the chest nodes are faded from what the game left",
      all(getattr(anim, name).ALPHA == 0.4 for name in body_pose.AIM_NODES))
check("the mech arms' node is left alone", anim.GbxAnimGraphNode_Rotation_AimOffset_1.ALPHA == 1.0)
check("the legs get the run seen from the body", anim.Direction == -3.0)
pose.apply(anim, 170.0, None)
check("no run given, the legs keep the game's", anim.Direction == -3.0
      and all(getattr(anim, name).ALPHA == 0.0 for name in body_pose.AIM_NODES))
pose.restore(anim)
check("restored, the game's twist is back", all(getattr(anim, name).ALPHA == 0.8 for name in body_pose.AIM_NODES))
anim.GbxAnimGraphNode_Rotation_AimOffset.ALPHA = 0.5
pose.apply(anim, 0.0, 0.0)
check("the next hold reads the game's values afresh", anim.GbxAnimGraphNode_Rotation_AimOffset.ALPHA == 0.5)
pose.restore(anim)
pose.restore(anim)
check("restoring twice, or with no body, changes nothing", anim.GbxAnimGraphNode_Rotation_AimOffset.ALPHA == 0.5)
pose.apply(anim, 0.0, 0.0)
pose.restore(None)
check("a body gone is not touched, and the hold is forgotten", pose.original is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
