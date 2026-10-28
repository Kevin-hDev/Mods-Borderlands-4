"""Loveless's pistol reload sounds given back, in a fake game: every two seconds at most, each pistol reload found in
memory and not seen yet gets its sounds made at the catalog's instants (the magazine sounds by tag and Wwise event,
the throws by tag), each made by the game under its own reload and holding the game's type marker, which the SDK
leaves zeroed, read once on the model reload's footstep before anything is added; nothing asked of her rifle
reloads; the pistols' other events untouched; a reload seen is not asked for again while it lives, and one loaded
again is given its sounds again; a reload already holding a sound, or of another length, left alone and said once;
the model reload away: waited for, said once, nothing marked seen, the sounds given once it is there; stopping takes
away only what was added, markers of the events moved checked, and the next check adds again; a Wwise field that is
not the typed reference, a sound that does not read back, a marker that cannot be written or read, a list longer than
any reload, or an addition the game stops half done stops this for the session, what was added taken away; a list
moved field by field as it grows still ends with every marker right.
python test_reload_sounds.py"""

import copy as copying
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import reload_sound_catalog as catalog  # noqa: E402
from apex_camera_runtime import reload_sounds  # noqa: E402
from apex_camera_runtime.reload_sounds import CHECK_NS, Game, ReloadSounds  # noqa: E402

MAG_OUT, MAG_IN = "Audio.Weapon.Foley.Reload.MagOut", "Audio.Weapon.Foley.Reload.MagIn"
OUT_EVENT = "Wep_Shared_Simple_Reloads.Wep_Shared_Simple_Reloads_Out"
IN_EVENT = "Wep_Shared_Simple_Reloads.Wep_Shared_Simple_Reloads_In"
GAME_MARKER = 0x7FF6_5A2C_6DD8
fails: list[str] = []
said: list[str] = []
gone: set[int] = set()
# Every event by its address: its first 8 bytes, the game's type marker or zero.
memory: dict[int, "Event"] = {}
# The structures handed to a list's append, which the SDK copies.
handed: list["Event"] = []
made: list[tuple] = []
faults: dict[str, object] = {"untyped": False, "wwise refused": None}


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Thing:
    def __init__(self, kind: str, name: str, **fields: object) -> None:
        self.Class, self.Name = types.SimpleNamespace(Name=kind), name
        self.__dict__.update(fields)

    def _get_address(self) -> int:
        return id(self)


class Layout:
    """FAnimNotifyEvent and the structure it builds on: their fields start at byte 8."""

    def _superfields(self) -> list:
        return [types.SimpleNamespace(_properties=lambda: [types.SimpleNamespace(Offset_Internal=o) for o in (72, 80)]),
                types.SimpleNamespace(_properties=lambda: [types.SimpleNamespace(Offset_Internal=o) for o in (8, 16)])]


class Event:
    _type = Layout()

    def __init__(self, **fields: object) -> None:
        self.Notify, self.LinkValue, self.marker = None, 0.0, 0
        self.EndLink = types.SimpleNamespace(SegmentIndex=0, LinkValue=0.0)
        self.__dict__.update(fields)
        memory[id(self)] = self

    def _get_address(self) -> int:
        return id(self)


class Events(list):
    refuse = False
    # A list moved field by field when it grows or shrinks: the markers of the events moved lost.
    moves_by_fields = False

    def append(self, item: Event) -> None:
        if Events.moves_by_fields:
            for other in self:
                other.marker = 0
        # The SDK copies an added structure, field by field and its nested structures with it, into zeroed memory
        # without building it: the one in the list is not the one handed in, and only the one in the list counts.
        # Objects it points at (the sound, the animation) stay the same objects.
        handed.append(item)
        stored = Event(**{name: (copying.deepcopy(value) if name == "EndLink" else value)
                          for name, value in item.__dict__.items() if name != "marker"})
        stored.through_sdk = True
        super().append(stored)
        if self.refuse:
            raise RuntimeError("refused, the addition half done")

    def __delitem__(self, index: int) -> None:
        if Events.moves_by_fields:
            for other in self[index + 1:]:
                other.marker = 0
        super().__delitem__(index)


