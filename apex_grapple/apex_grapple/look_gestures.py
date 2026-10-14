"""The grapple gun's gestures played on the hunter, on the first-person arms and on the body at each shot whatever the view (a
view changed during the grapple shows the right one), each set image by image where look_moves puts it, then stopped.

Every gesture plays as the trials played them, verified in game: a montage held still in its slot (rate 0.001,
animation.py), its place set at every frame (Montage_SetPosition, trial 6), faded in and out in 0.25 s (trial 2), each
animation looked up right before it plays and never kept (look_load.animation). The places were checked together in
game, standing and flying (docs/apex_grapple/pistolet-grappin/enquetes/2026-10-14-gestes-ensemble.md): on the arms,
ours in Offhand and the game's stow in Mainhand; on the body, the game's flight in UpperBody, ours over it in
Offhand and Mainhand. The body's arms come standing or flying, crossfaded with the flight (look_assets.GESTURES; why, in
fabrique/gesture_animations.py). A gesture the game refuses to play is a failure of the look (conception, « Pannes »).
"""

from typing import Any

from unrealsdk import unreal

from . import arms, look_assets, look_load, look_moves, report

ARMS, BODY = "arms", "body"
LEFT, RIGHT, FLIGHT = "left", "right", "flight"
SLOTS = {LEFT: "Offhand", RIGHT: "Mainhand", FLIGHT: "UpperBody"}
FADE_S = 0.25
# A play rate this small is a still image (animation.py).
FROZEN_RATE = 0.001
FPS = 30.0
# The game's own: the arms' stows, held one image before their end, before the weapon goes (trial 2); Vex's grapple
# flight from its image 24 to 30 (spec-pistolet-grappin.md, section 9, choice 5).
ARMS_STOWS = {"RH": "/Game/PlayerCharacters/_Shared/Animation/1st/Rifle/_Shared/AS_RH_UnEquip_Offhand"
                    ".AS_RH_UnEquip_Offhand",
              "PS": "/Game/PlayerCharacters/_Shared/Animation/1st/Pistol/_Shared/AS_PS_UnEquip_Offhand"
                    ".AS_PS_UnEquip_Offhand"}
FLIGHT_PATH = "/Game/PlayerCharacters/DarkSiren/Animation/3rd/Rifle/_Shared/AS_RH_Grapple.AS_RH_Grapple"
FLIGHT_IMAGES = (24, 30)
HELD_AT_END = None


def gesture(view: str, side: str, stance: str | None = None, flying: bool = False) -> dict:
    """One of our gestures, by view, arm, the right arm's weapon stance, and flight."""
    for one in look_assets.GESTURES:
        if (one["view"], one["side"], one["stance"], one["flying"]) == (view, side, stance, flying):
            return one
    raise KeyError(f"no gesture for {view} {side} {stance} {'flying' if flying else 'standing'}")


def arms_place(left: tuple[str, float]) -> float:
    """Where the arms' gesture is, in seconds, for a phase of look_moves and its fraction."""
    phase, fraction = left
    start, end = gesture(ARMS, LEFT)["parts"][phase]
    return start + (end - start) * fraction


def fold_place(one: dict, fold: float) -> float:
    start, end = one["parts"]["fold"]
    return start + (end - start) * fold


def flight_place(fold: float) -> float:
    first, last = FLIGHT_IMAGES
    return (first + (last - first) * fold) / FPS


