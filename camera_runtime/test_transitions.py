"""Camera transitions are rewritten only for the local player."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.transitions import TransitionHooks  # noqa: E402
from camera_test_fixtures import Bound, Hooks, args  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


hooks, player, stranger = Hooks(), object(), object()
changes = []
transitions = TransitionHooks(hooks, "camera", player, lambda *_: None,
                              lambda requested, effective: changes.append((requested, effective)))
transitions.install()
path = next(path for path in transitions.paths if path.endswith(":CameraTransition"))
callback = hooks.items[(path, "PRE", "camera")]
bound = Bound()
check("another controller's transition is untouched", callback(stranger, args("Slide"), None, bound) is None
      and bound.calls == [])
check("the player's slide stays in third person", callback(player, args("Slide"), None, bound) is hooks.Block
      and bound.calls[0][0] == "ThirdPerson")
transitions.set_first_person_allowed(True)
aim = Bound()
check("the player's native first-person mode is preserved while aiming",
      callback(player, args("Default"), None, aim) is None and aim.calls == [])
aim_slide = Bound()
check("the player's native slide mode is preserved while aiming",
      callback(player, args("Slide"), None, aim_slide) is None and aim_slide.calls == [])
transitions.set_first_person_allowed(False)
release = Bound()
check("the player's default mode returns to third person after aiming",
      callback(player, args("Default"), None, release) is hooks.Block
      and release.calls[0][0] == "ThirdPerson")
vehicle = Bound()
check("the player's vehicle camera is preserved",
      callback(player, args("ThirdPersonVehicle"), None, vehicle) is None and vehicle.calls == [])
transitions.remove()
check("transition cleanup removes every owned hook", hooks.items == {})

wrapped_a = types.SimpleNamespace(_get_address=lambda: 123)
wrapped_b = types.SimpleNamespace(_get_address=lambda: 123)
same_pointer = TransitionHooks(hooks, "pointer", wrapped_a, lambda *_: None, lambda *_: None)
same_pointer.install()
pointer_callback = hooks.items[(path, "PRE", "pointer")]
check("another SDK wrapper for the same controller is still scoped as the player",
      pointer_callback(wrapped_b, args("Default"), None, Bound()) is hooks.Block)
same_pointer.remove()

live_actor = types.SimpleNamespace(
    ZoomState=types.SimpleNamespace(bWantsToZoom=True))
live_player = types.SimpleNamespace(OakCharacter=live_actor)
live_hooks = Hooks()
live = TransitionHooks(live_hooks, "live", live_player, lambda *_: None, lambda *_: None)
live.install()
live_callback = live_hooks.items[(path, "PRE", "live")]
check("a live aim request preserves Default before the next camera sync",
      live_callback(live_player, args("Default"), None, Bound()) is None)
live_actor.ZoomState.bWantsToZoom = False
check("the live aim exception ends as soon as the input is released",
      live_callback(live_player, args("Default"), None, Bound()) is live_hooks.Block)
live.remove()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
