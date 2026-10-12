"""Tests the game's body channel aimed where the mod turns the body: asked again only when the body turns, given back
when the mod lets go, to the right hunter, and left to the game for the session after a refused call (2026-10-12)."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import body_channel  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Library:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.refuse_aim = self.refuse_default = False

    def SetRotationTargetRotation(self, Actor, ChannelTag, InRotation) -> None:
        self.calls.append(("aim", Actor.name, ChannelTag, (InRotation.Pitch, InRotation.Yaw, InRotation.Roll)))
        if self.refuse_aim:
            raise RuntimeError("refused")

    def SetRotationTargetDefault(self, Actor, ChannelTag) -> None:
        self.calls.append(("default", Actor.name, ChannelTag))
        if self.refuse_default:
            raise RuntimeError("refused")


def hunter(name: str, address: int) -> types.SimpleNamespace:
    return types.SimpleNamespace(name=name, _get_address=lambda: address)


class Pointer:
    """As unrealsdk's WeakPointer: None once the object is gone."""

    def __init__(self, target) -> None:
        self.target = target

    def __call__(self):
        return self.target


def make(library: Library):
    found, lines, pointers = [], [], []

    def find_class(name):
        found.append(name)
        if library is None:
            raise ValueError("no such class")
        return types.SimpleNamespace(ClassDefaultObject=library)

    def weak(target):
        pointers.append(Pointer(target))
        return pointers[-1]

    channel = body_channel.BodyChannel(find_class, lambda name: f"tag:{name}",
                                       lambda p, y, r: types.SimpleNamespace(Pitch=p, Yaw=y, Roll=r), weak,
                                       lines.append)
    return channel, found, lines, pointers


TAG = "tag:RotationChannel.Body"
library = Library()
channel, found, lines, pointers = make(library)
amon = hunter("amon", 1)
channel.aim(amon, 315.0)
check("aimed at the turned body, on the body channel, flat",
      library.calls == [("aim", "amon", TAG, (0.0, 315.0, 0.0))] and found == ["GbxRotationBlueprintLibrary"])
channel.aim(amon, 315.05)
check("a body turned by less than the margin does not ask again", len(library.calls) == 1)
channel.aim(amon, 315.2)
check("turned further, it asks again, the class found once", len(library.calls) == 2 and len(found) == 1)
channel.aim(amon, 0.05)
check("across north, the short way is measured", library.calls[-1][3][1] == 0.05 and len(library.calls) == 3)
channel.aim(amon, 359.99)
check("and so is a tiny turn back across north", len(library.calls) == 3)
channel.give_back()
check("let go: given back to the game", library.calls[-1] == ("default", "amon", TAG) and channel.aimed_yaw is None)
channel.give_back()
check("given back once only", len(library.calls) == 4)

channel.aim(amon, 90.0)
rafa = hunter("rafa", 2)
channel.aim(rafa, 90.0)
check("another hunter: the first gets his channel back before the second is aimed",
      library.calls[-2:] == [("default", "amon", TAG), ("aim", "rafa", TAG, (0.0, 90.0, 0.0))])
pointers[-1].target = None
channel.give_back()
check("the hunter gone: nothing is called, nothing is kept",
      library.calls[-1][0] == "aim" and channel.aimed_yaw is None and channel.held is None)
check("nothing said while all goes well", lines == [])

library = Library()
channel, found, lines, pointers = make(library)
library.refuse_aim = True
channel.aim(amon, 10.0)
check("a refused aim gives the channel back at once, said once",
      library.calls[-1] == ("default", "amon", TAG) and channel.broken and len(lines) == 1
      and "left to the game" in lines[0])
channel.aim(amon, 50.0)
channel.give_back()
check("then nothing more is asked for the session", len(library.calls) == 2 and len(lines) == 1)

library = Library()
channel, found, lines, pointers = make(library)
channel.aim(amon, 10.0)
library.refuse_default = True
channel.give_back()
check("a refused give-back is said once and the channel forgotten",
      channel.broken and channel.aimed_yaw is None and len(lines) == 1)

channel, found, lines, pointers = make(None)
channel.aim(amon, 10.0)
check("the game's library missing: nothing aimed, nothing to give back, said once",
      channel.broken and channel.aimed_yaw is None and len(lines) == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
