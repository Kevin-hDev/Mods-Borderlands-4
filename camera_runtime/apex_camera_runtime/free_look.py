"""Free Look: hold a key and the camera turns alone while the hunter or the vehicle keeps going.

Named by Kevin on 2026-10-07, after Apex's Freelook. The elected camera mod's frame hands its settings over
(CameraRuntime.tick); at the wheel that frame stops, so the unit keeps its own clock, any animation update as the
framing at the wheel does, updates closer than MIN_STEP_NS being the same frame seen again. Its keys are read each
frame on the game's key states (IsInputKeyDown, verified in game for A, Left Alt and L3 by the probes): the camera
commands' binds only see presses, and Free Look needs the release. One mistake stops it, everything put back,
until the player or the vehicle changes, as the framing at the wheel does.
"""

from typing import Any, Callable

from . import free_look_swap
from .easing import MAX_STEP_S
from .free_look_foot import Foot
from .free_look_keys import Trigger
from .free_look_wheel import Wheel

FRAME = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
IDENTIFIER = "apex_camera_runtime:free_look"
MIN_STEP_NS = 3_000_000
ON_FOOT, AT_WHEEL = "foot", "wheel"
# Bounded: two Free Look keys and the few movement keys of the game's list.
MAX_KEYS = 64


class FreeLook:
    def __init__(self, load: Callable) -> None:
        """load() gives (sdk, memory, hooks, get_pc, clock, log, address_of), asked when the clock is first needed:
        the runtime exists before the game's modules can be read, as in the camera mods' tests."""
        self.load = load
        self.game = None
        self.values = None
        self.installed = False
        self.trigger = Trigger()
        self.state = None
        self.identity = (0, 0)
        self.failed = (0, 0)
        self.last_ns = 0
        self.keys: dict = {}

    def sync(self, settings: Any) -> None:
        """On foot, from the elected mod's frame: the clock runs while a Free Look key is set."""
        read = getattr(settings, "free_look", None)
        values = read() if callable(read) else None
        self.values = values if values is not None and any(values.keys) else None
        if self.values is not None and not self.installed:
            if self.game is None:
                self.game = self.load()
                sdk, memory, hooks, _get_pc, _clock, log, _address = self.game
                self.foot, self.wheel = Foot(sdk, memory, hooks, log), Wheel(sdk, log)
            hooks = self.game[2]
            hooks.add_hook(FRAME, hooks.Type.POST, IDENTIFIER, self.on_frame)
            self.installed = True
        elif self.values is None and self.installed:
            self.stop()

    def _key(self, name: str) -> Any:
        key = self.keys.get(name)
        if key is None:
            if len(self.keys) >= MAX_KEYS:
                self.keys.clear()
            key = self.keys[name] = self.game[0].make_struct("Key", KeyName=name)
        return key

    def on_frame(self, _obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
        _sdk, _memory, _hooks, get_pc, clock, log, address_of = self.game
        now_ns = clock()
        if now_ns - self.last_ns < MIN_STEP_NS:
            return
        step_s = 0.0 if not self.last_ns else min((now_ns - self.last_ns) / 1e9, MAX_STEP_S)
        self.last_ns = now_ns
        pc = get_pc(possibly_loading=True)
        pawn = getattr(pc, "Pawn", None) if pc is not None else None
        identity = (address_of(pc), address_of(pawn)) if pawn is not None else (0, 0)
        if identity != self.identity:
            # A new character or vehicle under the same controller: its own state goes back; another controller:
            # the old one is gone and is not touched.
            same_controller = identity[0] != 0 and identity[0] == self.identity[0]
            self._drop(stale=not same_controller, pc=pc if same_controller else None)
            self.identity = identity
        if pawn is None or self.values is None or identity == self.failed:
            return
        try:
            self._step(pc, pawn, step_s)
        except Exception as error:
            self.failed = identity
            log(f"free look stopped until the next character or vehicle: {type(error).__name__}: {error}")
            self._drop(stale=False, pc=pc)

    def _step(self, pc: Any, pawn: Any, step_s: float) -> None:
        values = self.values
        downs = tuple(name is not None and bool(pc.IsInputKeyDown(self._key(name))) for name in values.keys)
        at_wheel = getattr(pawn, "OakVehicleMovement", None) is not None
        if not at_wheel and free_look_swap.aiming(pc):
            self.trigger.cancel()
        wanted = self.trigger.step(downs, values.holds, values.hold_s, step_s)
        if self.foot.returning:
            self.foot.finish_return()
        if self.state is not None and (self.state == AT_WHEEL) != at_wheel:
            self._drop(stale=False, pc=pc)
        if not wanted:
            self._release(pc)
            return
        value = lambda name: float(pc.GetInputAnalogKeyState(self._key(name)))
        if self.state is None:
            unit, state = (self.wheel, AT_WHEEL) if at_wheel else (self.foot, ON_FOOT)
            if not unit.begin(pc):
                return
            self.state = state
            self.game[5](f"free look on {state}")
        if self.state == ON_FOOT:
            self.foot.frame(pc, value, step_s)
        else:
            self.wheel.frame(pc, value)

    def _release(self, pc: Any) -> None:
        state, self.state = self.state, None
        if state == ON_FOOT:
            self.foot.release(pc)
        elif state == AT_WHEEL:
            self.wheel.release(pc)

    def _drop(self, stale: bool, pc: Any = None) -> None:
        """Everything back at once. stale: the old controller is gone and is not touched."""
        state, self.state = self.state, None
        if self.game is None:
            return
        try:
            self.foot.abort(None if stale else pc)
        finally:
            self.wheel.abort(stale=stale or state != AT_WHEEL)

    def stop(self) -> None:
        if self.installed:
            hooks = self.game[2]
            if hooks.has_hook(FRAME, hooks.Type.POST, IDENTIFIER):
                hooks.remove_hook(FRAME, hooks.Type.POST, IDENTIFIER)
            self.installed = False
        self.values = None
        self.trigger = Trigger()
        if self.game is not None:
            pc = self.game[3](possibly_loading=True)
            same = pc is not None and getattr(pc, "Pawn", None) is not None and self.identity == (
                self.game[6](pc), self.game[6](pc.Pawn))
            self._drop(stale=not same, pc=pc if same else None)
        self.identity = self.failed = (0, 0)


def game_modules() -> tuple:
    import time
    import unrealsdk
    from mods_base import get_pc
    from unrealsdk import hooks, logging
    from . import process_memory
    return (unrealsdk, process_memory, hooks, get_pc, time.perf_counter_ns,
            lambda message: logging.info(f"[Camera Runtime] {message}"), lambda item: int(item._get_address()))
