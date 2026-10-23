"""A fake game for the tests of an enemy drawn to the hunter (test_target, test_brain_walk, test_chaser): characters,
the targeting and brain libraries, and the walk's parameter blocks, which a fake process_event runs as the game does.
Installed over sdk_stubs: sdk_stubs.install() first.

Taken from the trials' tests (docs/RUN/sondes/test_run_zone_target.py, test_run_brain_walk.py, test_run_chaser.py)
and the research's (mods/perso/apex_probe/source/test_apex_brain_target_patch.py), which each kept their own copy.
"""

import sys
import types
from typing import Any

LIBRARY_ADDRESS, FUNCTION_ADDRESS = 0x1000, 0x2000
# EGbxBrainExec.Start, what the game writes in a walk's Exec when it takes the walk.
START = 0


def character(address: int, dead: Any = False) -> Any:
    """A character as the target's patch reads it: an address of its own, a health state, a root."""
    return types.SimpleNamespace(_get_address=lambda: address, RootComponent=object(),
                                 HealthState=types.SimpleNamespace(bCurrentlyDead=dead))


class Block:
    """Stands for the SDK's WrappedStruct of a function's parameters, at its own address, each field an attribute.
    Writing a field named in refused raises, as the SDK refuses a value of the wrong type."""

    def __init__(self, refused: set, function: Any, **fields: Any) -> None:
        object.__setattr__(self, "refused", refused)
        object.__setattr__(self, "function", function)
        for name, value in fields.items():
            setattr(self, name, value)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.refused:
            raise TypeError(f"{name} refused")
        object.__setattr__(self, name, value)

    def _get_address(self) -> int:
        return id(self)


class Game:
    """The fake game. log lists in order what the game was asked: ("set", actor, target, restrictions),
    ("clear", actor), ("walk", actor, goal), ("abort", actor, at_once); walks keeps, for each walk, its block's fields
    as the call found them. primary and imposed hold each enemy's targets by its address. set_fails is "before" or
    "after" the write; clear_silent makes the clearing do nothing; walk_fails is raised by the walk; refused names
    the block fields the SDK refuses."""

    def __init__(self, state: dict) -> None:
        self.log: list[tuple] = []
        self.walks: list[dict] = []
        self.primary: dict[int, Any] = {}
        self.imposed: dict[int, Any] = {}
        self.blocks: dict[int, Block] = {}
        self.set_fails: str | None = None
        self.clear_silent = False
        self.walk_fails: BaseException | None = None
        self.refused: set[str] = set()
        self.function = types.SimpleNamespace(_get_address=lambda: FUNCTION_ADDRESS)
        targeting = types.SimpleNamespace(GetPrimaryTarget=self._primary, AIGetScriptedTarget=self._imposed,
                                          AISetScriptedTarget=self._set, AIClearScriptedTarget=self._clear)
        brain = types.SimpleNamespace(_get_address=lambda: LIBRARY_ADDRESS, AbortScriptedBrainTask=self._abort,
                                      AIScriptedMove=types.SimpleNamespace(func=self.function))
        state["classes"]["GbxTargetingFunctionLibrary"] = types.SimpleNamespace(ClassDefaultObject=targeting)
        state["classes"]["GbxBrainFunctionLibrary"] = types.SimpleNamespace(ClassDefaultObject=brain)
        unrealsdk = sys.modules["unrealsdk"]
        unrealsdk.make_struct = lambda name, **fields: types.SimpleNamespace(struct_name=name, **fields)
        unrealsdk.unreal.WrappedStruct = self.make_block

    def reset(self) -> None:
        """Forgets what was asked and every target, and lets every call through again."""
        for collection in (self.log, self.walks, self.primary, self.imposed, self.refused):
            collection.clear()
        self.set_fails, self.clear_silent, self.walk_fails = None, False, None

    def make_block(self, function: Any, **fields: Any) -> Block:
        """A block the fake process_event can find by its address, as the SDK's WrappedStruct makes them."""
        block = Block(self.refused, function, **fields)
        self.blocks[id(block)] = block
        return block

    def process_event(self, obj: int, func: int, params: int) -> None:
        """AIScriptedMove run on the block at params, as the game runs it: Start written in its Exec at once."""
        block = self.blocks[params]
        self.walks.append({"object": obj, "function": func, "block": block, "AIActor": block.AIActor,
                           "GoalActor": block.GoalActor, "Exec": block.Exec, "LatentInfo": block.LatentInfo})
        self.log.append(("walk", block.AIActor, block.GoalActor))
        if self.walk_fails is not None:
            raise self.walk_fails
        block.Exec = START

    def _primary(self, *, AIActor: Any) -> Any:
        return self.primary.get(AIActor._get_address())

    def _imposed(self, *, AIActor: Any) -> Any:
        return self.imposed.get(AIActor._get_address())

    def _set(self, *, AIActor: Any, TargetActor: Any, bApplyRestrictions: bool) -> None:
        self.log.append(("set", AIActor, TargetActor, bApplyRestrictions))
        if self.set_fails == "before":
            raise RuntimeError("refused")
        self.imposed[AIActor._get_address()] = TargetActor
        if self.set_fails == "after":
            raise RuntimeError("written, then refused")

    def _clear(self, *, AIActor: Any) -> None:
        self.log.append(("clear", AIActor))
        if not self.clear_silent:
            self.imposed.pop(AIActor._get_address(), None)

    def _abort(self, *, AIActor: Any, bStopImmediately: bool) -> None:
        self.log.append(("abort", AIActor, bStopImmediately))
