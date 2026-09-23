"""Own the private backward-run carrier for one live third-person body."""

from . import animation_assets

BACK_KEY = 'AnimSet.Player.3rd.Run_B'
SPRINT_KEY = 'AnimSet.Player.3rd.BS_Sprint'
BODY_CLASS = 'BPAnim_Player_3rd_C'
NODE_CLASS = 'GbxAnimNode_Locomotion'
PLAYER_CLASS = 'GbxAnimNode_BlendSpacePlayer'
GROUND_MODE = 1
RETRY_NS = 5_000_000_000


def players(anim):
    if str(anim.Class.Name) != BODY_CLASS:
        raise ValueError('Unsupported player animation class')
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


class Runtime:
    def __init__(self, weak, build, emit):
        self.weak, self.build, self.emit = weak, build, emit
        self.owner = self.target = None
        self.source_id = self.owner_id = 0
        self.retry_at = 0
        self.blocked_id = 0
        self.blocked_owner_id = 0
        self.layout_blocked_id = 0

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
        source = forward.BlendSpace
        source_id = int(source._get_address()) if source is not None else 0
        if self.owner is not None:
            target = self.target()
            if source_id != self.source_id:
                self.stop()
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


_runtime = None


def tick(obj, now_ns):
    global _runtime
    body_callback = obj is not None and str(getattr(getattr(obj, 'Class', None), 'Name', '')) == BODY_CLASS
    if not body_callback and (_runtime is None or _runtime.owner is None):
        return
    from mods_base import get_pc

    pc = get_pc(possibly_loading=True)
    character = getattr(pc, 'OakCharacter', None) if pc is not None else None
    mesh = getattr(character, 'Mesh', None) if character is not None else None
    body = mesh.GetAnimInstance() if mesh is not None else None
    if body is None:
        if _runtime is not None:
            _runtime.update(None, None, now_ns)
        return
    if not body_callback or not animation_assets.same(body, obj):
        if _runtime is not None and _runtime.owner is not None and int(body._get_address()) != _runtime.owner_id:
            _runtime.update(None, None, now_ns)
        return
    if _runtime is None:
        from unrealsdk import construct_object, find_object
        from unrealsdk.unreal import WeakPointer
        from . import report

        _runtime = Runtime(WeakPointer,
                           lambda source, owner: animation_assets.build(source, owner, find_object, construct_object),
                           report.note)
    _runtime.update(character, obj, now_ns)


def stop():
    global _runtime
    if _runtime is not None:
        _runtime.stop()
        _runtime = None
