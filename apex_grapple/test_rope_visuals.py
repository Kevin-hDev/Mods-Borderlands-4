"""The optional visual layer must respect the menu and isolate a missing hand transform."""

import sys

import sdk_stubs

state = sdk_stubs.install()
from apex_grapple import beam, game, rope_visuals, settings

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
state["pc"] = sdk_stubs.player(player, state["mappings"])
game.refresh(0, at_once=True)
settings.show_rope.value = False
rope_visuals.start(player, (1000, 0, 0))
rope_visuals.follow(player, (1000, 0, 0))
check("hidden visuals spawn no beam", not state["niagara"].spawned)
settings.show_rope.value = True
rope_visuals.start(player, (1000, 0, 0))
component = beam._component


def missing_hand(character):
    raise RuntimeError("hand disappeared")


game.hand_spot = missing_hand
rope_visuals.follow(player, (1000, 0, 0))
rope_visuals.follow(player, (1000, 0, 0))
check("a failed hand lookup releases the visual", component in state["destroyed"])
check("the failure is reported once", sum("RuntimeError('hand disappeared')" in line for line in state["errors"]) == 1)
rope_visuals.start(player, (1000, 0, 0))
check("a broken visual does not keep spawning", len(state["niagara"].spawned) == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
