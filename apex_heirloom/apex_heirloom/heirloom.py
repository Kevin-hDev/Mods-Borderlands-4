"""Our heirloom in the player's right hand: our knife, from our own container, and our animations for empty hands.

Why, 2026-09-23 (cosmetics/heirloom/docs/enquetes/2026-09-23-modele-heirloom.md): Kevin chose to ship our own knife
model, cut from the game's grenade knife (cosmetics/heirloom/outils/modele/heirloom_build.py) and loaded through the
engine's loader (apex_held_object.load). It is cooked with the engine's default material, the engine's grid, and dressed
in its own look when placed (apex_own_look.py). Why its own look, 2026-09-26
(cosmetics/heirloom/docs/enquetes/2026-09-26-essai-du-mod.md): it borrowed the materials of a Jakobs grenade the game
had built, and stayed in the grid when none was there yet, or ever; Kevin chose to keep his grenade's look for good,
made from the game's files with no grenade. Hung on the right hand, its Y reversed (the mirror image of the game's
left-hand knife), held by its handle as Wraith holds her kunai (apex_fit.py). It shows only while no weapon is in
hand, the hands are not climbing and the camera looks through the player's eyes (apex_holster_follow.py); as the weapon
goes away, both hands rise from under the screen with it (apex_draw.py), and as it comes back they go down with it
(apex_put_away.py).
Why our own animations, 2026-09-26 (cosmetics/heirloom/docs/enquetes/2026-09-25-listes-d-animations.md, essai 6): the
mod gives our list to empty hands (apex_anim_list.py); the arms play it from the next weapon change, and the knife
comes with them. Switched off, our list is taken back and the knife leaves with our animations, at the next weapon
change, as Kevin chose (docs/mokup/menu_mods/decisions.md, 2026-09-26). What the player sets (heirloom_settings.py)
applies from the next weapon change too: the mode's list is given at once, and the game reads it then; the knife's
size and the draw's timing are read at each weapon change.
Why several heirlooms, 2026-09-29 (docs/mokup/menu_mods/decisions.md): Kevin chose that the menu offers the knife and
the axe, whose animations, model, hold and looks differ. The chosen heirloom's list goes to empty hands, its draw and
put-away play, its model, skin and glow go on (apex_wear.py) and its hold applies, each as the mod's catalog sets it
(heirloom_catalog.py, generated from their heirloom.json); it shows only while the arms play its animations: chosen
again, from the next weapon change. The player's choices are made through heirloom_choices.py.
Why an inspection, 2026-09-29 (cosmetics/heirloom/docs/heirloom.md, section 20): Kevin wants a key that makes the
heirloom's flourish in the hand, as in Apex; its key (inspect_keys.py) plays the chosen heirloom's (apex_inspect.py)
while it shows in the empty hand.
"""

import types
from typing import Any

from mods_base import get_pc
from unrealsdk import logging
from unrealsdk.unreal import WeakPointer

from . import apex_anim_list as anim_list
from . import apex_draw, apex_first_person, apex_inspect, apex_put_away
from . import heirloom_settings
from . import apex_held_object as held_object
from . import apex_holster_follow as holster_follow
from . import apex_fit
from . import apex_wear

PREFIX = "[ApexHeirloom]"
COMPONENT_CLASS = "StaticMeshComponent"
SOCKET = "R_Hand_Object"
NO_TURN = (0.0, 0.0, 0.0, 1.0)
MIRRORED = (1.0, -1.0, 1.0)

# The knife, the character and arms holding it, whether it is on its way out, the fit and timing last applied (the
# draw and the put-away read `timing` as they play), and its inspection, while it hangs.
STATE = types.SimpleNamespace(component=None, owner=None, arms=None, retiring=False, fit=None,
                              timing=heirloom_settings.timing(), inspect=None)


def say(text: str) -> None:
    logging.info(f"{PREFIX} {text}")


def _alive(pointer: Any) -> Any:
    return pointer() if pointer is not None else None


def held() -> Any:
    return _alive(STATE.component)


def holds_for(owner: Any) -> bool:
    """Whether the knife hangs on this character's hands."""
    return held() is not None and _alive(STATE.owner) == owner


def load(class_name: str, path: str) -> Any:
    return held_object.load(class_name, path, say)


def drop_knife() -> None:
    """The knife out of the hands it hangs on, and its watch stopped; our list stays."""
    holster_follow.stop()
    component = held()
    STATE.component, STATE.owner, STATE.inspect = None, None, None
    held_object.remove(component, say)


def remove() -> None:
    drop_knife()
    # Leaving after a switch-off, the list was taken back then: the one in the hands now may be another file's, given
    # since (Heirloom switched on after Apex Heirloom, in the same session), and is not ours to take (2026-09-27).
    if not STATE.retiring:
        anim_list.remove(say)
    STATE.retiring = False


def playing_ours() -> bool:
    arms = _alive(STATE.arms)
    return arms is not None and anim_list.played(arms.GetAnimInstance(), heirloom_settings.chosen_heirloom(), say)


