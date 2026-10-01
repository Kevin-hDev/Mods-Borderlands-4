"""Shows the heirloom only while no weapon is in hand, the hands are not climbing and the camera looks through the
player's eyes: the one place its visibility is set, following each weapon change and each frame of the arms'
animation.

Why, 2026-09-23 (cosmetics/heirloom/docs/enquetes/2026-09-23-modele-heirloom.md): our knife hangs on R_Hand_Object, the
anchor the weapon takes too. Left shown, it sat on top of the drawn weapon and hid the sight when aiming (Kevin's
screenshots). The heirloom is for the holstered hand only. The weapon change and the empty slot are read the way
Holster Your Weapon reads them (its code, 2026-09-23): the first-person animation's OnWeaponChanged, and
ActiveWeapons.Slots[0].Weapon, None while holstered.
Why, 2026-09-24 (cosmetics/heirloom/docs/heirloom.md, section 15): on a ladder, over a ledge and in Apex Movement's
wall climb the arms play the game's climbing animations, where the hand holds nothing; Kevin wants them without the
knife (apex_climb_watch.py). Both reasons are held here, so the end of a climb cannot show the knife over a weapon.
Why, 2026-09-25 (cosmetics/heirloom/docs/heirloom.md, the defect under its state): in third person and in a vehicle
the game no longer shows the first-person arms, but the knife hung on them stayed at the neck; Kevin wants no heirloom
out of first person (apex_camera_view.py). A camera out of the eyes counts as a climb: the knife goes without its
put-away and comes back without its draw.
The weapon put away starts the heirloom's draw (apex_draw.py); the weapon back starts its put-away (apex_put_away.py),
and the heirloom stays shown until the hands are down. A switch between two weapons, which passes through "no
weapon" for a few milliseconds, neither draws nor puts away: the heirloom goes at once and its draw stops.
Why, 2026-09-26 (cosmetics/heirloom/docs/enquetes/2026-09-25-listes-d-animations.md, essai 6): our animations no
longer replace the game's; the empty hands play them only once the game has read our list, at a weapon change
(apex_anim_list.py). Kevin chose that the heirloom comes and goes with them (docs/mokup/menu_mods/decisions.md,
2026-09-26): it shows only while the arms play our animations, read while the hands are empty and kept while they go
down with it. They may come a few frames after the weapon change event: the draw still plays within LATE_S.
Why, 2026-09-26 (docs/mokup/menu_mods/decisions.md): a setting changed in the menu applies from the next weapon change;
`weapon_changed` is called at each one, before the draw starts, so that it plays with what the player set.
Why, 2026-09-29 (Kevin's choice): the game's depth of field is off while the heirloom is shown, and back when it is
hidden or the watch stops (apex_depth_of_field.py says why); set here, with the visibility it follows.
Why, 2026-09-29 (cosmetics/heirloom/docs/heirloom.md, section 20): only drawing the weapon stops the heirloom's
inspection before its end (Kevin); it stops at once as its draw does, as the weapon comes back and whenever the
heirloom is hidden (apex_inspect.py). A key plays it only while the heirloom shows in the empty hand (in_empty_hand).
"""

import time
import types
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from unrealsdk.hooks import Type, add_hook, has_hook, remove_hook

from . import apex_camera_view as camera_view
from . import apex_climb_watch as climb_watch
from . import apex_depth_of_field as depth_of_field

Say = Callable[[str], None]
ARMS_ANIMATION = "/Game/PlayerCharacters/_Shared/Animation/BPAnim_Player_1st.BPAnim_Player_1st_C"
WEAPON_HOOK = f"{ARMS_ANIMATION}:OnWeaponChanged"
# Each frame of the arms' animation, on the game's thread (mouvements_borderlands_4.md, section 5 bis); Holster Your
# Weapon listens to it too.
FRAME_HOOK = f"{ARMS_ANIMATION}:BlueprintUpdateAnimation"
# Named after the package: Apex Heirloom switched off while its knife leaves, and Heirloom switched on in the same
# session, each watch removes and adds its own hooks, never the other file's (2026-09-27, separate files).
IDENTIFIER = f"{__package__}.apex_holster_follow"
# The game's switch between two weapons passes through "no weapon" for 20 to 64 ms (apex_weapon_calls.py, 2026-09-25):
# a heirloom shown for less than this was only a switch.
SWITCH_S = 0.15
# Our animations may be read a few frames after the weapon change event (their order is not measured); a draw started
# this long after the weapon went still starts with the hands under the screen.
LATE_S = 0.3


