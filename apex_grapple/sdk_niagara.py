"""Niagara test boundary; signatures come from Epic API and the captured BL4 calls."""

import types
from typing import Any


class FakeNiagara:
    """NiagaraFunctionLibrary's class default object: what was spawned and what was set on it."""

    def __init__(self, state: dict) -> None:
        self.state = state
        self.spawned: list[dict] = []
        self.set: list[tuple] = []
        # Niagara adds the User. prefix itself, so the effect prints "User.Target" and the setter
        # wants "Target". The fake models both, which is what the search has to cope with.
        self.end_name = "Target"
        self.source_name = "Source"
        # Set by a test to make the game refuse the free spawn, so the fallback is exercised.
        self.loose_fails = False
        self.float_fails = False

    def SpawnSystemAtLocation(self, world: Any, system: Any, location: Any, rotation: Any,
                              scale: Any, auto_destroy: bool, auto_activate: bool, pooling: int,
                              precull: bool) -> Any:
        """Free in the world, as the game spawns its own rope. Positional, as the game's function is."""
        if self.loose_fails:
            raise AttributeError("no SpawnSystemAtLocation on this build")
        component = self._component()
        component.bAutoDestroy = auto_destroy
        self.spawned.append({"how": "loose", "SystemTemplate": system, "Location": location,
                             "Rotation": rotation, "bAutoDestroy": auto_destroy,
                             "bAutoActivate": auto_activate, "component": component})
        return component

    def SpawnSystemAttached(self, **kwargs: Any) -> Any:
        component = self._component()
        component.bAutoDestroy = bool(kwargs.get("bAutoDestroy"))
        self.spawned.append(dict(kwargs, how="attached", Rotation=kwargs.get("Rotation"),
                                 component=component))
        return component

    def complete_effect(self, component: Any) -> None:
        """Model Niagara completing an effect while the owning gameplay action is still active."""
        if component.bAutoDestroy:
            component.DestroyComponent()

    def _component(self) -> Any:
        component = types.SimpleNamespace(alive=True)
        component.activations = 0
        def destroy():
            self.state["destroyed"].append(component)
            component.destroyed = True

        component.DestroyComponent = destroy

        def deactivate():
            component.alive = False

        component.Deactivate = deactivate

        def put(name: str, value: Any) -> None:
            if getattr(component, "destroyed", False):
                raise RuntimeError("native component expired")
            if name not in (self.end_name, self.source_name):
                raise RuntimeError(f"no parameter {name}")
            self.set.append((name, value))

        # The effect itself takes the positions. The library does not: verified in game on
        # 2026-09-21, it has no SetNiagaraVariablePosition at all, which is why it is absent here.
        component.SetVariablePosition = put
        component.float_parameters = {}

        def put_float(name: str, value: float) -> None:
            if self.float_fails:
                raise RuntimeError("lifetime refused")
            if name != "User.Lifetime" or not isinstance(value, float):
                raise ValueError("unexpected float parameter")
            component.float_parameters[name] = value

        component.SetVariableFloat = put_float
        # Record inputs at activation; this fake makes no assertion about simulated particles.
        component.lit_with = None

        def activate(reset):
            component.lit_with = list(self.set)
            component.floats_at_activation = dict(component.float_parameters)
            component.activations += 1

        def place(NewLocation, NewRotation, bSweep, SweepHitResult, bTeleport):
            # Epic's SceneComponent signature, UE 5.5. The SDK returns void as Ellipsis, then outputs.
            component.world_spot = (NewLocation.X, NewLocation.Y, NewLocation.Z)
            component.world_turn = (NewRotation.Pitch, NewRotation.Yaw, NewRotation.Roll)
            component.RelativeRotation = NewRotation
            return Ellipsis, SweepHitResult

        component.Activate = activate
        component.K2_SetWorldLocationAndRotation = place
        component.K2_GetComponentLocation = lambda: types.SimpleNamespace(
            X=component.world_spot[0], Y=component.world_spot[1], Z=component.world_spot[2])
        return component

    def SetNiagaraVariableVec3(self, component: Any, name: str, value: Any) -> None:
        # As Unreal 5 does: a world position is its own type and a plain vector cannot write it.
        raise RuntimeError(f"{name} is a position, not a vector")
