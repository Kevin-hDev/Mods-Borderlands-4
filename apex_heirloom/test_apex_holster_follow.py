"""Tests the weapon and climbing watch: the heirloom shown now if no weapon is in hand, hidden if one is; the weapon
put away shows it and draws it; the weapon back puts it away, the heirloom staying shown until the hands are down,
or goes at once when the put-away cannot play; a switch between two weapons neither draws nor puts away; a new change
or a climb cuts the put-away short; hidden while the player climbs, and not shown again by the end of a climb while a
weapon is in hand; hidden as a climb is while the camera is in third person or looks from a vehicle; another
character's changes are ignored; the watch stops when the heirloom is gone or when asked, showing a weapon hidden by a
put-away again. With our own animations: shown only while the arms play them, read as the hands empty or a few frames
later (drawn then), kept while the hands go down; its leaving the hands is told, not its hiding by a climb. The game's
depth of field is off while the heirloom is shown, and the player's value back when it is hidden or the watch
stops. The heirloom's inspection stops at once with its draw whenever it leaves the empty hand: a weapon back, a switch
between two weapons, a climb; a key may inspect it only while it shows in the empty hand."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402
from heirloom_stubs import sdk_stubs  # noqa: E402

fails: list[str] = []
said: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = heirloom_stubs.install()
# The engine's console, as the depth of field reads and sets it (apex_depth_of_field.py); the player's value is 2.
commands: list[str] = []
state["pc"] = types.SimpleNamespace(OakCharacter=None)
state["classes"]["KismetSystemLibrary"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
    GetConsoleVariableIntValue=lambda _name: 2,
    ExecuteConsoleCommand=lambda _world, command, _pc: commands.append(command)))
depth_said: list[str] = []


def say(text: str) -> None:
    (depth_said if text.startswith("depth of field") else said).append(text)

hooks: dict[tuple, object] = {}
hooks_module = sys.modules["unrealsdk.hooks"]
hooks_module.add_hook = lambda path, kind, identifier, callback: hooks.setdefault((path, kind, identifier), callback)
hooks_module.has_hook = lambda path, kind, identifier: (path, kind, identifier) in hooks
hooks_module.remove_hook = lambda path, kind, identifier: hooks.pop((path, kind, identifier), None) is not None

from apex_heirloom import apex_holster_follow as follow  # noqa: E402


class Knife:
    def __init__(self) -> None:
        self.visible: list[bool] = []

    def SetVisibility(self, shown: bool, children: bool) -> None:
        assert children, "what hangs on the heirloom follows it"
        self.visible.append(shown)


class Draw:
    def __init__(self) -> None:
        self.events: list[str] = []

    def play(self, _arms: object) -> None:
        self.events.append("play")

    def cancel(self, _arms: object) -> None:
        self.events.append("cancel")


class PutAway:
    def __init__(self) -> None:
        self.events: list[tuple] = []
        self.lasting: float | None = 0.4

    def start(self, _arms: object, weapon: object) -> float | None:
        self.events.append(("start", weapon))
        return self.lasting

    def finish(self) -> None:
        self.events.append(("finish",))

    def cancel(self, _arms: object) -> None:
        self.events.append(("cancel",))


def player(weapon) -> types.SimpleNamespace:
    return types.SimpleNamespace(ActiveWeapons=types.SimpleNamespace(Slots=[types.SimpleNamespace(Weapon=weapon)]),
                                 CharacterMovement=types.SimpleNamespace(
                                     LadderState=types.SimpleNamespace(CurrentClimbable=None),
                                     ReplicatedMantleState=types.SimpleNamespace(ActionIndex=-1)))


now = [0.0]
knife, draw, put_away = Knife(), Draw(), PutAway()
held = [knife]
owner = player(None)
follow.follow(lambda: held[0], owner, say, draw, put_away, lambda: now[0])
key = (follow.WEAPON_HOOK, "POST", follow.IDENTIFIER)
frame_key = (follow.FRAME_HOOK, "POST", follow.IDENTIFIER)
check("no weapon in hand: the heirloom is shown at once, with what hangs on it, and not drawn",
      knife.visible == [True] and said == ["no weapon in hand: heirloom shown"] and not draw.events)
check("the first-person animation's weapon change and frames are watched", key in hooks and frame_key in hooks)
check("under its package's name: Heirloom's watch never takes the hooks of Apex Heirloom's, leaving in the same session",
      follow.IDENTIFIER == "apex_heirloom.apex_holster_follow")
changed, frame = hooks[key], hooks[frame_key]
arms = types.SimpleNamespace(OakCharacter=owner, GetCurrentActiveMontage=lambda: None)


def weapon_change(weapon: object | None, at: float, obj: object | None = None) -> None:
    """A weapon change of the character watched now, unless another's arms are given."""
    now[0] = at
    changed(arms if obj is None else obj, types.SimpleNamespace(NewWeapon=weapon), None, None)


