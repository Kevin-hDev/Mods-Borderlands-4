"""Tests the weapon restriction: lifted after it began with the hand empty, the game's draw is skipped; otherwise the
game runs as it always did, and always while the holster does not run."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fake_player  # noqa: E402
import heirloom_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = heirloom_stubs.install()
bound: list = []
make = sys.modules["mods_base"].keybind
sys.modules["mods_base"].keybind = lambda *args, **kwargs: bound.append(make(*args, **kwargs)) or bound[-1]

from apex_heirloom import draw_keys, holster_settings, keys, restriction  # noqa: E402


def change(character, restricted: bool):
    """The game's restriction change, its own work done unless the hook blocks it: it sets the character's flag."""
    answer = restriction.on_restriction(character, types.SimpleNamespace(bRestricted=restricted), None, None)
    if answer is not heirloom_stubs.BLOCK and hasattr(character, "bWeaponsRestricted"):
        getattr(character, "game_sets", lambda value: setattr(character, "bWeaponsRestricted", value))(restricted)
    return answer


check("the hook is the character's restriction change, before the game runs it",
      restriction.on_restriction.path == "/Script/OakGame.OakCharacter:WeaponRestrictionChanged"
      and restriction.on_restriction.kind == "PRE")

pc, character = fake_player.player(None)
state["pc"] = pc
change(character, True)
check("the holster not running, the game gives the weapon back and nothing is said",
      change(character, False) is None and not state["misc"])
keys.start()
clock = [100.0]
restriction.clock = lambda: clock[0]
check("getting in with the hand empty, the game runs its restriction", change(character, True) is None)
check("... and the log says the hand was empty",
      state["misc"][-1] == "[Tidy Weapons] weapons restricted with no weapon in hand")
check("getting out, the game's draw is skipped", change(character, False) is heirloom_stubs.BLOCK)
check("... and the log says the weapon stays away", "weapon stays away" in state["misc"][-1])
check("... its flag left set while the game could still give the weapon back by itself",
      character.bWeaponsRestricted is True)
eyes, camera = fake_player.arms(character), pc.PlayerCameraManager
# Getting out, the camera flies back from 370 to 600 cm behind the eyes for 1.25 s, and the game gives the weapon back
# as it arrives (sondes/apex_exit_camera_watch.py, 2026-09-26).
camera.place = fake_player.spot(-500.0)
clock[0] = 101.3
restriction.tick(eyes)
check("the camera still flying back, the flag stays", character.bWeaponsRestricted is True)
clock[0] = 102.0
restriction.tick(eyes)
check("... however long its way (another vehicle): no timer clears it in first person",
      character.bWeaponsRestricted is True)
# Riding, the controller has no OakCharacter (Apex Movement's "character=none" at each ride, 2026-09-26).
pc.Pawn, pc.OakCharacter = types.SimpleNamespace(Name="Vehicle"), None
camera.place = fake_player.spot()
restriction.tick(eyes)
check("the player still getting out: it waits", character.bWeaponsRestricted is True)
pc.Pawn, pc.OakCharacter = character, character
clock[0] = 102.1
restriction.tick(eyes)
check("the camera back at the eyes: not at once, the game gives the weapon back just then",
      character.bWeaponsRestricted is True)
camera.place = fake_player.spot(-300.0)
clock[0] = 102.2
restriction.tick(eyes)
camera.place = fake_player.spot(0.0, 0.0, 12.0)
clock[0] = 102.25
restriction.tick(eyes)
clock[0] = 102.35
restriction.tick(eyes)
check("the eyes are counted from the camera's last return, 12 cm off them counting as in them",
      character.bWeaponsRestricted is True)
clock[0] = 102.41
restriction.tick(types.SimpleNamespace(OakCharacter=types.SimpleNamespace(Name="OakCharacter_7"), Outer=None))
check("another player's arms are not looked at", character.bWeaponsRestricted is True)
restriction.tick(eyes)
check("the camera in the eyes EYES_FOR_S: cleared, the weapons usable again, and said",
      character.bWeaponsRestricted is False
      and state["misc"][-1] == "[Tidy Weapons] weapons usable again, the camera in the eyes")
check("... a short wait past the camera's arrival, below a player's reaction", 0.1 <= restriction.EYES_FOR_S <= 0.2)
character.bWeaponsRestricted = True
clock[0] = 110.0
restriction.tick(eyes)
check("cleared once, never again", character.bWeaponsRestricted is True)
character.bWeaponsRestricted = False

change(character, True)
change(character, False)
camera.mode = "ThirdPerson"
clock[0] = 111.3
restriction.tick(eyes)
check("in third person, the camera never at the eyes: the flag stays past the game's own return",
      character.bWeaponsRestricted is True)
clock[0] = 110.0 + restriction.THIRD_PERSON_AFTER_S
restriction.tick(eyes)
check("... and is cleared THIRD_PERSON_AFTER_S after the lift, and said",
      character.bWeaponsRestricted is False
      and state["misc"][-1] == "[Tidy Weapons] weapons usable again, in third person")
check("... soon after the game's own return, 1.21 s at most in first person",
      1.21 < restriction.THIRD_PERSON_AFTER_S <= 1.5)
camera.mode = "Default"

clock[0] = 120.0
change(character, True)
change(character, False)
camera.place = fake_player.spot(-500.0)
clock[0] = 120.0 + restriction.AT_MOST_S - 0.1
restriction.tick(eyes)
check("a camera that never comes back keeps the flag a while", character.bWeaponsRestricted is True)
clock[0] = 120.0 + restriction.AT_MOST_S
restriction.tick(eyes)
check("... but never more than AT_MOST_S: the weapons are never left out of reach",
      character.bWeaponsRestricted is False
      and state["misc"][-1] == "[Tidy Weapons] weapons usable again, the camera still away")
camera.place = fake_player.spot()
restriction.tick(eyes)

# A press asking for a weapon while the camera flew back was lost (Kevin, 2026-09-26: "l'appui est perdu").
clock[0] = 125.0
change(character, True)
change(character, False)
camera.place = fake_player.spot(-500.0)
check("before the first frame on foot, no weapon key is listened to", not draw_keys.listening())
restriction.tick(eyes)
check("on foot after a skipped lift, the player's weapon keys are listened to",
      sorted(bind.key for bind in bound if bind.is_enabled and ":draw:" in bind.identifier)
      == ["Gamepad_FaceButton_Top", "One"])
press = next(bind for bind in bound if bind.is_enabled and bind.key == "One").callback
check("a weapon key pressed while the camera flies back is left to the game",
      press(types.SimpleNamespace(name="IE_Pressed")) is None)
check("... the weapons usable at once, before the game reads it, and said",
      character.bWeaponsRestricted is False
      and state["misc"][-1] == "[Tidy Weapons] weapons usable again, the player asking for a weapon")
check("... its keys let go at the next frame, not from inside the press", draw_keys.listening())
restriction.tick(eyes)
check("... and at the next frame they are", not draw_keys.listening())
character.bWeaponsRestricted = True
errors = len(state["errors"])
press(types.SimpleNamespace(name="IE_Pressed"))
check("a late press, the weapons already back, changes nothing and is no error",
      character.bWeaponsRestricted is True and len(state["errors"]) == errors)
character.bWeaponsRestricted = False

camera.place = fake_player.spot()
change(character, True)
change(character, False)
restriction.tick(eyes)
clock[0] += restriction.EYES_FOR_S
restriction.tick(eyes)
restriction.tick(eyes)
check("given back by the camera, the keys are let go too", character.bWeaponsRestricted is False
      and not draw_keys.listening())

listened: list[int] = []
listen = draw_keys.listen


def refused(_asked) -> None:
    listened.append(1)
    raise RuntimeError("refused")


draw_keys.listen = refused
change(character, True)
change(character, False)
restriction.tick(eyes)
restriction.tick(eyes)
check("weapon keys the SDK refuses: tried once, written once", listened == [1]
      and "weapon keys not listened" in state["errors"][-1])
clock[0] += restriction.EYES_FOR_S
restriction.tick(eyes)
check("... and the camera still gives the weapons back", character.bWeaponsRestricted is False)
draw_keys.listen = listen
state["errors"].clear()

change(character, True)
change(character, False)
change(character, True)
clock[0] = 130.0
restriction.tick(eyes)
check("a new trip begun before the flag was cleared: the flag is the new trip's", character.bWeaponsRestricted is True)
change(character, False)
restriction.tick(eyes)
restriction.forget()
check("the holster stopping clears a flag left set at once, and says so",
      character.bWeaponsRestricted is False
      and state["misc"][-1] == "[Tidy Weapons] weapons usable again, the holster stopping")
check("... and lets the weapon keys go at once", not draw_keys.listening())
change(character, True)
change(character, False)
other = types.SimpleNamespace(Name="OakCharacter_9", bWeaponsRestricted=False)
pc.OakCharacter = other
clock[0] = 140.0
restriction.tick(eyes)
pc.OakCharacter = character
restriction.tick(eyes)
check("another character by then (a death, a new map): the old one's flag is left alone",
      character.bWeaponsRestricted is True and other.bWeaponsRestricted is False)
character.bWeaponsRestricted = False
check("a second lift is the game's own again", change(character, False) is None)

pc, character = fake_player.player(fake_player.weapon())
state["pc"] = pc
change(character, True)
check("getting in with a weapon, the log says so",
      state["misc"][-1] == "[Tidy Weapons] weapons restricted with a weapon in hand")
check("getting out with a weapon at the start, the game gives it back", change(character, False) is None)

pc, character = fake_player.player(None)
state["pc"] = pc
other = types.SimpleNamespace(Name="OakCharacter_2", ActiveWeapons=character.ActiveWeapons)
check("another player's restriction is left to the game", change(other, True) is None)
check("... and its lift too", change(other, False) is None)

change(character, True)
state["pc"] = types.SimpleNamespace(Pawn=types.SimpleNamespace(Name="Vehicle"), OakCharacter=None)
check("the lift is recognised by the character's name even while the controller has no character yet",
      change(character, False) is heirloom_stubs.BLOCK)

state["pc"] = pc
change(character, True)
restriction.forget()
check("forgotten (mod switched off), the game gives the weapon back", change(character, False) is None)

now = [50.0]
keys.clock = lambda: now[0]
holster_settings.keyboard_hold.value = False
pc, character = fake_player.player(fake_player.weapon())
state["pc"] = pc
keys.keyboard_bind.callback(fake_player.event("IE_Pressed"))
now[0] += 0.3
change(character, True)
check("getting in while a key's put-away still lowers the weapon counts as empty-handed",
      character.calls and state["misc"][-1] == "[Tidy Weapons] weapons restricted with the weapon being put away"
      and change(character, False) is heirloom_stubs.BLOCK)

now[0] += 1.0
pc, character = fake_player.player(fake_player.weapon())
state["pc"] = pc
change(character, True)
character.ActiveWeapons.Slots[0].Weapon = None
change(character, True)
check("a second change within one restriction, never seen in game, is written so the log shows it",
      state["misc"][-1] == "[Tidy Weapons] weapons restricted again with no weapon in hand")
check("... and decides from the hand, as every change does", change(character, False) is heirloom_stubs.BLOCK)

change(character, True)
character.ActiveWeapons.Slots[0].Weapon = fake_player.weapon()
change(character, True)
check("a restriction whose lift went unseen does not keep a later one empty-handed when a weapon is in hand",
      change(character, False) is None)
change(character, True)
character.ActiveWeapons.Slots[0].Weapon = None
change(character, True)
check("nor with a weapon when the hand is empty: the weapon stays away",
      change(character, False) is heirloom_stubs.BLOCK)

class Stuck:
    """A character whose restriction flag cannot be written."""
    Name = "OakCharacter_1"

    def __init__(self):
        self.ActiveWeapons = types.SimpleNamespace(Slots=[types.SimpleNamespace(Weapon=None)])
        self.flag = False

    def game_sets(self, value):
        self.flag = value

    @property
    def bWeaponsRestricted(self):
        return self.flag

    @bWeaponsRestricted.setter
    def bWeaponsRestricted(self, _value):
        raise AttributeError("read only")


stuck = Stuck()
state["pc"] = types.SimpleNamespace(Pawn=stuck, OakCharacter=stuck)
change(stuck, True)
check("a flag that cannot be written leaves the lift to the game, which gives the weapon back usable",
      change(stuck, False) is None and stuck.flag is False and "left to the game" in state["errors"][-1])
state["errors"].clear()
restriction.report.reset()

broken = types.SimpleNamespace(Name="OakCharacter_1")
state["pc"] = types.SimpleNamespace(Pawn=broken, OakCharacter=broken)
check("an error leaves the change to the game", change(broken, True) is None)
check("... and is written once", len(state["errors"]) == 1 and "left to the game" in state["errors"][0])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
