"""Normal shots must retain visuals without class scans, particle scans or observer hooks."""

import sys

import sdk_stubs

state = sdk_stubs.install()
# Make observer functions discoverable so an accidental registration cannot hide in the fake SDK.
import unrealsdk

find_object = unrealsdk.find_object
unrealsdk.find_object = lambda kind, path: object() if kind == "Function" else find_object(kind, path)
from apex_grapple import beam, frame, game, keys, mod, settings
from unrealsdk.hooks import Block

SECOND = 1_000_000_000
DIAGNOSTIC_MARKERS = ("grapple data |", "grapple open |", "rope asset |", "rope probe |",
                      "rope dump |", "beam call |", "beam identity |", "hand socket |", "beam local pose |")
failures = []


def check(label, passed):
    print(("OK" if passed else "FAIL") + " | " + label)
    if not passed:
        failures.append(label)


check("only the gameplay frame hook is registered", mod.kwargs["hooks"] == [frame.tick])
settings.grapple_range.value = 3000
state["kismet"].hit = (2000.0, "StaticMeshActor")
for session in range(3):
    frame.stop()
    player = sdk_stubs.FakeCharacter()
    hands = sdk_stubs.FakeArms(player)
    hands.Outer.DoesSocketExist = lambda name: True
    hands.Outer.GetSocketLocation = lambda name: sdk_stubs.vector(0, 0, 160)
    state["anim_instances"] = [hands]
    state["pc"] = sdk_stubs.player(player, state["mappings"])
    now = (session * 10 + 1) * SECOND
    keys.time.perf_counter_ns = lambda: now
    frame.on_frame(player.anim, now)
    for shot in range(2):
        now += SECOND
        taken = state["keybinds"]["V"](sdk_stubs.event("IE_Pressed"))
        component = beam._component
        check(f"session {session} shot {shot} starts hands and beam",
              taken is Block and bool(hands.played) and component is not None and component.activations == 1)
        now += SECOND
        frame.on_frame(player.anim, now)
        check(f"session {session} shot {shot} reaches the held pose", frame.rope.holds)
        state["keybinds"]["V"](sdk_stubs.event("IE_Released"))
        check(f"session {session} shot {shot} releases its component", component in state["destroyed"])
    state["pc"].OakCharacter = None
    frame.on_frame(player.anim, now + SECOND)

check("no global class or particle observation scans",
      not any(name in ("Class", "NiagaraComponent") for name in state["find_all_calls"]))
check("no detailed investigation output", not any(
    marker in line for line in state["misc"] for marker in DIAGNOSTIC_MARKERS))
check("no runtime errors", not state["errors"])
check("normal shots retain the activation lifetime parameter",
      component.floats_at_activation == {"User.Lifetime": 10.0})
frame.stop()
print("RESULTAT:", "TOUS LES TESTS PASSENT" if not failures else f"{len(failures)} ECHEC(S)")
sys.exit(bool(failures))