def frame_at(at: float) -> None:
    now[0] = at
    frame(arms, None, None, None)


rifle, pistol = object(), object()
weapon_change(rifle, 1.0)
check("the weapon back a second later: the draw stops, the put-away starts with that weapon, the heirloom stays shown",
      draw.events == ["cancel"] and put_away.events == [("start", rifle)] and knife.visible[-1] is True
      and said[-1] == "weapon back, the hands go down: heirloom shown")
frame_at(1.3)
check("while the hands go down, the frames change nothing", len(knife.visible) == 2 and len(put_away.events) == 1)
frame_at(1.4)
check("the hands down, the weapon shows again and the heirloom is hidden",
      put_away.events[-1] == ("finish",) and knife.visible[-1] is False and said[-1] == "hands down: heirloom hidden")
check("the game's depth of field was off while the heirloom showed, and is the player's again once it is hidden",
      commands == ["r.DepthOfFieldQuality 0", "r.DepthOfFieldQuality 2"])
frame_at(2.0)
check("once down, nothing more happens", len(put_away.events) == 2 and len(knife.visible) == 3)

weapon_change(None, 3.0)
check("the weapon put away shows the heirloom and draws it", knife.visible[-1] is True and draw.events[-1] == "play")
weapon_change(None, 3.5)
check("a change that leaves it shown does not draw it again", draw.events.count("play") == 1)
weapon_change(rifle, 5.0)
weapon_change(None, 5.1)
check("the weapon put away again while the hands go down: the put-away is cut short, the heirloom stays shown, "
      "undrawn", put_away.events[-1] == ("cancel",) and knife.visible[-1] is True and draw.events.count("play") == 1)
weapon_change(pistol, 5.12)
check("then another weapon: the hands go down with the heirloom for it",
      put_away.events[-1] == ("start", pistol) and knife.visible[-1] is True)
frame_at(5.6)
weapon_change(None, 7.0)
events = len(put_away.events)
weapon_change(rifle, 7.02)
check("a switch between two weapons, \"no weapon\" for 20 ms: no put-away, the heirloom goes at once, its draw stops",
      len(put_away.events) == events and knife.visible[-1] is False and draw.events[-2:] == ["play", "cancel"])

weapon_change(None, 9.0)
put_away.lasting = None
weapon_change(rifle, 10.0)
check("a put-away that cannot play: the heirloom goes at once", knife.visible[-1] is False
      and said[-1] == "weapon in hand: heirloom hidden")
put_away.lasting = 0.4

weapon_change(None, 11.0)
weapon_change(rifle, 12.0)
owner.CharacterMovement.LadderState.CurrentClimbable = object()
frame_at(12.1)
check("a climb while the hands go down cuts the put-away short and hides the heirloom",
      put_away.events[-1] == ("cancel",) and knife.visible[-1] is False
      and said[-1] == "climbing (ladder): heirloom hidden")
visible = len(knife.visible)
frame_at(12.2)
check("each frame of the same climb changes nothing", len(knife.visible) == visible)
owner.CharacterMovement.LadderState.CurrentClimbable = None
frame_at(12.3)
check("a climb that ends with a weapon in hand leaves the heirloom hidden", knife.visible[-1] is False)
owner.CharacterMovement.LadderState.CurrentClimbable = object()
frame_at(13.0)
weapon_change(None, 13.5)
plays = draw.events.count("play")
check("the weapon put away on a ladder draws nothing, the heirloom staying hidden",
      knife.visible[-1] is False and draw.events.count("play") == plays)
owner.CharacterMovement.LadderState.CurrentClimbable = None
frame_at(14.0)
check("the climb's end shows the heirloom without a draw", knife.visible[-1] is True
      and draw.events.count("play") == plays)

visible = len(knife.visible)
weapon_change(rifle, 15.0, types.SimpleNamespace(OakCharacter=player(None)))
check("another character's weapon change is ignored", len(knife.visible) == visible)

weapon_change(rifle, 16.0)
held[0] = None
frame_at(16.1)
check("the heirloom gone while the hands go down: the watch stops and the weapon shows again",
      key not in hooks and frame_key not in hooks and put_away.events[-1] == ("finish",))

