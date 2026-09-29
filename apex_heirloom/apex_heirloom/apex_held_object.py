"""Builds an object and hangs it on the first-person arms, drawn the way the arms are drawn.

Shared by the probes that put something in the player's hand (apex_hand_item.py, apex_hand_knife.py). The recipe,
proven in game on 2026-09-23 (cosmetics/heirloom/docs/enquetes/2026-09-23-objet-premier-plan.md):
1. the component is asked for unfinished, so what decides its drawing is set before the game first draws it;
2. it takes the arms' drawing flags, bGbxForeground above all: without it, the object is drawn at the world's field
   of view while the arms are drawn at their own, and it floats away from the hand; bReceivesDecals too: the arms
   refuse the ground's decals, a component takes them by default, and the dirt of some roads painted over the knife;
3. it is finished, then hung on its anchor keeping the transform it was given, relative to that anchor.
"""

from typing import Any, Callable

import unrealsdk
from mods_base import get_pc

from . import apex_first_person

# What decides how and where a primitive is drawn, named as in the game's field map of 2026-09-23; bReceivesDecals
# added on 2026-09-26 (cosmetics/heirloom/docs/enquetes/2026-09-26-couteau-pale.md).
DRAW_FLAGS = ("bGbxForeground", "FirstPersonPrimitiveType", "DepthPriorityGroup", "bUseViewOwnerDepthPriorityGroup",
              "ViewOwnerDepthPriorityGroup", "bOnlyOwnerSee", "bOwnerNoSee", "CastShadow", "bReceivesDecals")
# EAttachmentRule 0: the transform given at creation stays the one relative to the anchor.
KEEP_RELATIVE = 0
# ERelativeTransformSpace 0: the world's axes and units.
WORLD_SPACE = 0
# EComponentMobility 2, Movable: the only one that may follow a moving parent.
MOVABLE = 2
# unrealsdk.load_package loads nothing in BL4, a game mesh included: unrealsdk 3.2.0 hands the game's LoadPackage a
# string where it reads another structure. The engine's AssetRegistryHelpers.GetAsset loads from plain names, packages
# of our own container included (2026-09-23, cosmetics/heirloom/docs/enquetes/2026-09-23-modele-heirloom.md).
LOADER = "AssetRegistryHelpers"

Say = Callable[[str], None]


def transform(rotation: tuple[float, float, float, float], scale: tuple[float, float, float]) -> Any:
    x, y, z, w = rotation
    return unrealsdk.make_struct(
        "Transform",
        Rotation=unrealsdk.make_struct("Quat", X=x, Y=y, Z=z, W=w),
        Translation=unrealsdk.make_struct("Vector", X=0.0, Y=0.0, Z=0.0),
        Scale3D=unrealsdk.make_struct("Vector", X=scale[0], Y=scale[1], Z=scale[2]),
    )


def triple(vector: Any) -> str:
    return f"({vector.X:.3f}, {vector.Y:.3f}, {vector.Z:.3f})"


def copy_draw_flags(arms: Any, component: Any, say: Say) -> None:
    """Gives the object the arms' own drawing flags, each one said with what the arms and the object now hold."""
    for flag in DRAW_FLAGS:
        try:
            value = getattr(arms, flag)
        except Exception as exc:
            say(f"draw flag {flag}: the arms will not say ({exc!r})")
            continue
        try:
            setattr(component, flag, value)
            say(f"draw flag {flag}: arms {value}, object {getattr(component, flag)}")
        except Exception as exc:
            say(f"draw flag {flag}: arms {value}, the object refused it ({exc!r})")