def game_adds(anim: Thing, notify: Thing, when: float) -> Event:
    event = Event(Notify=notify, LinkValue=when, LinkedSequence=anim, SegmentLength=anim.SequenceLength)
    event.marker = GAME_MARKER
    list.append(anim.Notifies, event)
    return event


class DefPtr:
    def __init__(self, name: str, type: object = None) -> None:
        self._name, self._type = name, type


class Audio:
    def __init__(self) -> None:
        self.bUseSoundTag, self.SoundTag, self._wwise = False, types.SimpleNamespace(TagName="None"), DefPtr("None")

    @property
    def WwiseEvent(self) -> DefPtr:
        return self._wwise

    @WwiseEvent.setter
    def WwiseEvent(self, value: DefPtr) -> None:
        if value._name != faults["wwise refused"]:
            self._wwise = DefPtr(value._name, value._type)


def sound(tag: str, wwise: str = "None") -> Thing:
    found = Thing(catalog.SOUND_CLASS, "AnimNotify_GbxAudioEvent_1", AudioEvent=Audio(),
                  NotifyType=types.SimpleNamespace(name="StandardEmitter"), EmitterTag="None", socket="None")
    found.AudioEvent.SoundTag.TagName, found.AudioEvent._wwise = tag, DefPtr(wwise)
    return found


def sequence(name: str, length: float, *events: tuple[Thing, float]) -> Thing:
    anim = Thing("AnimSequence", name, SequenceLength=length, Notifies=Events())
    for notify, when in events:
        game_adds(anim, notify, when)
    return anim


def loveless() -> dict[str, Thing]:
    """Her pistol reloads as the game's files have them."""
    return {
        "AS_PS_Reload": sequence("AS_PS_Reload", 2.8333333),
        "AS_PS_Reload_Throw": sequence("AS_PS_Reload_Throw", 1.5666667,
                                       (Thing("AnimNotify_AutoFootstep", "AnimNotify_AutoFootstep_7"), 0.2667)),
        "AS_PS_Reload_Throw_Borg": sequence("AS_PS_Reload_Throw_Borg", 2.4666667),
        "AS_PS_Reload_Throw_Forge": sequence("AS_PS_Reload_Throw_Forge", 2.9666667),
    }


world: dict[str, Thing] = {}
asked: list[str] = []
loads: list[int] = []
unwritable = False
# A sound added still without the game's marker when the game is next asked something: the window to keep short.
unmarked: list[str] = []
WWISE_DEF = types.SimpleNamespace(Name="WwiseEventDef")


def look_for_unmarked() -> None:
    if not Events.moves_by_fields and not unwritable:
        unmarked.extend(anim.Name for anim in world.values() for event in anim.Notifies
                        if getattr(event, "through_sdk", False) and event.marker != GAME_MARKER)


def find(path: str) -> Thing | None:
    look_for_unmarked()
    asked.append(path)
    return next((anim for name, anim in world.items() if path == catalog.path(name)), None)


def construct(cls: str, outer: Thing, flags: int) -> Thing:
    look_for_unmarked()
    made.append((cls, outer, flags))
    return sound("None")


def find_class(name: str) -> object:
    field = types.SimpleNamespace(Class=types.SimpleNamespace(Name="GbxDefPtrProperty"),
                                  Struct=None if faults["untyped"] else WWISE_DEF)
    audio = types.SimpleNamespace(_find_prop=lambda _name: field)
    return types.SimpleNamespace(_find_prop=lambda _name: types.SimpleNamespace(Struct=audio))


def weak(item: Thing):
    return lambda: None if id(item) in gone else item


def read(where: int, size: int) -> bytes | None:
    item = memory.get(where)
    return None if item is None else item.marker.to_bytes(size, "little")