def spot(x: float) -> types.SimpleNamespace:
    return types.SimpleNamespace(X=x, Y=0.0, Z=0.0)


class Camera:
    """The player's camera manager: its mode for the character, the actor it looks from, and where it is; the arms'
    eye is at the origin."""

    def __init__(self, looked_at: object) -> None:
        self.mode, self.ViewTarget, self.place = "Default", types.SimpleNamespace(Target=looked_at), spot(0.0)

    def GetActorCameraMode(self, _actor: object) -> str:
        return self.mode

    def GetCameraLocation(self) -> types.SimpleNamespace:
        return self.place


owner = player(None)
camera = Camera(owner)
follow.follow(lambda: knife, owner, say, draw, put_away, lambda: now[0], camera=lambda: camera)
changed, frame = hooks[key], hooks[frame_key]
arms = types.SimpleNamespace(OakCharacter=owner, GetCurrentActiveMontage=lambda: None,
                             Outer=types.SimpleNamespace(GetSocketLocation=lambda _bone: spot(0.0)))
events, plays = len(put_away.events), draw.events.count("play")
frame_at(20.0)
camera.mode = "ThirdPerson"
frame_at(20.1)
check("third person hides the heirloom at once, without a put-away",
      knife.visible[-1] is False and said[-1] == "camera in ThirdPerson: heirloom hidden"
      and len(put_away.events) == events)
camera.mode = "Default"
frame_at(20.2)
check("back in first person, the heirloom shows again without a draw",
      knife.visible[-1] is True and said[-1] == "camera in ThirdPerson over: heirloom shown"
      and draw.events.count("play") == plays)
camera.ViewTarget.Target = types.SimpleNamespace(Name="OakVehicle_2")
frame_at(20.3)
check("a camera looking from a vehicle hides it", knife.visible[-1] is False
      and said[-1] == "camera from OakVehicle_2: heirloom hidden")
weapon_change(rifle, 20.4)
weapon_change(None, 21.0)
check("a weapon taken and put away while the camera is out: no put-away, no draw, the heirloom stays hidden",
      len(put_away.events) == events and draw.events.count("play") == plays and knife.visible[-1] is False)
camera.ViewTarget.Target = owner
frame_at(21.1)
check("the camera back on the character shows it again", knife.visible[-1] is True)
# Getting out of a vehicle, the camera flies back from 370 to 600 cm behind the eyes for 1.25 s, and Kevin saw the
# knife float back into the hand (sondes/apex_exit_camera_watch.py, 2026-09-26).
camera.place = spot(-450.0)
frame_at(21.2)
check("the camera flying back to the eyes hides it, without a put-away",
      knife.visible[-1] is False and said[-1] == "camera on its way back to the eyes: heirloom hidden"
      and len(put_away.events) == events)
camera.place = spot(0.0)
frame_at(21.3)
check("... and at the eyes it shows again, without a draw",
      knife.visible[-1] is True and said[-1] == "camera on its way back to the eyes over: heirloom shown"
      and draw.events.count("play") == plays)

follow.follow(lambda: knife, player(object()), say)
check("a weapon in hand when the watch starts: hidden at once", knife.visible[-1] is False and key in hooks)
follow.stop()
check("stop removes the watch", key not in hooks and frame_key not in hooks and not follow.holding())

# The arms play our animations only once the game has read our list, at a weapon change (essai 6).
ours = [False]
went: list[float] = []
owner = player(None)
draw, put_away = Draw(), PutAway()
follow.follow(lambda: knife, owner, say, draw, put_away, lambda: now[0], played=lambda: ours[0],
              gone=lambda: went.append(now[0]))
changed, frame = hooks[key], hooks[frame_key]
arms = types.SimpleNamespace(OakCharacter=owner, GetCurrentActiveMontage=lambda: None)
check("empty hands playing the game's animations: the heirloom hidden from the start",
      knife.visible[-1] is False and not follow.holding())
frame_at(30.0)
check("frames that change nothing leave it hidden", knife.visible[-1] is False and not draw.events)
weapon_change(rifle, 31.0)
ours[0] = True
weapon_change(None, 32.0)
check("our animations read by the time the weapon goes: shown and drawn", knife.visible[-1] is True
      and draw.events == ["play"] and follow.holding())
weapon_change(rifle, 33.0)
ours[0] = False
frame_at(33.2)
check("the weapon back: the hands go down with it though the arms now play the weapon's",
      put_away.events[-1] == ("start", rifle) and knife.visible[-1] is True)
