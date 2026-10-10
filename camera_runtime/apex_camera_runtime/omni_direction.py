"""Omni direction: the body faces its run in third person, the sprint opens in every direction, the sprint's
backward slot follows, crouching beyond the game's angle still dashes, and slides follow the run
(docs/omni_direction/spec-omni-direction.md).

One unit for the three camera mods, made by shared.py and fed by CameraRuntime.tick: the elected mod's settings
decide the body, the angle, the third-person sprint and the crouch; Omni Sprint's own switch, from any installed
copy, opens the sprint in every view. The body is turned in a hook just before the played body's animation update.
"""

from dataclasses import dataclass
from typing import Any, Callable

from .backward_carrier import BackwardCarrier, players
from .backward_carrier_assets import build, same
from .body_actions import Actions
from .body_facing import BodyFacing
from .body_pose import Pose
from .crouch_dash import CrouchDash
from .omni_direction_reads import in_third_person, played_address, sprint_everywhere, wanted_values
from .slide_launch import SlideLaunch
from .sprint_search import SprintKeeper
from .sprint_slot import CARRIER, FORWARD, NONE, SprintSlot

FRAME = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
IDENTIFIER = "apex_camera_runtime:omni_direction"


@dataclass(frozen=True)
class Game:
    get_pc: Callable[[], Any]
    make_rotator: Callable[[float, float, float], Any]
    make_key: Callable[[str], Any]
    weak: Callable[[Any], Any]
    find: Callable[..., Any]
    construct: Callable[..., Any]
    hooks: Any
    log: Callable[[str], None]
    clock: Callable[[], int]
    # (identifier, key, callback(event)) -> a binding with disable(); nothing it binds blocks the key.
    bind: Callable[[str, str, Callable[[Any], None]], Any]