def write(where: int, data: bytes) -> bool:
    if unwritable:
        return False
    memory[where].marker = int.from_bytes(data, "little")
    return True


def load() -> Game:
    loads.append(1)
    return Game(find, weak, read, write, said.append, construct, lambda name, **fields: Event(**fields), DefPtr,
                find_class, lambda name: types.SimpleNamespace(SpawnAttached=types.SimpleNamespace(name="SpawnAttached")))


def at(name: str) -> list[tuple[str, float]]:
    return [(event.Notify.AudioEvent.SoundTag.TagName if event.Notify.Class.Name == catalog.SOUND_CLASS
             else str(event.Notify.Name), round(event.LinkValue, 3)) for event in world[name].Notifies]


def ours() -> list[Event]:
    return [event for anim in world.values() for event in anim.Notifies
            if event.Notify.Class.Name == catalog.SOUND_CLASS]


def as_made() -> bool:
    return (at("AS_PS_Reload") == [] and at("AS_PS_Reload_Throw") == [("AnimNotify_AutoFootstep_7", 0.267)]
            and at("AS_PS_Reload_Throw_Borg") == [] and at("AS_PS_Reload_Throw_Forge") == [])


T = 10 * CHECK_NS
unit = ReloadSounds(load)
unit.sync(T)
check("no Loveless in memory: four questions to the game, nothing said", len(asked) == 4 and said == [])
check("the game's access asked for once, at the first check", loads == [1])
world.update(loveless())
unit.sync(T + CHECK_NS - 1)
check("not before two seconds", at("AS_PS_Reload") == [])

unit.sync(T + CHECK_NS)
reload_events = world["AS_PS_Reload"].Notifies
check("the reload: magazine out at 0.534 s and in at 1.501 s, each by its tag and its Wwise event",
      at("AS_PS_Reload") == [(MAG_OUT, 0.534), (MAG_IN, 1.501)]
      and [(e.Notify.AudioEvent.WwiseEvent._name, e.Notify.AudioEvent.WwiseEvent._type) for e in reload_events]
      == [(OUT_EVENT, WWISE_DEF), (IN_EVENT, WWISE_DEF)]
      and all(e.Notify.EmitterTag == "RightHand" for e in reload_events))
throws = [event for name in ("AS_PS_Reload_Throw", "AS_PS_Reload_Throw_Borg", "AS_PS_Reload_Throw_Forge")
          for event in world[name].Notifies if event.Notify.Class.Name == catalog.SOUND_CLASS]
check("each Tediore throw: the throw sound at its instant, by its tag alone, attached to the right hand, the footstep "
      "kept", at("AS_PS_Reload_Throw") == [("AnimNotify_AutoFootstep_7", 0.267), (catalog.THROW, 0.53)]
      and at("AS_PS_Reload_Throw_Borg") == [(catalog.THROW, 1.236)]
      and at("AS_PS_Reload_Throw_Forge") == [(catalog.THROW, 1.905)]
      and all(e.Notify.AudioEvent.WwiseEvent._name == "None" and e.Notify.NotifyType.name == "SpawnAttached"
              and e.Notify.socket == "RightHand" for e in throws))
check("each sound made by the game under its own pistol reload, temporary",
      [(cls, outer.Name, flags) for cls, outer, flags in made]
      == [(catalog.SOUND_CLASS, name, 0x40) for name in ("AS_PS_Reload", "AS_PS_Reload", "AS_PS_Reload_Throw",
                                                          "AS_PS_Reload_Throw_Borg", "AS_PS_Reload_Throw_Forge")])
first = reload_events[0] if reload_events else None
check("its event said to belong to the pistol reload and its length",
      first is not None and first.LinkedSequence is world["AS_PS_Reload"] and first.SegmentLength == 2.8333333
      and first.EndLink.LinkValue == first.LinkValue)
