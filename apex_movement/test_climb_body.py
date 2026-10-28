"""Tests the third-person wall-climb body animation and its wall-facing guard, with the real choice of loop
(climb_loops.py): each hunter's loop plays on whatever body it wears, the game's refusal is said once and leaves no
hook, and a body without animation plays nothing."""

import math
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

from apex_movement import climb_body, climb_loops  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Body:
    """A body's animation instance: plays what it is given and gives a montage back, as the engine does once it
    plays; refusing, it gives none."""

    def __init__(self, skeleton: str, refuses: bool = False) -> None:
        self.CurrentSkeleton = types.SimpleNamespace(Name=skeleton)
        self.refuses = refuses
        self.plays: list[dict[str, object]] = []
        self.stops: list[tuple[float, str]] = []

    def PlaySlotAnimationAsDynamicMontage(self, **kwargs: object) -> object:
        self.plays.append(kwargs)
        return None if self.refuses else object()

    def StopSlotAnimation(self, blend: float, slot: str) -> None:
        self.stops.append((blend, slot))


class Sequence(sdk_stubs.FakeSequence):
    def __init__(self, name: str, length: float) -> None:
        super().__init__(length)
        self.Name = name


def make_character(hunter: str, body: object) -> object:
    character = sdk_stubs.FakeCharacter()
    character.GbxActorData = types.SimpleNamespace(GbxActorDef=f"FGbxDefPtr('Char_{hunter}', x)")
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
    return character


# Each hunter's first loop and its length in the game's files (2026-10-25).
FIRST = {"DarkSiren": ("AS_Wall_Climb_U", 0.6), "RoboDealer": ("AS_Wall_Climb_U", 0.8),
         "Paladin": ("AS_Ladder_Ascend", 0.6333333), "ExoSoldier": ("AS_Ladder_Ascend", 0.6333333),
         "Gravitar": ("AS_Ladder_Ascend", 0.6333333), "CorpoHacker": ("AS_Ladder_Ascend", 0.6333333)}
sequences = {hunter: Sequence(name, length) for hunter, (name, length) in FIRST.items()}
state["objects"].update({("AnimSequence", climb_loops.LOOPS[hunter][0]): sequences[hunter] for hunter in FIRST
                         if hunter in climb_loops.LOOPS})
wall = types.SimpleNamespace(into_x=1.0, into_y=0.0)
key = (climb_body.HOOK_PATH, "PRE", climb_body.IDENTIFIER)

body = Body("SK_DarkSiren_Skeleton")
character = make_character("DarkSiren", body)
climb_body.start(character, wall, 372 / 370)
check("Vex's wall climb plays on her body, as validated on 2026-09-23", body.plays == [{
    "Asset": sequences["DarkSiren"], "SlotNodeName": "FullBody", "BlendInTime": 0.2, "BlendOutTime": 0.2,
    "InPlayRate": 1.0, "LoopCount": 3, "BlendOutTriggerTime": -1.0, "InTimeToStartMontageAt": 0.0,
}])
check("the log names the loop and the body it plays on",
      any("AS_Wall_Climb_U on SK_DarkSiren_Skeleton" in line for line in state["misc"]))
check("wall-facing is installed only while the body animation runs", key in hooks)
hooks[key](object(), None, None, None)
check("another animation instance cannot turn the player", character.turns == [])
hooks[key](body, None, None, None)
check("the body faces the wall without changing pitch or roll", character.turns == [(2.0, 0.0, 3.0, False)])

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

# The bodies worn on 2026-10-25, C4SH in his Premium body among them, and another hunter's Prison body.
WORN = {"DarkSiren": "SK_DarkSiren_Skeleton", "RoboDealer": "SK_RD_Body_02_Premium_Skeleton",
        "Paladin": "SK_PA_Body_01_Prison_Skeleton", "ExoSoldier": "SK_ExoSoldier_Skeleton",
        "Gravitar": "SK_Gravitar_Skeleton", "CorpoHacker": "SK_CorpoHacker_Skeleton"}
