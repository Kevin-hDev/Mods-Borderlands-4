"""Native valid targets own their action; walls and cancellation retain Apex behavior."""

from types import SimpleNamespace as NS

from grapple_fixture import fresh, game, settings, state
from apex_grapple import native_interaction


def target(kind):
    return NS(Class=NS(Name=kind))


pc = NS(GrappleTargetingStrategy=NS(BestValidTarget=NS(Grappleable=None)))
game.controller = lambda: pc
settings.keep_game_grapple.value = False
assert not native_interaction.has_priority()
for kind in ("CarryableObject", "GrappleInteractable", "GrappleGrate", "SiloGrappleSlider"):
    pc.GrappleTargetingStrategy.BestValidTarget.Grappleable = target(kind)
    assert native_interaction.has_priority(), kind
    player, rope = fresh(on_ground=False)
    assert not rope.fire(player, 0), kind
    assert not rope.busy

pc.GrappleTargetingStrategy.BestValidTarget.Grappleable = target("GrapplePoint")
assert not native_interaction.has_priority()
settings.keep_game_grapple.value = True
assert native_interaction.has_priority()
pc.GrappleTargetingStrategy.BestValidTarget.Grappleable = None
player, rope = fresh(on_ground=False)
assert rope.fire(player, 0)
pc.GrappleTargetingStrategy.BestValidTarget.Grappleable = target("CarryableObject")
assert rope.fire(player, 1)  # The existing shot must still cancel on a second press.
assert not rope.busy


class Broken:
    @property
    def BestValidTarget(self):
        raise RuntimeError("private details")


pc.GrappleTargetingStrategy = Broken()
assert native_interaction.has_priority()
assert not any("private details" in line for line in state["errors"])
pc.GrappleTargetingStrategy = NS(BestValidTarget=NS(Grappleable=None))
assert not native_interaction.has_priority()  # An error must not disable future surface shots.

from apex_grapple import keys
import sdk_stubs
from unrealsdk.hooks import Block

player, rope = fresh(on_ground=False)
strategy = pc.GrappleTargetingStrategy
pc = state["pc"]
pc.GrappleTargetingStrategy = strategy
keys.bind(state["mappings"], rope)
pc.GrappleTargetingStrategy.BestValidTarget.Grappleable = target("CarryableObject")
press = state["keybinds"]["V"]
assert press(sdk_stubs.event("IE_Pressed")) is None
assert press(sdk_stubs.event("IE_Repeat")) is None
assert press(sdk_stubs.event("IE_Released")) is None
assert not rope.busy
pc.GrappleTargetingStrategy.BestValidTarget.Grappleable = None
assert press(sdk_stubs.event("IE_Pressed")) is Block
assert press(sdk_stubs.event("IE_Released")) is Block
assert rope.busy
keys.unbind()

# Native validity must match the game's indicator, even outside the former narrow cone.
from apex_grapple import aim

player, rope = fresh(on_ground=False)
pc = state["pc"]
pc.GrappleTargetingStrategy = NS(BestValidTarget=NS(Grappleable=target("GrapplePoint")))
settings.keep_game_grapple.value = True
aim.game_point_near = lambda anchor: True
game.character = lambda: player
game.aim = lambda char: ((0, 0, 0), (1, 0, 0))
state["extra_classes"]["SceneComponent"] = NS(Name="SceneComponent")
for kind, socket in (("GrapplePoint", "Attach"), ("CarryableObject", "GrappleTarget")):
    item = target(kind)
    item.K2_GetComponentsByClass = lambda cls, socket=socket: [NS(
        GetAllSocketNames=lambda: [socket],
        GetSocketLocation=lambda name: sdk_stubs.vector(1000, 500, 0))]
    pc.GrappleTargetingStrategy.BestValidTarget.Grappleable = item
    assert native_interaction.has_priority() is True, "native valid target rejected by angle"
    assert not rope.fire(player, 0), "Apex must leave the indicated native action available"
    assert not rope.busy
pc.GrappleTargetingStrategy.BestValidTarget.Grappleable = None
assert rope.fire(player, 1)
rope.reset()
del pc.GrappleTargetingStrategy
assert native_interaction.has_priority() is None
assert not rope.fire(player, 2)  # Unknown capability keeps the previous protection.
print("RESULTAT: native priority, option independence, wall shots, cancel and read failure OK")
