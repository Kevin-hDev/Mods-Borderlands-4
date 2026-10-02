"""The left hand raised while the beam fires: a pose played on the first-person arms and on the body seen from
outside, the way the game plays its grenades.

Read in the game's files, then seen in game on 2026-10-01 for the arms (docs/attaque-rayon/enquetes/
2026-10-01-main-gauche.md): the arms keep the slot Offhand for the left hand; a pose played there takes the left arm
alone and switches the weapon to its one-handed hold by itself. The pose is a still image: the fades raise and lower
the hand. The body's graph has the same slot, taking the same left arm (read in its files on 2026-10-01, not seen in
game: docs/attaque-rayon/enquetes/2026-10-01-troisieme-personne.md). Both are played at every shot, whatever the
view: the body is what a shadow and another player show.

Both poses are ours and come in one container, built by docs/attaque-rayon/outils/pose_build.py (the arms) and
body_build.py (the body); test_pose_container.py, beside them, checks they name the same animations. The body's
pose is built on the arms' skeleton, its left arm's turns worked out for the body: the game matches the bones by
name.

The gesture is only what the player sees: nothing here may stop a shot. On a mesh that cannot play its pose the arm
stays where it is, said once.
"""

from typing import Any

from unrealsdk import unreal

from . import game_assets, hand, report

KIND = "AnimSequence"
ANIMATION = "/Game/PlayerCharacters/_Shared/Animation/1st/BeamAtk/AS_Beam_Hold.AS_Beam_Hold"
CONTAINER = "000_BenefixOhmAttack_999_P"
BODY_ANIMATION = "/Game/PlayerCharacters/_Shared/Animation/1st/BeamAtk/AS_Beam_Body.AS_Beam_Body"
# The slot of the game's own grenades. On the arms: weapon out, weapon stowed and running all hold in it (trial 2).
SLOT = "Offhand"
RAISE_S, LOWER_S = 0.2, 0.25
# Enough turns of a short pose for an hour's shot, the energy being allowed never to run out.
TURNS = 3600
# What takes the pose: its name in the log, its mesh on the character, the animation played on it.
PARTS = (("arms", hand.arms, ANIMATION), ("body", hand.body, BODY_ANIMATION))

# Each animation instance and the montage it plays, kept weakly: the game owns both.
_playing: list[tuple[Any, Any]] = []


def _play(mesh: Any, path: str) -> tuple[Any, Any]:
    if mesh is None:
        raise ValueError("no such mesh on the character")
    animation = mesh.GetAnimInstance()
    montage = animation.PlaySlotAnimationAsDynamicMontage(
        Asset=game_assets.load(KIND, path), SlotNodeName=SLOT, BlendInTime=RAISE_S, BlendOutTime=LOWER_S,
        InPlayRate=1.0, LoopCount=TURNS, BlendOutTriggerTime=-1.0, InTimeToStartMontageAt=0.0)
    # The SDK may give output parameters after the return value.
    if isinstance(montage, tuple):
        montage = montage[0] if montage else None
    if montage is None:
        raise ValueError("the game played nothing")
    return unreal.WeakPointer(animation), unreal.WeakPointer(montage)


def raise_hand(character: Any) -> tuple[str, ...]:
    """Starts the pose on the character's arms and body; names the parts that took it."""
    lower()
    raised = []
    for name, mesh_of, path in PARTS:
        try:
            _playing.append(_play(mesh_of(character), path))
            raised.append(name)
        except Exception as error:
            report.error_once(f"gesture:raise:{name}",
                              f"the left hand stays down on the {name} (is {CONTAINER} in the game's Paks?): {error!r}")
    return tuple(raised)


def lower() -> None:
    """Fades the pose out wherever it still plays; another montage of the game's is left alone."""
    held = _playing[:]
    _playing.clear()
    for animation_of, montage_of in held:
        animation, montage = animation_of(), montage_of()
        if animation is None or montage is None:
            continue
        try:
            animation.Montage_Stop(LOWER_S, montage)
        except Exception as error:
            report.error_once("gesture:lower", f"the left hand's pose could not be stopped: {error!r}")
