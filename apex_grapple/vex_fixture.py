"""Vex as the grapple gun's look meets her in game, for the tests: her definition, a weapon in her right hand, her
first-person arms and her body each recording the montages played on them, the camera through her eyes or behind her,
and every animation the look plays, ours and the game's, in the game's memory."""

import types
from typing import Any

from apex_grapple import look_assets, look_gestures, look_load, look_pieces
import sdk_objects

EYE = (0.0, 0.0, 170.0)
# The parts her body merges, by outfit: the Premium one the holster was fitted on, and her own with its long coat
# (the game's files, 14 October 2026).
PREMIUM = ("SKPart_DS_Body_02_Premium_Upperbody", "SKPart_DS_Body_02_Premium_Lowerbody", "SK_DarkSiren_Base_Head")
COAT = ("SKPart_DarkSiren_Upperbody", "SKPart_DarkSiren_Lowerbody", "SKPart_DarkSiren_Jacket",
        "SKPart_DarkSiren_Stomach", "SK_DarkSiren_Base_Head")
ARMS_FIELD, WORLD_FIELD = 77.0, 110.0
# The game's stows are 0.67 and 0.33 s long, its flight 1 s (read in its files on 2026-10-14).
LENGTHS = {look_gestures.ARMS_STOWS["RH"]: 0.6666667, look_gestures.ARMS_STOWS["PS"]: 0.33333334,
           look_gestures.FLIGHT_PATH: 1.0}


def animations() -> dict[str, float]:
    """Every animation the look can play, by path, with its length."""
    found = dict(LENGTHS)
    for one in look_assets.GESTURES:
        ends = [end for _start, end in one["parts"].values()]
        found[one["path"]] = max(ends)
    return found


def install(state: dict, missing: tuple[str, ...] = ()) -> None:
    """Every animation in the game's memory, but for `missing` paths."""
    for path, length in animations().items():
        state["objects"].pop((look_load.ANIMATION, path), None)
        if path not in missing:
            state["objects"][(look_load.ANIMATION, path)] = sdk_objects.FakeSequence(length)


def dress(state: dict, character: Any, weapon: str | None = "Body_JAK_AR", definition: str = "Char_DarkSiren",
          parts: tuple[str, ...] = PREMIUM) -> tuple[sdk_objects.FakeArms, sdk_objects.FakeArms]:
    """Vex holding `weapon`'s body (None: no weapon), with her arms and her body merging `parts`; returns their
    animation instances."""
    character.GbxActorData = types.SimpleNamespace(GbxActorDef=f"FGbxDefPtr('{definition}', 'GbxActorDef', {{}})")
    held = None if weapon is None else types.SimpleNamespace(BodyData=types.SimpleNamespace(Name=weapon))
    character.ActiveWeapons = types.SimpleNamespace(Slots=[types.SimpleNamespace(Weapon=held)])
    arms = sdk_objects.FakeArms(character)
    for flag in look_pieces.DRAW_FLAGS:
        setattr(arms.Outer, flag, f"arms {flag}")
    body = sdk_objects.FakeArms(character)
    body.Outer.Name = "CharacterMesh0"
    body.Outer.GestaltMeshParts = [types.SimpleNamespace(Name=part) for part in parts]
    character.Mesh = body.Outer
    state["anim_instances"] = [arms]
    return arms, body


def camera(state: dict, character: Any, third: bool = False, yaw: float = 0.0) -> dict:
    """The player's camera through Vex's eyes, or 180 cm behind her, looking along `yaw`, and the game's clock. The
    camera's own clock is before any frame the look saw, so it is taken as given, unless a test moves the clocks
    through the returned dict ("now", the game's; the camera's is manager.CameraCachePrivate.Timestamp)."""
    where = sdk_objects.vector(-180.0 if third else EYE[0], EYE[1], EYE[2])
    turn = types.SimpleNamespace(Pitch=0.0, Yaw=yaw, Roll=0.0)
    manager = types.SimpleNamespace(
        GetActorCameraMode=lambda who: "CameraMode_ThirdPerson" if third else "FirstPerson",
        GetCameraLocation=lambda: where,
        GetCameraRotation=lambda: turn,
        GetFOVAngle=lambda: WORLD_FIELD, CameraModeState=types.SimpleNamespace(ViewModelFOV=ARMS_FIELD),
        CameraCachePrivate=types.SimpleNamespace(Timestamp=-1.0))
    clock = {"now": 0.0}
    state["extra_classes"]["GameplayStatics"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
        GetTimeSeconds=lambda who: clock["now"]))
    character.location = sdk_objects.vector(0.0, 0.0, 0.0)
    state["pc"] = sdk_objects.player(character, state["mappings"])
    state["pc"].PlayerCameraManager = manager
    state["pc"].ControlRotation = turn
    return clock


def slots(instance: sdk_objects.FakeArms) -> list[tuple[str, str]]:
    """Each montage played on an instance: its slot and its animation's name."""
    return [(played["SlotNodeName"], _name(played["Asset"])) for played in instance.played]


def _name(asset: Any) -> str:
    return next((path.rsplit(".", 1)[-1] for (kind, path), found in _registry.items() if found is asset), "?")


_registry: dict = {}


def remember(state: dict) -> None:
    """Lets slots() name the animations: the game's memory as installed."""
    _registry.clear()
    _registry.update(state["objects"])
