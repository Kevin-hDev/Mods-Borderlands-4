"""Tests the third-person wall-climb body animation and its wall-facing guard."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
hooks: dict[tuple[str, str, str], object] = {}
hooks_module = sys.modules["unrealsdk.hooks"]
hooks_module.Type.PRE = "PRE"
hooks_module.add_hook = lambda path, kind, identifier, callback: hooks.__setitem__(
    (path, kind, identifier), callback)
hooks_module.has_hook = lambda path, kind, identifier: (path, kind, identifier) in hooks
hooks_module.remove_hook = lambda path, kind, identifier: hooks.pop((path, kind, identifier), None) is not None

from apex_movement import climb_body  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Body:
    def __init__(self, skeleton: object) -> None:
        self.CurrentSkeleton = skeleton
        self.plays: list[dict[str, object]] = []
        self.stops: list[tuple[float, str]] = []

    def PlaySlotAnimationAsDynamicMontage(self, **kwargs: object) -> object:
        self.plays.append(kwargs)
        return object()

    def StopSlotAnimation(self, blend: float, slot: str) -> None:
        self.stops.append((blend, slot))


class Sequence(sdk_stubs.FakeSequence):
    def __init__(self, skeleton: object) -> None:
        super().__init__(0.6)
        self.Name = "AS_Wall_Climb_U"
        self.Skeleton = skeleton


player_skeleton = object()
other_skeleton = object()
body = Body(player_skeleton)
character = sdk_stubs.FakeCharacter()
character.anim = body
character.Mesh = types.SimpleNamespace(GetAnimInstance=lambda: body)
character.rotation = types.SimpleNamespace(Pitch=2.0, Yaw=15.0, Roll=3.0)
character.turns = []
character.K2_GetActorRotation = lambda: character.rotation


def turn(rotation: object, teleport: bool) -> bool:
    character.rotation = rotation
    character.turns.append((rotation.Pitch, rotation.Yaw, rotation.Roll, teleport))
    return True


character.K2_SetActorRotation = turn
expected = Sequence(player_skeleton)
foreign = Sequence(other_skeleton)
state["objects"].update({
    ("AnimSequence", climb_body.SEQUENCE_PATH.format(character="DarkSiren")): expected,
    ("AnimSequence", climb_body.SEQUENCE_PATH.format(character="ExoSoldier")): foreign,
})
wall = types.SimpleNamespace(into_x=1.0, into_y=0.0)

climb_body.start(character, wall, 372 / 370)
check("the current character's native climb animation plays on the body", body.plays == [{
    "Asset": expected, "SlotNodeName": "FullBody", "BlendInTime": 0.2, "BlendOutTime": 0.2,
    "InPlayRate": 1.0, "LoopCount": 3, "BlendOutTriggerTime": -1.0, "InTimeToStartMontageAt": 0.0,
}])
key = (climb_body.HOOK_PATH, "PRE", climb_body.IDENTIFIER)
check("wall-facing is installed only while the body animation runs", key in hooks)
hooks[key](object(), None, None, None)
check("another animation instance cannot turn the player", character.turns == [])
hooks[key](body, None, None, None)
check("the body faces the wall without changing pitch or roll",
      character.turns == [(2.0, 0.0, 3.0, False)])

climb_body.update_wall(types.SimpleNamespace(into_x=0.0, into_y=1.0))
hooks[key](body, None, None, None)
check("a changing wall updates the facing on the next body frame", character.turns[-1] == (2.0, 90.0, 3.0, False))

climb_body.stop()
check("the end stops only the body's climb slot", body.stops == [(0.2, "FullBody")])
check("the end removes the wall-facing hook", key not in hooks)
turns = len(character.turns)
climb_body.before_update(body, None, None, None)
check("after the climb the game controls facing again", len(character.turns) == turns)

climb_body.start(character, wall, 1.0)
stops = len(body.stops)
climb_body.reset()
check("a character reset forgets the old body without writing into it", len(body.stops) == stops and key not in hooks)


def refuse(**_kwargs: object) -> object:
    raise RuntimeError("unknown slot")


body.PlaySlotAnimationAsDynamicMontage = refuse
climb_body.start(character, wall, 1.0)
climb_body.start(character, wall, 1.0)
check("a body failure is reported once and leaves no hook",
      sum("body climb animation switched off" in line for line in state["errors"]) == 1 and key not in hooks)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
