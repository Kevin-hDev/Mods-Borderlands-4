"""A completed Deactivate call must not require synchronous Niagara destruction."""

import sys

import sdk_stubs

state = sdk_stubs.install()
from apex_grapple import beam, beam_cleanup, game

failures = []
ANCHOR = (2500, 0, 160)
player = sdk_stubs.FakeCharacter()
state["pc"] = sdk_stubs.player(player, state["mappings"])
game.refresh(0, at_once=True)


def check(label, passed):
    print(("OK" if passed else "FAIL") + " | " + label)
    if not passed:
        failures.append(label)


def unavailable(*args):
    raise AttributeError("destruction unavailable")


for still_active in (False, True):
    for destroy_raises in (False, True):
        before = len(state["niagara"].spawned)
        for shot in range(3):
            beam.start(player, ANCHOR)
            component = beam._component
            label = f"active={still_active}, destroy_raises={destroy_raises}, shot={shot}"
            check(f"a new beam is activated: {label}",
                  component is not None and component.activations == 1)
            if component is None:
                continue
            component.IsActive = lambda: still_active
            component.IsBeingDestroyed = lambda: False
            component.GetOwner = lambda: player
            component.K2_DestroyComponent = unavailable if destroy_raises else lambda owner: None
            component.DestroyComponent = unavailable
            # Both snapshots occur in session_155332.log: active may remain true after return.
            if shot == 1:
                beam.reset()
            else:
                beam.stop()
            check(f"release hands the beam to Niagara destruction: {label}", component.bAutoDestroy)
            check(f"accepted deactivation permits another shot: {label}", beam_cleanup.retry())
        check(f"three shots created three beams: active={still_active}, raises={destroy_raises}",
              len(state["niagara"].spawned) - before == 3)
        # Simulate eventual engine collection before the next independent scenario.
        if beam_cleanup._pending is not None:
            beam_cleanup._pending().destroyed = True
        beam.reset()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not failures else f"{len(failures)} ECHEC(S)")
sys.exit(bool(failures))