check("each sound added holds the game's type marker, the footstep its own", len(ours()) == 5
      and all(event.marker == GAME_MARKER for event in ours())
      and world["AS_PS_Reload_Throw"].Notifies[0].marker == GAME_MARKER)
check("each one from right after its addition, before the game is asked anything else", unmarked == [])
check("the marker goes on the event in the list, never on the structure handed to it, which the SDK copies",
      len(handed) == 5 and all(item.marker == 0 for item in handed))
check("nothing asked of her rifle reloads", asked and not any("/Rifle/" in path for path in asked))
check("said once per reload", len(said) == 4 and "reload sounds: Loveless AS_PS_Reload given 2 sound(s)" in said)

asked.clear()
unit.sync(T + 3 * CHECK_NS)
check("a reload seen is not asked for again while it lives, nor given again",
      asked == [] and len(ours()) == 5 and len(said) == 4)

unit.stop()
check("stopping takes away what was added, said", as_made() and "reload sounds: 5 taken away" in said[-1])
unit.sync(T + 3 * CHECK_NS + 1)
check("the next check after a stop adds again at once", len(ours()) == 5)

old = world["AS_PS_Reload"]
gone.add(id(old))
world["AS_PS_Reload"] = sequence("AS_PS_Reload", 2.8333333)
unit.sync(T + 5 * CHECK_NS)
check("a reload loaded again, a new object, given its sounds again",
      at("AS_PS_Reload") == [(MAG_OUT, 0.534), (MAG_IN, 1.501)] and len(old.Notifies) == 2)
gone.clear()
unit.stop()
check("stopping then takes away from the reload alive, not from the one gone", as_made() and len(old.Notifies) == 2)

said.clear()
game_adds(world["AS_PS_Reload"], sound(MAG_IN), 1.5)
world["AS_PS_Reload_Throw_Borg"].SequenceLength = 3.0
unit.sync(T + 7 * CHECK_NS)
unit.sync(T + 9 * CHECK_NS)
check("a reload already holding a sound, or of another length: left alone, said once",
      at("AS_PS_Reload") == [(MAG_IN, 1.5)] and at("AS_PS_Reload_Throw_Borg") == []
      and sum("AS_PS_Reload already has a sound; left alone" in line for line in said) == 1
      and sum("AS_PS_Reload_Throw_Borg lasts 3.000 s, not 2.467 s; left alone" in line for line in said) == 1
      and len(ours()) == 3)
unit.stop()
check("stopping keeps the game's own sound", at("AS_PS_Reload") == [(MAG_IN, 1.5)])
list.clear(world["AS_PS_Reload"].Notifies)
world["AS_PS_Reload_Throw_Borg"].SequenceLength = 2.4666667

said.clear()
model = world.pop(catalog.MODEL)
waiting = ReloadSounds(load)
waiting.sync(T)
waiting.sync(T + 2 * CHECK_NS)
check("the model reload away: waited for, said once, nothing given, nothing marked seen",
      ours() == [] and waiting.seen == {} and not waiting.failed
      and sum(f"waiting for {catalog.MODEL}" in line for line in said) == 1)
world[catalog.MODEL] = model
waiting.sync(T + 4 * CHECK_NS)
check("once it is there, the sounds given", len(ours()) == 5 and all(event.marker == GAME_MARKER for event in ours()))
waiting.stop()

Events.moves_by_fields = True
unit.sync(T + 17 * CHECK_NS)
footstep = world["AS_PS_Reload_Throw"].Notifies[0]
check("a list moved field by field as it grows: every marker right in the end, the game's events' too",
      len(ours()) == 5 and all(event.marker == GAME_MARKER for event in ours()) and footstep.marker == GAME_MARKER)
after = game_adds(world["AS_PS_Reload_Throw"], Thing("AnimNotify_Trick", "AnimNotify_Trick_0"), 1.0)
unit.stop()
check("an event after ours, moved when ours goes: kept, its marker right",
      list(world["AS_PS_Reload_Throw"].Notifies)[-1] is after and after.marker == GAME_MARKER
      and at("AS_PS_Reload_Throw") == [("AnimNotify_AutoFootstep_7", 0.267), ("AnimNotify_Trick_0", 1.0)])
