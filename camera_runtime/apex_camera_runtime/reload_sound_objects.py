"""One reload sound of the catalog (reload_sound_catalog.py) made as the game makes its own: a sound object and the
animation event that plays it. game: reload_sounds.Game.

The sound object is an AnimNotify_GbxAudioEvent constructed by the game under the pistol reload, held by the event
only: when the game swept its memory, ours stayed, and they go with their animation (trial 14, 2026-10-25). Its Wwise
event is a reference written by name and the field's own type (FGbxDefPtr), as the game's files show it; the field is
first checked to be that typed reference, a typed reference given where none is expected having crashed the game
(2026-09-28). What is written is read back.

The event is a structure of ours with the fields the game's own carry (read in the files). The SDK leaves its C++ type
marker zeroed: it is written once the event is in the animation's list (event_marker.py).
"""

from typing import Any

from . import reload_sound_catalog as catalog

TRANSIENT = 0x40
# How the SDK reads a reference that names nothing.
EMPTY = "None"


def wwise_type(game: Any) -> Any | None:
    """The type the sound's Wwise event field holds; None when it is not the typed reference the game's files show."""
    sound = game.find_class(catalog.SOUND_CLASS)._find_prop("AudioEvent").Struct
    field = sound._find_prop("WwiseEvent")
    return field.Struct if str(field.Class.Name) == "GbxDefPtrProperty" else None


def make_sound(game: Any, anim: Any, row: catalog.Made, kind: Any) -> Any:
    """kind: wwise_type()'s answer."""
    notify = game.construct(catalog.SOUND_CLASS, anim, TRANSIENT)
    notify.AudioEvent.bUseSoundTag = True
    notify.AudioEvent.SoundTag.TagName = row.tag
    if row.wwise is not None:
        notify.AudioEvent.WwiseEvent = game.def_ptr(row.wwise, kind)
    thrown = row.tag == catalog.THROW
    if thrown:
        notify.NotifyType = game.find_enum("EGbxAudioNotifyType").SpawnAttached
        notify.socket = catalog.HAND
    else:
        notify.EmitterTag = catalog.HAND
    audio = notify.AudioEvent
    if thrown:
        emitted = notify.NotifyType.name == "SpawnAttached" and str(notify.socket) == catalog.HAND
    else:
        emitted = str(notify.EmitterTag) == catalog.HAND
    written = (emitted and bool(audio.bUseSoundTag) and str(audio.SoundTag.TagName) == row.tag
               and str(audio.WwiseEvent._name) == (row.wwise or EMPTY))
    if not written:
        raise RuntimeError(f"a sound for {row.pistol} does not read back as written")
    return notify


def make_event(game: Any, anim: Any, notify: Any, at: float) -> Any:
    event = game.make_struct(
        "AnimNotifyEvent", NotifyName="GbxAudioEvent", Notify=notify, TriggerWeightThreshold=1e-05,
        NotifyTriggerChance=1.0, bCanBeFilteredViaRequest=True, bTriggerOnDedicatedServer=True,
        SegmentLength=anim.SequenceLength, LinkValue=at, LinkedSequence=anim)
    event.EndLink.SegmentIndex = -1
    event.EndLink.LinkValue = at
    return event