frame_at(33.5)
check("hands down: hidden, and its leaving the hands told", knife.visible[-1] is False and went == [33.5])
weapon_change(None, 34.0)
check("put away while the game's animations are still read: hidden, no draw", knife.visible[-1] is False
      and draw.events.count("play") == 1)
ours[0] = True
frame_at(34.1)
check("our animations read a few frames later: shown then, and drawn", knife.visible[-1] is True
      and draw.events.count("play") == 2 and draw.events[-1] == "play" and said[-1] == "our animations: heirloom shown")
ours[0] = False
frame_at(34.2)
check("the game's animations back while the hands are empty: hidden, the draw stopped, the leaving told",
      knife.visible[-1] is False and draw.events[-1] == "cancel" and went[-1] == 34.2
      and said[-1] == "the game's animations: heirloom hidden")
ours[0] = True
frame_at(40.0)
check("our animations read long after the weapon went: shown without a draw", knife.visible[-1] is True
      and draw.events.count("play") == 2)
owner.CharacterMovement.LadderState.CurrentClimbable = object()
frame_at(40.1)
check("hidden by a climb, the hands still hold it: its leaving is not told", knife.visible[-1] is False
      and went == [33.5, 34.2] and follow.holding())
weapon_change(rifle, 40.2)
check("the weapon back while the climb hides it: the hands no longer hold it, and its leaving is told though unseen",
      went == [33.5, 34.2, 40.2] and not follow.holding())
weapon_change(pistol, 40.3)
check("a second weapon change tells nothing more", went == [33.5, 34.2, 40.2])
follow.stop()

follow.follow(lambda: knife, player(None), say)
shown_commands = list(commands)
follow.stop()
check("the watch stopped while the heirloom shows: the player's depth of field back",
      shown_commands[-1:] == ["r.DepthOfFieldQuality 0"] and commands[-1:] == ["r.DepthOfFieldQuality 2"])

# A knife destroyed with its character (a new one after a death or a map): any arms' frame stops the watch.
gone_knife = [knife]
follow.follow(lambda: gone_knife[0], player(None), say)
gone_knife[0] = None
hooks[frame_key](types.SimpleNamespace(OakCharacter=player(None)), None, None, None)
check("the knife gone, the next frame of any arms stops the watch", key not in hooks and frame_key not in hooks)


class Gesture:
    """The heirloom's inspection as the watch sees it: stopped, and how often."""

    def __init__(self) -> None:
        self.cancelled = 0

    def cancel(self, _arms: object) -> None:
        self.cancelled += 1


inspection, owner, draw, put_away = Gesture(), player(None), Draw(), PutAway()
now[0] = 49.0
follow.follow(lambda: knife, owner, say, draw, put_away, lambda: now[0], inspect=inspection)
changed, frame = hooks[key], hooks[frame_key]
arms = types.SimpleNamespace(OakCharacter=owner, GetCurrentActiveMontage=lambda: None)
check("the heirloom shown in the empty hand: a key may inspect it",
      follow.in_empty_hand() and inspection.cancelled == 0)
weapon_change(rifle, 50.0)
check("the weapon back: the inspection stops at once with the draw; while the hands go down with the heirloom, a key "
      "plays nothing", inspection.cancelled == 1 and draw.events[-1:] == ["cancel"] and knife.visible[-1] is True
      and not follow.in_empty_hand())
frame_at(50.5)
check("the hands down: hidden, a key plays nothing", knife.visible[-1] is False and not follow.in_empty_hand())
weapon_change(None, 51.0)
check("put away again: a key may inspect it", follow.in_empty_hand())
stopped = inspection.cancelled
weapon_change(pistol, 51.05)
check("a switch between two weapons: the heirloom goes at once, its inspection stopped",
      inspection.cancelled == stopped + 1 and not follow.in_empty_hand())
weapon_change(None, 52.0)
stopped = inspection.cancelled
owner.CharacterMovement.LadderState.CurrentClimbable = object()
frame_at(52.1)
check("a climb hides it: its inspection stops, a key plays nothing",
      inspection.cancelled == stopped + 1 and not follow.in_empty_hand())
owner.CharacterMovement.LadderState.CurrentClimbable = None
frame_at(52.2)
check("the climb over: a key may inspect it again", follow.in_empty_hand())
follow.stop()
check("the watch stopped: a key plays nothing", not follow.in_empty_hand())

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