Events.moves_by_fields = False
world["AS_PS_Reload_Throw"].Notifies[:] = [event for event in world["AS_PS_Reload_Throw"].Notifies if event is not after]


def stopped_by(label: str, prepare, undo) -> None:
    """A failure: stopped for the session, what was added taken away, said; later checks do nothing."""
    trial = ReloadSounds(load)
    said.clear()
    prepare()
    trial.sync(T)
    undo()
    trial.sync(T + 2 * CHECK_NS)
    check(label, trial.failed and as_made() and any("stopped for the session" in line for line in said))


def refuse_marker() -> None:
    global unwritable
    unwritable = True


def allow_marker() -> None:
    global unwritable
    unwritable = False


stopped_by("a Wwise field that is not the typed reference", lambda: faults.update(untyped=True),
           lambda: faults.update(untyped=False))
stopped_by("a sound that does not read back, the one added before it taken away",
           lambda: faults.update({"wwise refused": IN_EVENT}), lambda: faults.update({"wwise refused": None}))
stopped_by("a marker that cannot be written", refuse_marker, allow_marker)
crowded = world["AS_PS_Reload_Throw_Forge"]
stopped_by("a list longer than any reload",
           lambda: [game_adds(crowded, Thing("AnimNotify_Trick", "AnimNotify_Trick_0"), 0.1) for _ in range(17)],
           lambda: list.clear(crowded.Notifies))
source = world[catalog.MODEL].Notifies[0]
stopped_by("the game's marker unreadable", lambda: memory.pop(id(source)), lambda: memory.update({id(source): source}))
world["AS_PS_Reload_Throw_Forge"].Notifies.refuse = True
stopped_by("an addition the game stops half done", lambda: None, lambda: None)
world["AS_PS_Reload_Throw_Forge"].Notifies.refuse = False


def no_access() -> Game:
    raise ImportError("no FGbxDefPtr in this SDK")


told: list[str] = []
cut_off = ReloadSounds(no_access, told.append)
cut_off.sync(T)
cut_off.sync(T + 2 * CHECK_NS)
check("the game's access out of reach: stopped for the session, said once all the same, nothing added",
      cut_off.failed and as_made() and told == ["reload sounds stopped for the session: ImportError: no FGbxDefPtr in "
                                                "this SDK"])

# The way the game builds it (shared.py): the default log and the real access, on an SDK standing in for the game's.
logged: list[str] = []
fake_logging = types.ModuleType("unrealsdk.logging")
fake_logging.info = logged.append
fake_unreal = types.ModuleType("unrealsdk.unreal")
fake_unreal.FGbxDefPtr, fake_unreal.WeakPointer = DefPtr, weak
fake_sdk = types.ModuleType("unrealsdk")
fake_sdk.logging, fake_sdk.unreal = fake_logging, fake_unreal
for name in ("find_object", "construct_object", "make_struct", "find_class", "find_enum"):
    setattr(fake_sdk, name, lambda *args, **kwargs: None)
sys.modules.update({"unrealsdk": fake_sdk, "unrealsdk.logging": fake_logging, "unrealsdk.unreal": fake_unreal})
check("the game's access writes its lines in the same log as a failure to reach it",
      reload_sounds.game_modules().log is reload_sounds.log_line)
del fake_unreal.FGbxDefPtr
in_game = ReloadSounds(reload_sounds.game_modules)
in_game.sync(T)
in_game.sync(T + 2 * CHECK_NS)
check("in the game, an SDK without its typed reference: said once, in the camera runtime's log",
      in_game.failed and len(logged) == 1
      and logged[0].startswith("[Camera Runtime] reload sounds stopped for the session: ImportError: ")
      and "FGbxDefPtr" in logged[0])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
