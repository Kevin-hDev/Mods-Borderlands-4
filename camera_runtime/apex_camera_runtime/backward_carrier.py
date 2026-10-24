"""Own the private backward-run carrier for one live third-person body.

Moved from Omni Sprint (animation.py) on 2026-10-09: the omni direction unit (omni_direction.py) now decides
when it may fill the sprint's backward slot, so one writer owns that slot (sprint_slot.py).
"""

import re

from . import backward_carrier_assets as animation_assets

BACK_KEY = 'AnimSet.Player.3rd.Run_B'
SPRINT_KEY = 'AnimSet.Player.3rd.BS_Sprint'
# Vex, Rafa and the Harmonica DLC hunter (CorpoHacker) play BPAnim_Player_3rd_C; Harlow plays BPAnim_Player_3rd_Grav_C, Amon and C4sh
# BPAnim_Player_3rd_Paladin_C, with the same sprint node and keys (read in game on 2026-10-24). The name only says
# it is a hunter's third-person body: the node, player and key checks below are what guard the slot.
BODY_CLASS = re.compile(r'BPAnim_Player_3rd(_[A-Za-z0-9]+)?_C')
NODE_CLASS = 'GbxAnimNode_Locomotion'
PLAYER_CLASS = 'GbxAnimNode_BlendSpacePlayer'
GROUND_MODE = 1
RETRY_NS = 5_000_000_000
# Put-backs said one by one, then no more: a game that empties the slot every frame must not flood the log.
MAX_SAID = 5


def players(anim):
    name = str(anim.Class.Name)
    if not BODY_CLASS.fullmatch(name):
        raise ValueError(f'Unsupported player animation class {name[:64]}')
    node = anim.GbxAnimGraphNode_Locomotion_2
    if str(node._type.Name) != NODE_CLASS:
        raise ValueError('Unsupported locomotion node')
    found = node.BlendSpacePlayers
    if len(found) != 2:
        raise ValueError('Unexpected animation player count')
    for index, key in enumerate((SPRINT_KEY, BACK_KEY)):
        player = found[index]
        tag = player.AnimAssetKey
        if (str(player._type.Name) != PLAYER_CLASS or str(tag._type.Name) != 'GameplayTag'
                or str(tag.TagName) != key):
            raise ValueError('Unexpected animation player key')
    return found


class BackwardCarrier:
    def __init__(self, weak, build, emit):
        self.weak, self.build, self.emit = weak, build, emit
        self.owner = self.target = None
        self.source_id = self.owner_id = 0
        self.retry_at = 0
        self.blocked_id = 0
        self.blocked_owner_id = 0
        self.layout_blocked_id = 0
        # The body's last forward sprint, held weakly, and that body: see _source.
        self.last_source = None
        self.last_owner_id = 0
        self.put_back = 0

    def _source(self, forward, owner_id):
        """The forward sprint, or this body's last one while the game leaves it empty.

        A weapon change empties both players, and the game fills only the one it plays: sprinting backward, the
        backward one, which has no resource of its own, so the forward one stays empty until the sprint starts
        again (watch of 2026-10-24, docs/investigations/omni_sprint/2026-10-24-fige-amon-harlow-c4sh.md).
        """
        if owner_id != self.last_owner_id:
            self.last_source, self.last_owner_id = None, owner_id
        source = forward.BlendSpace
        last = self.last_source() if self.last_source is not None else None
        if source is None:
            return last
        if not animation_assets.same(source, last):
            self.last_source = self.weak(source)
        return source

    def _clear(self):
        self.owner = self.target = None
        self.source_id = self.owner_id = 0

    def stop(self):
        if self.owner is None:
            return
        owner, target = self.owner(), self.target()
        if owner is None:
            self._clear()
            self.emit('backward carrier released: owner expired')
            return
        player = players(owner)[1]
        current = player.BlendSpace
        if current is None:
            self._clear()
            return
        if target is None or not animation_assets.same(current, target):
            self._clear()
            self.emit('backward carrier released: another resource now owns the slot')
            return
        player.BlendSpace = None
        if player.BlendSpace is not None:
            raise ValueError('Backward carrier restoration failed')
        self._clear()
        self.emit('backward carrier restored')

    def update(self, character, anim, now_ns):
        if character is None or anim is None:
            self.stop()
            return
        owner_id = int(anim._get_address())
        if self.blocked_owner_id and owner_id != self.blocked_owner_id:
            self.blocked_id = self.blocked_owner_id = 0
            self.retry_at = 0
        if owner_id == self.layout_blocked_id:
            return
        if self.owner is not None and owner_id != self.owner_id:
            self.stop()
        movement = character.CharacterMovement
        sprinting = (movement.bIsSprinting and anim.bIsSprinting
                     and movement.MovementMode == GROUND_MODE)
        eligible = sprinting and anim.bIsBackward
        if not sprinting and self.owner is not None:
            self.stop()
            return
        if not eligible and self.owner is None:
            return
        try:
            forward, backward = players(anim)
        except (AttributeError, TypeError, ValueError):
            self.stop()
            self.layout_blocked_id = owner_id
            self.emit('backward carrier unavailable: animation layout changed')
            return
        source = self._source(forward, owner_id)
        source_id = int(source._get_address()) if source is not None else 0
        if self.owner is not None:
            target = self.target()
            if source_id != self.source_id:
                self.stop()
            elif target is not None and backward.BlendSpace is None:
                # The game emptied the slot on a weapon change: an empty slot is nobody's, the run goes back.
                backward.BlendSpace = target
                if not animation_assets.same(backward.BlendSpace, target):
                    self.stop()
                    raise ValueError('Backward carrier assignment failed')
                self.put_back += 1
                if self.put_back <= MAX_SAID:
                    self.emit(f'backward carrier put back after the game emptied the slot, {self.put_back}')
                return
            elif target is None or not animation_assets.same(backward.BlendSpace, target):
                self.blocked_id = source_id
                self.blocked_owner_id = owner_id
                self.stop()
                return
            else:
                return
        if not eligible or source is None or backward.BlendSpace is not None:
            return
        if source_id == self.blocked_id or now_ns < self.retry_at:
            return
        try:
            target = self.build(source, anim)
        except (AttributeError, TypeError, ValueError) as exc:
            self.retry_at = now_ns + RETRY_NS
            self.emit(f'backward carrier unavailable: {type(exc).__name__}')
            return
        self.owner, self.target = self.weak(anim), self.weak(target)
        self.owner_id, self.source_id = owner_id, source_id
        # Take ownership before the write so a failed setter can still be restored.
        backward.BlendSpace = target
        if not animation_assets.same(backward.BlendSpace, target):
            self.stop()
            raise ValueError('Backward carrier assignment failed')
        self.blocked_id = 0
        self.retry_at = 0
        self.emit('backward carrier applied')