def build(owner: Any, arms: Any, class_name: str, dress: Callable[[Any], None], placed: Any, say: Say) -> Any:
    """The object, finished and drawn as the arms are, or None; dress gives it its model before it is finished."""
    try:
        made = owner.AddComponentByClass(unrealsdk.find_class(class_name), True, placed, True)
    except Exception as exc:
        say(f"the character refused to build a component: {exc!r}")
        return None
    # The SDK may hand back output parameters after the return value.
    if isinstance(made, tuple):
        made = made[0] if made else None
    if made is None:
        say("the character handed back no component")
        return None
    for label, apply in (("its model", lambda: dress(made)), ("the right to move", lambda: made.SetMobility(MOVABLE))):
        try:
            apply()
        except Exception as exc:
            say(f"the object refused {label}: {exc!r}")
    copy_draw_flags(arms, made, say)
    try:
        owner.FinishAddComponent(made, True, placed)
    except Exception as exc:
        say(f"the character refused to finish the object: {exc!r}")
        remove(made, say)
        return None
    return made


def hang(component: Any, arms: Any, sockets: tuple[str, ...], say: Say) -> str | None:
    """Hangs the object on the first anchor the arms carry and accept; says which one answered."""
    names = apex_first_person.sockets(arms)
    for socket in sockets:
        if names and socket not in names:
            continue
        try:
            component.K2_AttachToComponent(arms, socket, KEEP_RELATIVE, KEEP_RELATIVE, KEEP_RELATIVE, False)
        except Exception as exc:
            say(f"the anchor {socket} refused the object: {exc!r}")
            continue
        try:
            component.SetVisibility(True, True)
        except Exception as exc:
            say(f"the object refused to be shown: {exc!r}")
        return socket
    say("no anchor took the object")
    return None


def remove(component: Any, say: Say) -> None:
    if component is None:
        return
    for label, call in (("detach", lambda: component.K2_DetachFromComponent(0, 0, 0, True)),
                        ("remove", lambda: component.K2_DestroyComponent(component.GetOwner()))):
        try:
            call()
        except Exception as exc:
            say(f"the object refused to {label}: {exc!r}")


def measure(arms: Any, component: Any, socket: str, say: Say) -> None:
    """How far the anchor sits from the eye and how big everything really is, in the world."""
    try:
        anchor = arms.GetSocketTransform(socket, WORLD_SPACE)
        eye = get_pc().PlayerCameraManager.GetCameraLocation()
        spot = anchor.Translation
        distance = ((spot.X - eye.X) ** 2 + (spot.Y - eye.Y) ** 2 + (spot.Z - eye.Z) ** 2) ** 0.5
        say(f"anchor {socket}: {distance:.1f} cm from the eye, scale {triple(anchor.Scale3D)}; "
            f"arms scale {triple(arms.K2_GetComponentScale())}; "
            f"object scale {triple(component.K2_GetComponentScale())}")
    except Exception as exc:
        say(f"the sizes could not be read: {exc!r}")


def asset_data(class_name: str, path: str) -> Any:
    """The names the engine's loader reads: package, its folder, the asset, and the asset's class."""
    package, name = path.rsplit(".", 1)
    kind_package, kind = unrealsdk.find_class(class_name)._path_name().rsplit(".", 1)
    return unrealsdk.make_struct("AssetData", PackageName=package, PackagePath=package.rsplit("/", 1)[0],
                                 AssetName=name,
                                 AssetClassPath=unrealsdk.make_struct("TopLevelAssetPath", PackageName=kind_package,
                                                                      AssetName=kind))


def load(class_name: str, path: str, say: Say) -> Any:
    """An asset by its full path, loaded from the game's archives if nothing has loaded it yet; None if it cannot."""
    try:
        return unrealsdk.find_object(class_name, path)
    except ValueError:
        pass
    try:
        # What GetAsset returns is not relied on (it came back with its struct on 2026-09-23): the object is found
        # again by its path, the same way whatever the loader gives.
        unrealsdk.find_class(LOADER).ClassDefaultObject.GetAsset(asset_data(class_name, path))
        found = unrealsdk.find_object(class_name, path)
    except Exception as exc:
        say(f"{path} could not be loaded: {exc!r}")
        return None
    say(f"{path} was not loaded yet; loaded it")
    return found
