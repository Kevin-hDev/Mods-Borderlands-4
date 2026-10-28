"""The rope follows the measured socket and safely falls back when it cannot be read."""

import importlib.util
import sys
import types

import sdk_stubs

state = sdk_stubs.install()
from apex_grapple import arms, beam, game, rope_visuals

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
position = types.SimpleNamespace(X=50, Y=60, Z=170)
calls = []
mesh = types.SimpleNamespace(
    DoesSocketExist=lambda name: True,
    GetSocketLocation=lambda name: (calls.append(name), position)[1],
)
arms.find = lambda character: types.SimpleNamespace(Outer=mesh)
rope_visuals.reset()
check("the beam origin uses the actual animated socket", game.hand_spot(player) == (50, 60, 170))
position.X = -20
check("the socket follows the hand on the next frame", game.hand_spot(player) == (-20, 60, 170))
beam.start(player, (1500, 0, 170))
check("spawning also uses the same socket", beam._component.world_spot == (-20, 60, 170))
beam.stop()

if importlib.util.find_spec("apex_grapple.hand_anchor") is not None:
    from apex_grapple import hand_anchor

    scans = []
    arms.find = lambda character: (scans.append(character), types.SimpleNamespace(Outer=mesh))[1]
    hand_anchor.reset()
    for _ in range(20):
        game.hand_spot(player)
    check("one mesh lookup serves all frames in a shot", len(scans) == 1)
    position.X = float("nan")
    check("invalid socket coordinates fall back to finite placement", game.hand_spot(player) == (0, 30, 135))
    before = len(calls)
    game.hand_spot(player)
    check("a failed socket is not retried every frame", len(calls) == before)
    position.X = 80
    hand_anchor.reset()
    check("a new shot can recover its hand", game.hand_spot(player) == (80, 60, 170))
    other = sdk_stubs.FakeCharacter()
    game.hand_spot(other)
    check("a changed character invalidates the mesh", len(scans) == 3)
    hand_anchor.reset()
    mesh.DoesSocketExist = lambda name: False
    before = len(calls)
    check("missing sockets preserve the old fallback", game.hand_spot(player) == (0, 30, 135))
    check("a missing socket is never queried", len(calls) == before)
else:
    check("the bounded hand reader exists", False)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