for hunter, skeleton in WORN.items():
    climb_body.reset()
    worn = Body(skeleton)
    # 2.5 s: 6 loops of 0.6 s, 5 of 0.63 s and of 0.8 s, so a wrong length shows.
    climb_body.start(make_character(hunter, worn), wall, 2.5)
    played = worn.plays[0] if len(worn.plays) == 1 else {}
    name, length = FIRST[hunter]
    check(f"{hunter} on {skeleton}: its {name} loops on the body, enough loops for the longest climb",
          played.get("Asset") is sequences[hunter] and played.get("LoopCount") == math.ceil(2.5 / length) + 1
          and key in hooks)
    climb_body.stop()

errors = len(state["errors"])
climb_body.reset()
refusing = Body("SK_Stranger_Skeleton", refuses=True)
for hunter in ("Paladin", "Paladin", "ExoSoldier", "DarkSiren"):
    climb_body.start(make_character(hunter, refusing), wall, 1.0)
climb_body.start(make_character("Paladin", Body("SK_Other_Skeleton", refuses=True)), wall, 1.0)
check("a loop the game refuses: no hook, nothing to stop, said once per hunter and body worn, naming both",
      key not in hooks and refusing.stops == [] and state["errors"][errors:] == [
          "[Apex Movement] body climb animation refused by the game: Paladin's AS_Ladder_Ascend on SK_Stranger_Skeleton",
          "[Apex Movement] body climb animation refused by the game: ExoSoldier's AS_Ladder_Ascend on "
          "SK_Stranger_Skeleton",
          "[Apex Movement] body climb animation refused by the game: DarkSiren's AS_Wall_Climb_U on SK_Stranger_Skeleton",
          "[Apex Movement] body climb animation refused by the game: Paladin's AS_Ladder_Ascend on SK_Other_Skeleton"])
climb_body.start(make_character("Paladin", Body("SK_Paladin_Skeleton")), wall, 1.0)
check("a refusal does not switch the animation off for the next climb", key in hooks)
climb_body.stop()

errors = len(state["errors"])
climb_body.start(make_character("Paladin", None), wall, 1.0)
check("a character without a body animation plays nothing and says it", key not in hooks
      and len(state["errors"]) == errors + 1 and "the body has no animation" in state["errors"][-1])

errors = len(state["errors"])
lonely = Body("SK_Stranger_Skeleton")
climb_body.start(make_character("Stranger", lonely), wall, 1.0)
check("a hunter without a known loop plays nothing", lonely.plays == [] and key not in hooks
      and len(state["errors"]) == errors + 1)


def refuse(**_kwargs: object) -> object:
    raise RuntimeError("unknown slot")


body.PlaySlotAnimationAsDynamicMontage = refuse
climb_body.reset()
climb_body.start(character, wall, 1.0)
climb_body.start(character, wall, 1.0)
check("a body failure is reported once and leaves no hook",
      sum("body climb animation switched off" in line for line in state["errors"]) == 1 and key not in hooks)


def unreadable() -> object:
    raise RuntimeError("mesh gone")


climb_body.reset()
lost = make_character("Paladin", None)
lost.Mesh = types.SimpleNamespace(GetAnimInstance=unreadable)
try:
    climb_body.start(lost, wall, 1.0)
    raised = False
except Exception:
    raised = True
later = Body("SK_Paladin_Skeleton")
climb_body.start(make_character("Paladin", later), wall, 1.0)
check("a body the game cannot give: the climb's caller never sees the error, the body animation off until a reset",
      not raised and key not in hooks and later.plays == [])
climb_body.reset()
climb_body.start(make_character("Paladin", later), wall, 1.0)
check("and back after the next character reset", len(later.plays) == 1 and key in hooks)
climb_body.stop()


def lookup_fails(class_name: str, path: str) -> object:
    raise RuntimeError("lookup failed")


climb_body.reset()
sdk = sys.modules["unrealsdk"]
kept_find, sdk.find_object = sdk.find_object, lookup_fails
try:
    climb_body.start(make_character("Paladin", Body("SK_Paladin_Skeleton")), wall, 1.0)
    raised = False
except Exception:
    raised = True
sdk.find_object = kept_find
check("a loop lookup the game fails: the climb's caller never sees the error, no hook left", not raised
      and key not in hooks)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