class Track:
    """One slot of one mesh: the animation it holds, if any."""

    def __init__(self, slot: str) -> None:
        self.slot, self.path, self.at = slot, None, 0.0
        self.instance: Any = None
        self.montage: Any = None

    def playing(self) -> bool:
        return self.path is not None

    def follow(self, instance: Any, path: str, at: float | None) -> None:
        """Holds `path` at `at` seconds (HELD_AT_END: one image before its end): played anew, the one before faded
        out, when it is another animation or another mesh; moved there otherwise."""
        if self.path != path or self.instance is None or self.instance() is not instance:
            self.stop(FADE_S)
            self._play(instance, path, at)
        elif at is not None and abs(at - self.at) > 1e-6:
            self.at = at
            instance.Montage_SetPosition(self.montage(), at)

    def _play(self, instance: Any, path: str, at: float | None) -> None:
        animation = look_load.animation(path)
        if at is HELD_AT_END:
            at = max(0.0, float(animation.GetPlayLength()) - 1.0 / FPS)
        montage = instance.PlaySlotAnimationAsDynamicMontage(
            Asset=animation, SlotNodeName=self.slot, BlendInTime=FADE_S, BlendOutTime=FADE_S, InPlayRate=FROZEN_RATE,
            LoopCount=1, BlendOutTriggerTime=-1.0, InTimeToStartMontageAt=at)
        # The SDK may give output parameters after the return value.
        if isinstance(montage, tuple):
            montage = montage[0] if montage else None
        if montage is None:
            raise RuntimeError(f"the game played none of {path.rsplit('.', 1)[-1]} in {self.slot}")
        self.path, self.at = path, at
        self.instance, self.montage = unreal.WeakPointer(instance), unreal.WeakPointer(montage)

    def stop(self, fade_s: float) -> None:
        instance = self.instance() if self.instance is not None else None
        montage = self.montage() if self.montage is not None else None
        self.path, self.instance, self.montage = None, None, None
        if instance is not None and montage is not None:
            instance.Montage_Stop(fade_s, montage)


_tracks = {(ARMS, LEFT): Track(SLOTS[LEFT]), (ARMS, RIGHT): Track(SLOTS[RIGHT]),
           (BODY, FLIGHT): Track(SLOTS[FLIGHT]), (BODY, LEFT): Track(SLOTS[LEFT]), (BODY, RIGHT): Track(SLOTS[RIGHT])}


def busy() -> bool:
    return any(track.playing() for track in _tracks.values())


def frame(character: Any, pose: look_moves.Pose, kind: str | None, holding: bool) -> None:
    """Every gesture where `pose` puts it. `kind`: the right hand's weapon (look_weapon), None with none; `holding`:
    the body's left hand still holds the pistol, until the shot's hook is back."""
    found = arms.find(character)
    if found is None:
        report.error_once("look:arms", "the first-person arms were not found: the arms' gestures wait for them")
    else:
        _arms(found, pose, kind)
    _body(character.Mesh.GetAnimInstance(), pose, kind, holding)


def _arms(instance: Any, pose: look_moves.Pose, kind: str | None) -> None:
    left, right = _tracks[(ARMS, LEFT)], _tracks[(ARMS, RIGHT)]
    if pose.left[0] == look_moves.GONE:
        left.stop(FADE_S)
    else:
        left.follow(instance, gesture(ARMS, LEFT)["path"], arms_place(pose.left))
    if kind is not None and pose.right_away:
        right.follow(instance, ARMS_STOWS[kind], HELD_AT_END)
    else:
        right.stop(look_moves.RETURN_S)


def _body(instance: Any, pose: look_moves.Pose, kind: str | None, holding: bool) -> None:
    flying = pose.flight is not None
    if flying:
        _tracks[(BODY, FLIGHT)].follow(instance, FLIGHT_PATH, flight_place(pose.flight))
    else:
        _tracks[(BODY, FLIGHT)].stop(FADE_S)
    if holding:
        left = gesture(BODY, LEFT, flying=flying)
        _tracks[(BODY, LEFT)].follow(instance, left["path"], fold_place(left, pose.fold))
    else:
        _tracks[(BODY, LEFT)].stop(FADE_S)
    if kind is not None and pose.right_away:
        right = gesture(BODY, RIGHT, kind, flying)
        _tracks[(BODY, RIGHT)].follow(instance, right["path"], fold_place(right, pose.fold))
    else:
        _tracks[(BODY, RIGHT)].stop(look_moves.RETURN_S)


def stop() -> None:
    """Every gesture faded out, each tried even when another fails, the first failure raised after."""
    failed = None
    for track in _tracks.values():
        try:
            track.stop(FADE_S)
        except Exception as error:
            failed = failed or error
    if failed is not None:
        raise failed