class Draw(Protocol):
    def play(self, arms_animation: Any) -> None: ...

    def cancel(self, arms_animation: Any) -> None: ...


class Inspect(Protocol):
    def cancel(self, arms_animation: Any) -> None: ...


class PutAway(Protocol):
    def start(self, arms_animation: Any, weapon: Any) -> float | None: ...

    def finish(self) -> None: ...

    def cancel(self, arms_animation: Any) -> None: ...


@dataclass
class Watch:
    holstered: bool
    # Why the hands are out of the player's sight, "" while they are not: a climb, or the camera out of his eyes.
    away: str = ""
    shown_at: float = 0.0
    # While the hands go down with the heirloom, it stays shown until then.
    leaving_until: float | None = None
    # Whether the hands play our animations: read while they are empty, kept while they go down with the heirloom.
    ours: bool = True
    holstered_at: float = float("-inf")
    # Whether the hands held it at the last turn: its leaving is told once, seen or hidden by a climb or the camera
    # (audit of 2026-09-26: switched off while hidden, the knife was never taken away).
    was_holding: bool = False

    def holding(self) -> bool:
        """Whether the hands hold the heirloom, seen or not: empty and playing our animations, or going down."""
        return (self.holstered or self.leaving_until is not None) and self.ours

    def shown(self) -> bool:
        return self.holding() and not self.away


# `finish` shows the hidden weapon again if the watch stops while the hands go down; `watch` is the watch running.
STATE = types.SimpleNamespace(finish=None, watch=None)


def weapon_in_hand(owner: Any) -> bool:
    return owner.ActiveWeapons.Slots[0].Weapon is not None


def show(component: Any, watch: Watch, why: str, say: Say) -> None:
    component.SetVisibility(watch.shown(), True)
    say(f"{why}: heirloom {'shown' if watch.shown() else 'hidden'}")
    depth_of_field.follow(watch.shown(), say)


