"""Real rope transitions trigger audio while preserving visual and input options."""

from types import SimpleNamespace as NS

from grapple_fixture import fresh, state, SECOND, settings
from apex_grapple import frame, game, rope_audio, rope_visuals


def names():
    return [request["Event"].WwiseEvent._name.rsplit("_", 1)[-1]
            for request, _ in state["audio_calls"]]


player, rope = fresh(on_ground=False)
settings.show_rope.value = False
assert rope.fire(player, 0)
assert names() == ["Shot"]
rope.update(player, int(0.2 * SECOND))
assert names() == ["Shot", "Connect"]
rope.update(player, int(0.21 * SECOND))
rope.update(player, int(0.22 * SECOND))
assert names() == ["Shot", "Connect", "Pull"]
rope.let_go("test", int(0.23 * SECOND))
assert len(state["audio_stops"]) == 3
state["audio_calls"].clear()
state["audio_stops"].clear()
player, rope = fresh(on_ground=False)
state["pc"].GrappleTargetingStrategy = NS(BestValidTarget=NS(Grappleable=NS(Class=NS(Name="CarryableObject"))))
assert not rope.fire(player, 0)
assert names() == [], "Native objects must retain their own sounds"
state["pc"].GrappleTargetingStrategy.BestValidTarget.Grappleable = None
assert rope.fire(player, SECOND)
rope.let_go("jump", int(1.1 * SECOND))
rope.update(player, 2 * SECOND)
assert names() == ["Shot"], "Cancellation must not start pending contact/pull"
state["audio_calls"].clear()
player, rope = fresh(on_ground=False)
assert rope.fire(player, 0)
game.forget()
rope.reset()
assert not rope.busy and not rope_audio._handles
player, rope = fresh(on_ground=False)
state["audio_calls"].clear()
assert rope.fire(player, 0)
assert names() == ["Shot"], "Next session must recover"
rope.reset()

# Broken audio still leaves both gameplay and the existing visual layer running.
player, rope = fresh(on_ground=False)
def unavailable(**kwargs):
    raise RuntimeError("missing audio")
state["extra_classes"]["GbxAudioBlueprintFunctionLibrary"] = NS(ClassDefaultObject=NS(PostWwiseEventOnActor=unavailable))
settings.show_rope.value = True
assert rope.fire(player, 0) and rope.busy
assert rope_visuals._active
rope.update(player, int(0.2 * SECOND))
assert rope.holds
rope.reset()
print("RESULTAT: rope audio with hidden visuals, native priority, cancel, new session and audio failure OK")
