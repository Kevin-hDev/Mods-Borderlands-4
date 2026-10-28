"""The player the holster's tests drive: a controller, its character holding a weapon or none, on foot or driving, its
camera, arms and key list, and the key events the SDK hands a keybind."""

import types
from typing import Any


def event(name: str) -> Any:
    """An EInputEvent as the SDK hands it to a keybind declared with event_filter=None."""
    return types.SimpleNamespace(name=name)


def player(weapon: Any = None, on_foot: bool = True) -> tuple[Any, Any]:
    """A player controller and its character holding `weapon`, or riding a vehicle when not `on_foot`."""
    calls: list[tuple] = []
    character = types.SimpleNamespace(
        Name="OakCharacter_1", ActiveWeapons=types.SimpleNamespace(Slots=[types.SimpleNamespace(Weapon=weapon)]),
        ServerSetCurrentWeapon=lambda *args: calls.append(args), calls=calls, bWeaponsRestricted=False)
    pawn = character if on_foot else types.SimpleNamespace(Name="Vehicle")
    return types.SimpleNamespace(Pawn=pawn, OakCharacter=character, PlayerCameraManager=camera(character),
                                 PlayerInput=types.SimpleNamespace(EnhancedActionMappings=MAPPINGS)), character


def _mapping(action: str, key: str) -> Any:
    return types.SimpleNamespace(Action=types.SimpleNamespace(Name=action), Key=types.SimpleNamespace(KeyName=key))


# The player's key list, a weapon key on each device and one key that draws nothing.
MAPPINGS = [_mapping("Action_Weapon1", "One"), _mapping("Action_NextWeapon", "Gamepad_FaceButton_Top"),
            _mapping("Action_Fire", "LeftMouseButton")]


def spot(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Any:
    return types.SimpleNamespace(X=x, Y=y, Z=z)


def camera(character: Any) -> Any:
    """The player's camera manager, looking through the eyes of `character`, at the origin, until a test sets its
    `mode` or `place`."""
    manager = types.SimpleNamespace(mode="Default", place=spot(), ViewTarget=types.SimpleNamespace(Target=character))
    manager.GetActorCameraMode = lambda _actor: manager.mode
    manager.GetCameraLocation = lambda: manager.place
    return manager


def arms(character: Any) -> Any:
    """The animation of `character`'s first-person arms, their eye, the Camera bone, at the origin."""
    mesh = types.SimpleNamespace(GetSocketLocation=lambda bone: spot() if bone == "Camera" else spot(1e6))
    return types.SimpleNamespace(OakCharacter=character, Outer=mesh)


def weapon(name: str = "OakWeapon_1") -> Any:
    return types.SimpleNamespace(Name=name)