def follow(held: Callable[[], Any], owner: Any, say: Say, draw: Draw | None = None, put_away: PutAway | None = None,
           clock: Callable[[], float] = time.perf_counter, camera: Callable[[], Any] = lambda: None,
           played: Callable[[], bool] = lambda: True, gone: Callable[[], None] = lambda: None,
           weapon_changed: Callable[[], None] = lambda: None, inspect: Inspect | None = None) -> None:
    """Shows or hides what `held` gives now, at each weapon change of `owner`, as its hands climb, as `camera` (the
    player's camera manager) leaves his eyes and as the arms start or stop playing our animations (`played`), until
    stop(); `draw` plays as the weapon put away shows the heirloom, `put_away` as the weapon back takes it away;
    `gone` is called each time the heirloom leaves the hands: a weapon in them, or the game's animations;
    `weapon_changed` at each weapon change, first; `inspect` stops with the draw. Hidden by a climb or the camera,
    the hands still hold it."""
    stop()
    watch = Watch(holstered=not weapon_in_hand(owner), shown_at=clock(), ours=played())
    watch.was_holding = watch.holding()
    STATE.watch = watch
    component = held()
    if component is not None:
        show(component, watch, "no weapon in hand" if watch.holstered else "weapon in hand", say)

    def current(obj: Any) -> Any:
        """The heirloom, when `obj` is the player's arms animation; the watch stops once the heirloom is gone, seen from
        any arms: gone with its character, it would wait for arms that never come back."""
        component = held()
        if component is None:
            stop()
            return None
        return component if getattr(obj, "OakCharacter", None) is owner else None

    def still(obj: Any) -> None:
        """The heirloom's own gestures stopped at once: it leaves the empty hand."""
        for gesture in (draw, inspect):
            if gesture is not None:
                gesture.cancel(obj)

    def leave(obj: Any, weapon: Any, now: float) -> None:
        if put_away is None or now - watch.shown_at < SWITCH_S:
            return
        still(obj)
        lasting = put_away.start(obj, weapon)
        if lasting is not None:
            watch.leaving_until = now + lasting
            STATE.finish = put_away.finish

    def cut(obj: Any) -> None:
        if watch.leaving_until is not None and put_away is not None:
            put_away.cancel(obj)
        watch.leaving_until, STATE.finish = None, None

    def turned(obj: Any, component: Any, was_shown: bool, why: str, now: float, draws: bool) -> None:
        show(component, watch, why, say)
        if watch.shown() and not was_shown:
            watch.shown_at = now
            if draws and draw is not None:
                draw.play(obj)
        if was_shown and not watch.shown():
            still(obj)
        holding = watch.holding()
        if watch.was_holding and not holding:
            gone()
        watch.was_holding = holding

    def changed(obj: Any, args: Any, _ret: Any, _func: Any) -> None:
        component = current(obj)
        if component is None:
            return
        weapon_changed()
        now, was_shown = clock(), watch.shown()
        cut(obj)
        watch.holstered = args.NewWeapon is None
        if watch.holstered:
            watch.holstered_at, watch.ours = now, played()
        if not watch.holstered and was_shown and not watch.away:
            leave(obj, args.NewWeapon, now)
        why = ("no weapon in hand" if watch.holstered else
               "weapon back, the hands go down" if watch.leaving_until is not None else "weapon in hand")
        turned(obj, component, was_shown, why, now, draws=True)

    def frame(obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
        component = current(obj)
        if component is None:
            return
        now = clock()
        if watch.leaving_until is not None and now >= watch.leaving_until and put_away is not None:
            put_away.finish()
            watch.leaving_until, STATE.finish = None, None
            turned(obj, component, True, "hands down", now, draws=False)
            component = current(obj)
            if component is None:
                return
        if watch.holstered and watch.leaving_until is None and played() != watch.ours:
            was_shown, watch.ours = watch.shown(), not watch.ours
            turned(obj, component, was_shown, "our animations" if watch.ours else "the game's animations", now,
                   draws=now - watch.holstered_at <= LATE_S)
            component = current(obj)
            if component is None:
                return
        climb = climb_watch.climbing(owner.CharacterMovement, obj, say)
        outside = "" if climb else camera_view.outside(camera(), owner, obj, say)
        away = f"climbing ({climb})" if climb else f"camera {outside}" if outside else ""
        if away != watch.away:
            was_shown = watch.shown()
            if away:
                cut(obj)
            ended, watch.away = watch.away, away
            turned(obj, component, was_shown, away or f"{ended} over", now, draws=False)

    add_hook(WEAPON_HOOK, Type.POST, IDENTIFIER, changed)
    add_hook(FRAME_HOOK, Type.POST, IDENTIFIER, frame)


def holding() -> bool:
    """Whether the watched hands hold the heirloom now, seen or not."""
    return STATE.watch is not None and STATE.watch.holding()


def in_empty_hand() -> bool:
    """Whether the heirloom shows in the empty hand now: not while it goes down with the weapon coming back."""
    watch = STATE.watch
    return watch is not None and watch.holstered and watch.shown()


def stop() -> None:
    finish = STATE.finish
    STATE.finish, STATE.watch = None, None
    if finish is not None:
        finish()
    depth_of_field.give_back()
    for path in (WEAPON_HOOK, FRAME_HOOK):
        if has_hook(path, Type.POST, IDENTIFIER):
            remove_hook(path, Type.POST, IDENTIFIER)
