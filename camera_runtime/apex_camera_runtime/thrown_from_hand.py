"""Third person: the hunter's knife or grenade leaves his hand for the crosshair (Kevin, 2026-10-21).

Provisional (Kevin, 2026-10-22: « c'est temporaire, il faudra corriger le vrai probleme apres »). The game makes a
throw start about 1.5 m in front of the camera (its GbxViewRelativeLocation): in first person that is by the hand, in
third person beside the hunter, while his animation shows the object in his left hand, so it popped from one to the
other. This unit catches the object once it exists, moves it into that hand and turns the game's own launch toward the
point under the crosshair (thrown_send.py). It goes away once the game itself starts the throw in the hand
(docs/investigations/third_person_fov/camera/2026-10-21-rayon-ohm-et-couteau.md).

Every animation update, not once a frame: the object must move before the frame it is born in is drawn. The first
throw of a kind exists before the game places and launches it (at the world's origin, without speed): it is watched
until it flies, WAIT_S at most. Only objects this game runs (HasAuthority): a client's copy would be put back by the
host. Any failure stops the unit until the camera starts again, and throws stay as the game makes them.
"""

import math
import time
from typing import Any, Callable

from .constants import THIRD_PERSON_MODE
from .thrown_send import ThrowSender, vector

FRAME = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
IDENTIFIER = "apex_camera_runtime:thrown_from_hand"
THROWN_CLASS = "ModularGrenade"
# How long a first throw may wait to be launched; the time the game takes is not measured.
WAIT_S = 3.0
# Bounds on what the game hands us: children looked at, objects remembered or waited for, detail lines per start.
MAX_CHILDREN = 64
MAX_SEEN = 256
MAX_WAITING = 8
MAX_DETAIL_LINES = 50


def _speed(obj: Any) -> float:
    return math.sqrt(sum(part * part for part in vector(obj.GetVelocity())))


class ThrownFromHand:
    def __init__(self, hooks: Any, sdk: Any, kismet: Any, weak_ref: Callable, log: Callable[[str], None],
                 detail_log: Callable[[str], None], clock: Callable[[], float] = time.perf_counter) -> None:
        self.hooks, self.sdk, self.weak_ref, self.clock = hooks, sdk, weak_ref, clock
        self.sender = ThrowSender(sdk, kismet)
        self.log, self.detail_log = log, detail_log
        self.active = False
        self._forget()

    def _forget(self) -> None:
        self.pc_ref = self.thrown_class = None
        # Address and name: an address freed by a destroyed object can come back with the next one.
        self.seen: dict[tuple, None] = {}
        # (weak reference, name, seen at) of the objects not launched yet.
        self.waiting: list[tuple] = []
        self.children_key: tuple | None = None
        self.sent = self.left = self.details = 0
        self.failed = False

    def start(self, pc: Any) -> None:
        self.stop()
        self.thrown_class = self.sdk.find_class(THROWN_CLASS)
        if self.thrown_class is None:
            raise LookupError("thrown object class missing")
        self.pc_ref = self.weak_ref(pc)
        pawn = getattr(pc, "Pawn", None)
        if pawn is not None:
            # Objects thrown before (a knife still in a wall) are only remembered.
            self._new_children(pawn)
        self.hooks.add_hook(FRAME, self.hooks.Type.POST, IDENTIFIER, self.on_frame)
        self.active = True

    def stop(self) -> None:
        if self.hooks.has_hook(FRAME, self.hooks.Type.POST, IDENTIFIER):
            self.hooks.remove_hook(FRAME, self.hooks.Type.POST, IDENTIFIER)
        if self.active and (self.sent or self.left):
            self.detail_log(f"throws from the hand sent={self.sent} left={self.left}")
        self.active = False
        self._forget()

    def on_frame(self, _obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
        if not self.active or self.failed:
            return
        try:
            self._step()
        except Exception as error:
            self.failed = True
            self.log(f"throws from the hand stopped: {type(error).__name__}")

    def _step(self) -> None:
        pc = self.pc_ref()
        pawn = getattr(pc, "Pawn", None) if pc is not None else None
        if pawn is None:
            return
        if self.waiting:
            self._check_waiting(pc, pawn)
        children = pawn.Children
        count = len(children)
        # A new child is added at the end: the same count and last child mean nothing was thrown since.
        key = (count, int(children[count - 1]._get_address()) if count else 0)
        if key == self.children_key:
            return
        self.children_key = key
        for obj in self._new_children(pawn):
            if obj.Class._inherits(self.thrown_class) and obj.Instigator == pawn:
                self._first_sight(pc, pawn, obj)

    def _new_children(self, pawn: Any) -> list:
        children = pawn.Children
        count = len(children)
        found = []
        for index in range(count - 1, max(-1, count - 1 - MAX_CHILDREN), -1):
            obj = children[index]
            key = (int(obj._get_address()), str(obj.Name))
            if key not in self.seen:
                self.seen[key] = None
                found.append(obj)
        while len(self.seen) > MAX_SEEN:
            del self.seen[next(iter(self.seen))]
        return found

    def _third_person(self, pc: Any, pawn: Any) -> bool:
        return str(pc.PlayerCameraManager.GetActorCameraMode(pawn)) == THIRD_PERSON_MODE

    def _first_sight(self, pc: Any, pawn: Any, obj: Any) -> None:
        if not self._third_person(pc, pawn):
            return
        if not obj.HasAuthority():
            self._leave(str(obj.Name), "client")
        elif _speed(obj) > 0.0:
            self._send(pc, pawn, obj, "")
        elif len(self.waiting) < MAX_WAITING:
            # Kept weakly: the game may destroy it before it flies, and a stale object would crash the game.
            self.waiting.append((self.weak_ref(obj), str(obj.Name), self.clock()))
        else:
            self._leave(str(obj.Name), "too_many_waiting")

    def _check_waiting(self, pc: Any, pawn: Any) -> None:
        now = self.clock()
        for entry in list(self.waiting):
            ref, name, seen_at = entry
            obj = ref()
            if obj is None:
                self.waiting.remove(entry)
                self._leave(name, "gone_before_launch")
            elif _speed(obj) > 0.0:
                self.waiting.remove(entry)
                if self._third_person(pc, pawn):
                    self._send(pc, pawn, obj, f" waited_ms={(now - seen_at) * 1000:.0f}")
            elif now - seen_at > WAIT_S:
                self.waiting.remove(entry)
                self._leave(name, "never_launched")

    def _send(self, pc: Any, pawn: Any, obj: Any, waited: str) -> None:
        sent, detail = self.sender.send(pc, pawn, obj)
        if not sent:
            self._leave(str(obj.Name), detail + waited)
            return
        self.sent += 1
        self._detail(f"throw from the hand object={obj.Name} {detail}{waited}")

    def _leave(self, name: str, reason: str) -> None:
        self.left += 1
        self._detail(f"throw left as thrown object={name} reason={reason}")

    def _detail(self, line: str) -> None:
        if self.details < MAX_DETAIL_LINES:
            self.details += 1
            self.detail_log(line)
