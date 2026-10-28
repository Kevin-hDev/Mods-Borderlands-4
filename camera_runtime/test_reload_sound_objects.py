"""One reload sound made as the game makes its own, in a fake game: the Wwise field's type taken only when it is the
typed reference the files show; a magazine sound constructed by the game under its pistol reload, temporary, by its
tag and its Wwise event typed as the field's own, from the right hand; a throw by its tag alone, attached to the right
hand; a write that does not hold refused; the event with the fields the game's own carry.
python test_reload_sound_objects.py"""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import reload_sound_catalog as catalog  # noqa: E402
from apex_camera_runtime import reload_sound_objects as objects  # noqa: E402
from apex_camera_runtime.reload_sounds import Game  # noqa: E402

fails: list[str] = []
made: list[tuple] = []
# Fields whose writes the fake game drops, to see a write that does not hold.
dropped: set[str] = set()


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Prop:
    def __init__(self, kind: str, struct: object = None) -> None:
        self.Class, self.Struct = types.SimpleNamespace(Name=kind), struct


class Kind:
    def __init__(self, name: str, **props: Prop) -> None:
        self.Name, self.props = name, props

    def _find_prop(self, name: str) -> Prop:
        return self.props[name]


WWISE_DEF = Kind("WwiseEventDef")


def audio_class(field: Prop) -> Kind:
    return Kind(catalog.SOUND_CLASS, AudioEvent=Prop("StructProperty", Kind("GbxAudioEventDef", WwiseEvent=field)))


class DefPtr:
    def __init__(self, name: str, type: object = None) -> None:
        self._name, self._type = name, type


class Fields:
    """A structure of the game whose later writes are dropped for the fields named in dropped."""

    def __init__(self, **values: object) -> None:
        for name, value in values.items():
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: object) -> None:
        if name not in dropped:
            object.__setattr__(self, name, value)


def construct(cls: str, outer: object, flags: int) -> Fields:
    made.append((cls, outer, flags))
    sound = Fields(bUseSoundTag=False, WwiseEvent=DefPtr("None"), SoundTag=Fields(TagName="None"))
    return Fields(Outer=outer, AudioEvent=sound, NotifyType=types.SimpleNamespace(name="StandardEmitter"),
                  EmitterTag="None", socket="None")


def made_or_none(row: catalog.Made, kind: object) -> Fields | None:
    try:
        return objects.make_sound(game, anim, row, kind)
    except RuntimeError as error:
        check(f"{row.tag} made without a refusal ({error})", False)
        return None


classes = {catalog.SOUND_CLASS: audio_class(Prop("GbxDefPtrProperty", WWISE_DEF))}
game = Game(None, None, None, None, None, construct,
            lambda name, **fields: types.SimpleNamespace(name=name, EndLink=types.SimpleNamespace(), **fields),
            DefPtr, lambda name: classes[name],
            lambda name: types.SimpleNamespace(SpawnAttached=types.SimpleNamespace(name="SpawnAttached")))
anim = types.SimpleNamespace(Name="AS_PS_Reload", SequenceLength=2.8333333)
rows = catalog.pistols()

kind = objects.wwise_type(game)
check("the Wwise field's type: the typed reference's own", kind is WWISE_DEF)
for label, field in (("untyped", Prop("GbxDefPtrProperty")), ("not a reference", Prop("StructProperty", WWISE_DEF))):
    classes[catalog.SOUND_CLASS] = audio_class(field)
    check(f"a Wwise field {label}: no type", objects.wwise_type(game) is None)
classes[catalog.SOUND_CLASS] = audio_class(Prop("GbxDefPtrProperty", WWISE_DEF))

out = made_or_none(rows["AS_PS_Reload"][0], kind)
check("a magazine sound constructed by the game under its pistol reload, temporary",
      made == [(catalog.SOUND_CLASS, anim, 0x40)] and out is not None and out.Outer is anim)
check("by its tag and its Wwise event, typed as the field's own",
      out is not None and out.AudioEvent.bUseSoundTag is True
      and out.AudioEvent.SoundTag.TagName == "Audio.Weapon.Foley.Reload.MagOut"
      and out.AudioEvent.WwiseEvent._name == "Wep_Shared_Simple_Reloads.Wep_Shared_Simple_Reloads_Out"
      and out.AudioEvent.WwiseEvent._type is WWISE_DEF)
check("from the right hand, its emitter, as her rifle's",
      out is not None and out.EmitterTag == "RightHand" and out.NotifyType.name == "StandardEmitter"
      and out.socket == "None")
thrown = made_or_none(rows["AS_PS_Reload_Throw"][0], kind)
check("a throw by its tag alone, attached to the right hand, as her rifle's throws",
      thrown is not None and thrown.AudioEvent.SoundTag.TagName == catalog.THROW
      and thrown.AudioEvent.WwiseEvent._name == "None" and thrown.NotifyType.name == "SpawnAttached"
      and thrown.socket == "RightHand" and thrown.EmitterTag == "None")

for field, row in (("WwiseEvent", rows["AS_PS_Reload"][1]), ("TagName", rows["AS_PS_Reload"][1]),
                   ("bUseSoundTag", rows["AS_PS_Reload"][1]), ("EmitterTag", rows["AS_PS_Reload"][1]),
                   ("socket", rows["AS_PS_Reload_Throw"][0]), ("NotifyType", rows["AS_PS_Reload_Throw"][0])):
    dropped.add(field)
    try:
        objects.make_sound(game, anim, row, kind)
        refused = False
    except RuntimeError as error:
        refused = "does not read back as written" in str(error)
    dropped.discard(field)
    check(f"a write of {field} that does not hold: refused", refused)

event = objects.make_event(game, anim, out, 0.53371465)
check("the event with the fields the game's own carry",
      event.name == "AnimNotifyEvent" and event.NotifyName == "GbxAudioEvent" and event.Notify is out
      and event.TriggerWeightThreshold == 1e-05 and event.NotifyTriggerChance == 1.0
      and event.bCanBeFilteredViaRequest is True and event.bTriggerOnDedicatedServer is True
      and event.SegmentLength == 2.8333333 and event.LinkValue == 0.53371465 and event.LinkedSequence is anim
      and getattr(event.EndLink, "SegmentIndex", None) == -1 and getattr(event.EndLink, "LinkValue", None) == 0.53371465)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