class OmniDirection:
    def __init__(self, load: Callable[[], Game], identifier: str = IDENTIFIER) -> None:
        """load() gives the game's modules, asked at the first tick: the runtime exists before they can be read.
        A private copy (Omni Sprint's sprint_fallback.py) hooks under its own identifier."""
        self.load, self.identifier = load, identifier
        self.game: Game | None = None
        self.third_person = False
        self.values: Any = None
        self.open_wanted = False
        self.installed = False
        self.failed = False
        # The played body's address, read at each tick: the hook drops every other animation of the world on it.
        self.played_id = 0

    def _start(self) -> None:
        game = self.game = self.load()
        self.keeper = SprintKeeper(game.log)
        carrier = BackwardCarrier(game.weak, lambda source, owner: build(source, owner, game.find, game.construct),
                                  game.log)
        self.slot = SprintSlot(carrier, players, same, game.weak, game.log)
        self.facing = BodyFacing(game.make_rotator)
        self.pose = Pose()
        self.actions = Actions(game.make_key, game.log)
        self.crouch = CrouchDash(game.bind, self.keeper, game.get_pc, game.clock, game.log, self.identifier)
        self.slides = SlideLaunch(game.find, game.log)
        self.body_ref: Any = None
        self.body_id = 0

    def sync(self, clients: Any, settings: Any, pc: Any, controller: Any, now_ns: int) -> None:
        if self.failed:
            return
        try:
            if self.game is None:
                self._start()
            self.values = wanted_values(settings)
            self.played_id = played_address(pc)
            self.third_person = in_third_person(controller)
            facing = self.third_person and self.values is not None and self.values.body
            self.open_wanted = sprint_everywhere(clients) or (
                self.third_person and self.values is not None and self.values.sprint)
            self.keeper.update(pc, self.open_wanted, now_ns)
            self.crouch.update(pc, self.open_wanted, self.values is None or self.values.dash, now_ns)
            self.slides.update(facing or self.open_wanted, now_ns)
            hooks = self.game.hooks
            if (facing or self.open_wanted) and not self.installed:
                hooks.add_hook(FRAME, hooks.Type.PRE, self.identifier, self.on_frame)
                self.installed = True
            elif not (facing or self.open_wanted) and self.installed and not self._held():
                # Every animation update in the world calls the hook: off while nothing is asked or held.
                hooks.remove_hook(FRAME, hooks.Type.PRE, self.identifier)
                self.installed = False
        except Exception as error:
            self._fail(error)

    def _held(self) -> bool:
        return self.facing.holding or self.slot.holding or self.slot.carrier.owner is not None

    def facing_wanted(self) -> bool:
        return self.third_person and self.values is not None and self.values.body

    def on_frame(self, obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
        if self.failed or self.game is None:
            return
        try:
            self._frame(obj)
        except Exception as error:
            self._fail(error)

    def _frame(self, obj: Any) -> None:
        if obj is None or not self.played_id or int(obj._get_address()) != self.played_id:
            return
        pc = self.game.get_pc()
        character = getattr(pc, "OakCharacter", None) if pc is not None else None
        if character is None:
            return
        body, body_id = obj, self.played_id
        if body_id != self.body_id:
            self._forget_body()
            self.body_ref, self.body_id = self.game.weak(body), body_id
        now_ns = self.game.clock()
        holding = False
        if self.facing_wanted():
            acting = self.actions.acting(pc, body, now_ns)
            holding = self.facing.step(character, body, self.pose, acting, self.values.full_turn, now_ns)
        elif self.facing.holding:
            self.facing.release(body, self.pose)
        use = FORWARD if holding else CARRIER if self.open_wanted else NONE
        self.slot.update(character, body, body_id, use, now_ns)

    def _forget_body(self) -> None:
        """A new body (map change, respawn, a new look) starts with the game's own pose: the old one is let go."""
        self.facing.holding, self.facing.offset, self.facing.kept_yaw = False, 0.0, None
        self.pose.original = None
        self.actions.reset()

    def _fail(self, error: Exception) -> None:
        self.failed = True
        if self.game is not None:
            self.game.log(f"omni direction stopped for the session after an error: {type(error).__name__}")
        try:
            self.stop()
        except Exception as cleanup:
            # Inside the game's own hook: said, never raised.
            if self.game is not None:
                self.game.log(f"omni direction could not give everything back: {type(cleanup.__cause__).__name__}")

    def stop(self) -> None:
        """Everything back to the game: the body, the chest's twist, the sprint slot, the crouch keys, the slides'
        direction, the sprint limit, the hook."""
        if self.game is None:
            return
        errors = []
        hooks = self.game.hooks
        if self.installed and hooks.has_hook(FRAME, hooks.Type.PRE, self.identifier):
            hooks.remove_hook(FRAME, hooks.Type.PRE, self.identifier)
        self.installed = False
        body = self.body_ref() if self.body_ref is not None else None
        for action in (lambda: self.facing.release(body, self.pose), self.slot.stop, self.crouch.stop,
                       self.slides.give_back, self._put_back):
            try:
                action()
            except Exception as error:
                errors.append(error)
        self.body_ref, self.body_id, self.third_person, self.values, self.open_wanted = None, 0, False, None, False
        self.played_id = 0
        self.actions.reset()
        if errors:
            raise RuntimeError("omni direction cleanup incomplete") from errors[0]

    def _put_back(self) -> None:
        restored, left = self.keeper.stop()
        if restored or left:
            line = f"stopped, game sprint limit put back in {restored} movement definition(s)"
            self.game.log(line + (f", {left} left alone: no longer recognised in memory" if left else ""))


def game_modules() -> Game:
    import time

    import unrealsdk
    from mods_base import get_pc, keybind
    from unrealsdk import hooks, logging
    from unrealsdk.unreal import WeakPointer

    def bind(identifier: str, key: str, callback: Callable[[Any], None]) -> Any:
        # Every event, the callback keeping the press only (event_filter=None), as the trial 9 probe bound it.
        bound = keybind(identifier, key, callback, is_hidden=True, event_filter=None)
        bound.enable()
        return bound

    loaded = Game(lambda: get_pc(possibly_loading=True),
                  lambda pitch, yaw, roll: unrealsdk.make_struct("Rotator", Pitch=pitch, Yaw=yaw, Roll=roll),
                  lambda name: unrealsdk.make_struct("Key", KeyName=name), WeakPointer, unrealsdk.find_object,
                  unrealsdk.construct_object, hooks, lambda message: logging.info(f"[Camera Runtime] {message}"),
                  time.perf_counter_ns, bind)
    return loaded
