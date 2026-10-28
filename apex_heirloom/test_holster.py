"""Tests the put-away: the game asked once for the weapon in hand, on foot only, never twice while it goes down."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fake_player  # noqa: E402
import heirloom_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


heirloom_stubs.install()

from apex_heirloom import holster  # noqa: E402

now = [10.0]
put = holster.Holster(lambda: now[0])

pc, character = fake_player.player(fake_player.weapon("OakWeapon_1"))
check("a weapon in hand is put away", put.put_away(pc) == holster.PUT_AWAY)
check("the game is asked to equip nothing, slot -1", character.calls == [(None, 0, 0, 0, -1)])

now[0] = 10.5
check("asked again while it goes down, the game is not asked twice", put.put_away(pc) == holster.GOING_DOWN)
check("... and only one call was made", len(character.calls) == 1)
check("the weapon is known to be going down", put.going_down(character.ActiveWeapons.Slots[0].Weapon))

now[0] = 10.61
check("the same weapon in hand once it is down (drawn back at once), the game is asked again",
      put.put_away(pc) == holster.PUT_AWAY and len(character.calls) == 2)

pc2, character2 = fake_player.player(fake_player.weapon("OakWeapon_2"))
now[0] = 11.2
check("another weapon drawn meanwhile is put away at once", put.put_away(pc2) == holster.PUT_AWAY)
check("... by its own call", character2.calls == [(None, 0, 0, 0, -1)])

pc, character = fake_player.player(None)
check("no weapon in hand, nothing is asked", put.put_away(pc) == holster.NO_WEAPON and character.calls == [])

pc, character = fake_player.player(fake_player.weapon(), on_foot=False)
check("in a vehicle, nothing is asked", put.put_away(pc) == holster.NOT_ON_FOOT and character.calls == [])
check("no controller (loading), nothing is asked", put.put_away(None) == holster.NOT_ON_FOOT)
pc.OakCharacter = None
check("no character, nothing is asked", put.put_away(pc) == holster.NOT_ON_FOOT)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
