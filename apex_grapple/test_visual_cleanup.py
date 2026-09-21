"""Owned resources must stop on reset without stopping a successor's animation."""

import sys
import types

import sdk_stubs

state = sdk_stubs.install()
from apex_grapple import animation, beam, game, rope_visuals

fails = []


def check(label, condition):
    print(("OK" if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Hands(sdk_stubs.FakeArms):
    def __init__(self, player):
        super().__init__(player)
        self.active = None
        self.targeted = []

    def PlaySlotAnimationAsDynamicMontage(self, **kwargs):
        super().PlaySlotAnimationAsDynamicMontage(**kwargs)
        self.active = types.SimpleNamespace(asset=kwargs["Asset"])
        return self.active

    def Montage_Stop(self, blend, montage):
        self.targeted.append(montage)
        if self.active is montage:
            self.active = None

    def StopSlotAnimation(self, blend, slot):
        super().StopSlotAnimation(blend, slot)
        self.active = None


def setup():
    rope_visuals.reset()
    player = sdk_stubs.FakeCharacter()
    hands = Hands(player)
    state["anim_instances"] = [hands]
    state["pc"] = sdk_stubs.player(player, state["mappings"])
    game.refresh(0, at_once=True)
    return player, hands


player, hands = setup()
rope_visuals.start(player, (2500, 0, 160))
rope_visuals.hold()
held = hands.active
component = beam._component
rope_visuals.reset()
check("reset stops the held hand montage", hands.active is None and held in hands.targeted)
check("reset releases the beam", component in state["destroyed"])

player, old_hands = setup()
animation.start()
old_montage = old_hands.active
replacement = sdk_stubs.FakeCharacter()
new_hands = Hands(replacement)
state["anim_instances"] = [new_hands]
state["pc"] = sdk_stubs.player(replacement, state["mappings"])
game.refresh(1_000_000_000, at_once=True)
animation.reset()
check("owner changes stop the old arms rather than the new arms",
      old_hands.active is None and old_montage in old_hands.targeted and not new_hands.targeted)

player, hands = setup()
animation.start()
animation.hold()
owned = hands.active
successor = hands.active = types.SimpleNamespace(asset="wall climb")
animation.stop()
check("a successor's montage remains active", hands.active is successor)
check("only the owned montage is stopped", hands.targeted == [owned] and not hands.stopped)

player, hands = setup()
state["anim_instances"] = []
animation.reset()
animation.start()
state["anim_instances"] = [hands]
animation.hold()
owned = hands.active
animation.stop()
check("late arms are tracked and released", owned is not None and hands.active is None)

player, hands = setup()
beam.start(player, (2500, 0, 160))
component = beam._component


def refuse():
    raise RuntimeError("temporary release failure")


component.Deactivate = refuse
beam.stop()
check("deactivation failure does not prevent destruction", component in state["destroyed"])

player, hands = setup()
beam.start(player, (2500, 0, 160))
component = beam._component
component.Deactivate = component.DestroyComponent = refuse
beam.stop()
before = len(state["niagara"].spawned)
beam.start(player, (2500, 0, 160))
check("failed cleanup cannot accumulate new components", len(state["niagara"].spawned) == before)
component.Deactivate = lambda: setattr(component, "alive", False)
component.DestroyComponent = lambda: (state["destroyed"].append(component), setattr(component, "destroyed", True))
beam.reset()
check("reset retries an earlier failed cleanup", component in state["destroyed"])

player, hands = setup()
animation.start()
stop = hands.Montage_Stop
hands.Montage_Stop = lambda *args: refuse()
animation.reset()
before = len(hands.played)
animation.hold()
check("a failed montage release cannot be replaced by an untracked held pose", len(hands.played) == before)
hands.Montage_Stop = stop
animation.stop()
check("an unsuccessful hand release is retried", hands.active is None)

player, hands = setup()
animation.start()
animation.stop()
replacement = Hands(player)
hands.Outer.GetAnimInstance = lambda: replacement
state["anim_instances"] = [replacement]
animation.start()
check("replaced first-person arms are acquired on the same character", len(replacement.played) == 1)

player, hands = setup()
animation.start()
animation.stop()
hands.destroyed = True
replacement = Hands(player)
state["anim_instances"] = [replacement]
animation.start()
check("destroyed cached arms are not reused", len(replacement.played) == 1)

player, hands = setup()
beam.start(player, (2500, 0, 160))
component = beam._component
component.DestroyComponent = refuse
owner = object()
component.GetOwner = lambda: owner
passed = []


def remove_component(caller):
    passed.append(caller)
    component.destroyed = True


component.K2_DestroyComponent = remove_component
beam.stop()
check("the reflected destruction receives the component's owning actor", passed == [owner])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
