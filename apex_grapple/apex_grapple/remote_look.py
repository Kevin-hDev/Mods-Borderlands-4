"""Another player's grapple gun, seen from outside on that player's character: the body's pistol, the holster and the
pistol in it, the ropes and hooks, the body's gestures, each as that player chose them (look_code.py; Kevin, 17
October 2026: "chaque joueur conserve son grappin").

The same pieces, timings and gestures as the player's own seen from behind (look_play.py), built on the other
character: look_gun's body pieces, look_shots' places drawn by look_shots.draw, look_timing's hook, look_moves' poses
played by a look_gestures.Gestures of its own on the body only. The other player's game says when the rope goes and
when it lets go (coop_messages.py, coop_relay.py); the hook bites when its flight is over, as on that player's game.
Gone with the character: a new one gets new pieces, the old ones forgotten, never called.
"""

import math
from typing import Any

from unrealsdk.unreal import WeakPointer

from . import (game, look_assets, look_gestures, look_gun, look_hook, look_load, look_moves, look_muzzle, look_outfit,
               look_play, look_rope, look_settings, look_shots, look_timing, look_view, look_weapon, release, settings)

ROLES = (look_gun.BODY_PISTOL, look_gun.HOLSTERED, look_gun.HOLSTER)
NS = look_timing.NS_PER_S


def weapon(character: Any) -> str | None:
    """The right hand's weapon as its gestures stow it; None when the other game does not tell this one."""
    try:
        return look_weapon.kind(character)
    except Exception:
        return None


class GunGrapple:
    def __init__(self, character: Any, look: Any, hunter: str) -> None:
        self.pointer = WeakPointer(character)
        self.look = look
        rope_look, thickness = look.rope_look, look.rope_thickness
        colour = look.rope_colour if look_rope.glows(rope_look) else look_assets.COLOUR_AT_FIRST
        objects = look_load.fetch(look_gun.wanted(hunter) + look_rope.wanted(rope_look, colour) + look_hook.wanted())
        self.gun = look_gun.Gun(character, None, objects, hunter, ROLES)
        count = look_rope.count(rope_look, thickness, float(settings.grapple_range.value))
        self.places = [look_shots.Place(character, rope_look, thickness, count, objects, colour)
                       for _ in range(look_shots.PLACES)]
        self.gestures = look_gestures.Gestures()
        self.current: look_shots.Place | None = None
        self.moves: look_moves.Moves | None = None
        self.kind: str | None = None
        self.hand: tuple | None = None

    def character(self) -> Any:
        return self.pointer()

    def busy(self) -> bool:
        return self.moves is not None or any(place.shot is not None for place in self.places)

    def _muzzle(self) -> tuple:
        return look_muzzle.on_piece(self.gun.pieces[look_gun.BODY_PISTOL],
                                    look_assets.PIECES[look_gun.BODY_PISTOL]["muzzle_cm"])

    def start(self, anchor: tuple, flight_s: float, now_ns: int) -> None:
        character = self.pointer()
        if character is None:
            return
        self.release(now_ns)
        free = [place for place in self.places if place.shot is None]
        place = free[0] if free else min(self.places, key=lambda one: one.shot.released_ns or 0)
        place.hide()
        look = self.look
        place.slack, place.size = look.rope_movement, look.hook_size
        place.rope.light(look_assets.ROPE_LIGHTS[look.rope_light], look.rope_colour, look.glow_face)
        place.shot = look_timing.Shot(now_ns, int(flight_s * NS), tuple(anchor), look_hook.length(look.hook_size),
                                      look_assets.HOOK_SUNK_CM, float(settings.hook_speed.value))
        self.current = place
        self.moves = look_moves.Moves(look_play.ENTRY_S, look_play.EXIT_S, now_ns, float(settings.longest_pull.value))
        self.kind = weapon(character)
        self.hand = self._muzzle()

    def release(self, now_ns: int) -> None:
        if self.current is not None and self.current.shot is not None and self.hand is not None:
            look_timing.release(self.current.shot, self.hand, now_ns)
        self.current = None
        if self.moves is not None:
            self.moves.end(now_ns)

    def tick(self, now_ns: int) -> None:
        character = self.pointer()
        if character is None:
            return
        hand = self.hand = self._muzzle()
        current = self.current
        pull = None
        if current is not None and current.shot is not None and current.shot.released_ns is None:
            shot = current.shot
            if shot.planted is None and now_ns >= shot.fired_ns + shot.flight_ns:
                look_timing.catch(shot, hand, now_ns)
                gap = math.dist(game.location(character), shot.anchor)
                near = release.arrival_for_shot(float(settings.arrival_distance.value), gap)
                self.moves.catch(now_ns, gap, near, float(settings.pull_speed_cap.value))
            if shot.planted is not None:
                here = game.location(character)
                pull = look_moves.Pull(tuple(a - h for a, h in zip(shot.anchor, here)),
                                       game.velocity(character.CharacterMovement))
        for place in self.places:
            if place.shot is not None and not look_shots.draw(place, hand, now_ns) and place is self.current:
                self.current = None
        holding = any(place.shot is not None for place in self.places)
        if self.moves is not None:
            pose = self.moves.frame(now_ns, pull)
            self.gestures.body(character.Mesh.GetAnimInstance(), pose, self.kind, holding)
            if pose.left[0] == look_moves.GONE and not holding and not self.gestures.busy():
                self.moves = None
        holster = (self.look.holster == look_settings.WITH
                   and not look_outfit.covers_hip(character, quiet=True))
        self.gun.show(look_gun.shown(look_view.THIRD, False, holding, holster))

    def drop(self) -> None:
        """Its pieces removed while the character still holds them; forgotten in any case."""
        alive = self.pointer() is not None
        places, gun, gestures = self.places, self.gun, self.gestures
        self.places, self.current, self.moves = [], None, None
        if not alive:
            return
        failed = None
        for step in [gestures.stop, gun.destroy] + [place.destroy for place in places]:
            try:
                step()
            except Exception as error:
                failed = failed or error
        if failed is not None:
            raise failed