def gone() -> None:
    """The knife left the hands: switched off, the heirloom goes now."""
    if STATE.retiring:
        remove()
        say("heirloom off: our knife removed, the game's animations play")


def switch_off() -> None:
    anim_list.remove(say)
    STATE.retiring = True
    if holster_follow.holding():
        say("heirloom off: the knife leaves with our animations, at the next weapon change")
    else:
        gone()


def give_list(mode: str | None = None) -> bool:
    """The chosen heirloom's list of the chosen mode, or of `mode`, to empty hands."""
    return anim_list.add(load, heirloom_settings.chosen_heirloom(), mode or heirloom_settings.chosen_mode(), say)


def switch_on() -> None:
    """Back on before the knife left: our list again, and it stays."""
    if held() is not None and STATE.retiring and give_list():
        STATE.retiring = False


def _choice() -> tuple[str, str, int]:
    """The chosen heirloom, its skin and the glow's force, as the menu sets them."""
    return (heirloom_settings.chosen_heirloom(), heirloom_settings.chosen_skin(), heirloom_settings.chosen_force())


def dress(component: Any) -> None:
    """The chosen heirloom's chosen skin on the component, its glow at the chosen force."""
    apex_wear.dress(component, *_choice(), load, say)


def rewear(component: Any) -> bool:
    """The chosen heirloom's model, skin and hold on the component; False, said, when its model is not in the game."""
    if not apex_wear.wear(component, *_choice(), load, say):
        return False
    weapon_changed()
    return True


def weapon_changed() -> None:
    """At each weapon change, before the draw: the heirloom's size and the draw's timing as the menu sets them."""
    fit = heirloom_settings.fit()
    component = held()
    if component is not None and fit != STATE.fit:
        apex_fit.apply(component, fit, say)
        STATE.fit = fit
    vars(STATE.timing).update(vars(heirloom_settings.timing()))


def show(owner: Any) -> bool:
    """Our list to empty hands and our knife in the right hand of `owner`, the player's character; False, said, when
    something is missing. A knife still on another character's hands leaves them first."""
    if held() is not None:
        drop_knife()
    arms = apex_first_person.mesh(owner)
    if arms is None:
        say("the first-person arms were not found")
        return False
    if not give_list():
        return False
    STATE.arms, STATE.retiring = WeakPointer(arms), False
    model = apex_wear.model(heirloom_settings.chosen_heirloom(), load, say)
    if model is None:
        anim_list.remove(say)
        return False
    say(f"our model is loaded: {model._path_name()}")
    component = held_object.build(owner, arms, COMPONENT_CLASS, lambda made: made.SetStaticMesh(model),
                                  held_object.transform(NO_TURN, MIRRORED), say)
    if component is None:
        anim_list.remove(say)
        return False
    STATE.component, STATE.owner = WeakPointer(component), WeakPointer(owner)
    try:
        if not _hang(component, arms, owner):
            remove()
            return False
    except Exception:
        # Hung and shown before its watch runs, a knife left by an error would stay on screen, over the weapon too,
        # and holds_for would stop every new try (audit of 2026-09-26).
        remove()
        raise
    say("our knife is in the right hand, with our animations from the next weapon change")
    return True


def inspect() -> None:
    """The chosen heirloom's inspection, at a press of its key: only while it shows in the empty hand."""
    arms, inspection = _alive(STATE.arms), STATE.inspect
    if arms is None or inspection is None or not holster_follow.in_empty_hand():
        return
    inspection.play(arms.GetAnimInstance())


def _animation(name: str) -> str:
    """One of the chosen heirloom's animations, read as it plays: the heirloom chosen since the knife was hung."""
    return anim_list.animation(heirloom_settings.chosen_heirloom(), name)


def _hang(component: Any, arms: Any, owner: Any) -> bool:
    """The knife built for `owner` dressed, hung, fitted and watched; False, said, when no anchor takes it."""
    dress(component)
    if held_object.hang(component, arms, (SOCKET,), say) is None:
        return False
    held_object.measure(arms, component, SOCKET, say)
    STATE.fit = None
    weapon_changed()
    draw = apex_draw.Draw(lambda: load("AnimSequence", _animation(apex_draw.DRAW)), STATE.timing, WeakPointer, say)
    put_away = apex_put_away.PutAway(lambda: load("AnimSequence", _animation(apex_put_away.PUT_AWAY)), STATE.timing,
                                     WeakPointer, say)
    STATE.inspect = apex_inspect.Inspect(heirloom_settings.chosen_heirloom, lambda: _alive(STATE.owner).bIsCrouched,
                                         lambda name: load("AnimSequence", _animation(name)), WeakPointer, say)
    holster_follow.follow(held, owner, say, draw, put_away,
                          camera=lambda: getattr(get_pc(), "PlayerCameraManager", None), played=playing_ours,
                          gone=gone, weapon_changed=weapon_changed, inspect=STATE.inspect)
    return True
