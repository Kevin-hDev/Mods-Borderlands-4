"""Mechanical sounds follow the rope once; faults remain isolated from movement."""

import types
import sdk_stubs

state = sdk_stubs.install()
calls, stopped = [], []
fail_play = fail_stop = False


def post(**kwargs):
    if fail_play:
        raise RuntimeError("play failed")
    calls.append(kwargs)
    return len(calls)


def stop(**kwargs):
    if fail_stop:
        raise RuntimeError("stop failed")
    stopped.append(kwargs["PlaybackInstance"])


library = types.SimpleNamespace(PostWwiseEventOnActor=post, Stop=stop)
state["extra_classes"]["GbxAudioBlueprintFunctionLibrary"] = types.SimpleNamespace(ClassDefaultObject=library)
import unrealsdk
unrealsdk.unreal.FGbxDefPtr = lambda name, kind: types.SimpleNamespace(_name=name, kind=kind)
from apex_grapple import game, rope_audio

player = sdk_stubs.FakeCharacter()
game.character = lambda: player
rope_audio.reset()
rope_audio.start(player)
assert len(calls) == 1 and calls[-1]["Event"].WwiseEvent._name.endswith("_Shot")
rope_audio.pull(player)
assert len(calls) == 1, "No pull sound before contact"
rope_audio.attach()
rope_audio.attach()
assert len(calls) == 2 and calls[-1]["Event"].WwiseEvent._name.endswith("_Connect")
rope_audio.pull(player)
rope_audio.pull(player)
assert len(calls) == 3 and calls[-1]["Event"].WwiseEvent._name.endswith("_Pull")
rope_audio.stop()
assert stopped == [1, 2, 3]
rope_audio.attach()
rope_audio.pull(player)
assert len(calls) == 3, "Release cancels pending stages"
rope_audio.start(player)
rope_audio.stop()
rope_audio.pull(player)
assert len(calls) == 4, "Cancel during flight suppresses contact and pull"
rope_audio.start(player)
replacement = sdk_stubs.FakeCharacter()
game.character = lambda: replacement
rope_audio.attach()
assert len(calls) == 5, "Never use old character after replacement"
rope_audio.reset()
game.character = lambda: player
fail_play = True
rope_audio.start(player)
rope_audio.attach()
rope_audio.pull(player)
assert len(calls) == 5
fail_play = False
rope_audio.start(player)
assert len(calls) == 5, "Keep failed audio off until lifecycle reset"
rope_audio.reset()
rope_audio.start(player)
assert len(calls) == 6
fail_stop = True
rope_audio.stop()
fail_stop = False
rope_audio.start(player)
assert len(calls) == 6, "No stacking after cleanup failure"
rope_audio.reset()
rope_audio.start(player)
assert len(calls) == 7
rope_audio.stop()
print("RESULTAT: audio order, once-only stages, cancel, character change and isolated errors OK")
