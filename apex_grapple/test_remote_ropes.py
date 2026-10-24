"""Tests remote_ropes.py, remote_look.py and remote_beam.py: another player's grapple drawn on that player's character
as that player chose it: the grapple gun's body pieces only, the holster as chosen, the rope going, biting after its
flight, the body's gestures, the hook coming back and the pistol back in its holster; the game's rope in that player's
colour with the classic look; nothing for a rope hidden; a rope told before the character is found; a look changed
built again between shots; a new character; a failure costing that player alone; everything removed at switch-off."""

import types

from grapple_fixture import SECOND, check, fails, fresh, sdk_stubs, settings, state
from apex_grapple import look_assets, look_code, look_gun, look_settings, remote_look, remote_ropes
import look_fixture
import vex_fixture

import sys

MS = 1_000_000
ANCHOR = (2000.0, 0.0, 170.0)


def look_with(shown: bool = True, **chosen: str) -> int:
    # The fixture plays the player's own rope in the classic look; the other player chose the grapple gun.
    chosen.setdefault("look", look_settings.GRAPPLE_GUN)
    values = tuple(chosen.get(option.identifier, option.value) for option in look_settings.ALL)
    return look_code.encode(shown, values)


def remote(definition: str = "Char_DarkSiren") -> tuple:
    character = look_fixture.dress(sdk_stubs.FakeCharacter(), record)
    _arms, body = vex_fixture.dress(state, character, definition=definition)
    character.IsLocallyControlled = lambda: False
    character.Mesh.GetSocketLocation = lambda bone: types.SimpleNamespace(X=10.0, Y=20.0, Z=150.0)
    return character, body


def meshes(pieces) -> list[str]:
    return [look_fixture.mesh_of(made).rsplit(".", 1)[-1] for made in pieces if made.called("SetStaticMesh")]


player, rope = fresh(on_ground=False)
local_pc = state["pc"]
record = look_fixture.install(state)
vex_fixture.install(state)
other, body = remote()
state["players"][:] = [types.SimpleNamespace(PlayerId=7, PawnPrivate=other)]

# 1. The grapple gun, as that player chose it.
remote_ropes.look(7, look_with(holster=look_settings.WITH))
remote_ropes.tick(0)
grapple = remote_ropes._remotes[7].grapple
check("a hunter we know with the grapple gun: its look is built", isinstance(grapple, remote_look.GunGrapple))
check("the body's pieces only, never the arms' pistol", set(grapple.gun.pieces) == set(remote_look.ROLES))
check("the holster shows, with the pistol in it", grapple.gun.seen == {look_gun.HOLSTERED, look_gun.HOLSTER})

remote_ropes.start(7, ANCHOR, 0.4, 0)
remote_ropes.tick(10 * MS)
check("its rope goes: the pistol in the hand, the holster kept", grapple.gun.seen == {look_gun.BODY_PISTOL,
                                                                                   look_gun.HOLSTER})
check("a rope and a hook are drawn", look_fixture.shown(record["pieces"]) > 3)
check("the hook flies, not yet planted", grapple.current.shot.planted is None)
remote_ropes.tick(410 * MS)
check("after its flight the hook bites", grapple.current.shot.planted is not None)
remote_ropes.tick(500 * MS)
check("the body's gestures play, on the body only", body.played and all(
    played["SlotNodeName"] in ("UpperBody", "Offhand", "Mainhand") for played in body.played))
remote_ropes.release(7, 600 * MS)
for frame in range(1, 200):
    remote_ropes.tick(600 * MS + frame * 20 * MS)
check("let go, the hook comes back and the pistol goes back in its holster",
      grapple.gun.seen == {look_gun.HOLSTERED, look_gun.HOLSTER} and not grapple.busy())

# 2. A look changed: built again between shots, with its holster as chosen.
pieces_before = len(record["pieces"])
remote_ropes.look(7, look_with(holster=look_settings.WITHOUT))
remote_ropes.tick(5 * SECOND)
again = remote_ropes._remotes[7].grapple
check("a look changed is built again", again is not grapple and len(record["pieces"]) > pieces_before)
check("the old pieces are removed", all(made.called("K2_DestroyComponent") for made in record["pieces"][:pieces_before]))
check("without the holster, nothing shows between shots", again.gun.seen == set())

remote_ropes.start(7, ANCHOR, 0.4, 6 * SECOND)
remote_ropes.look(7, look_with(holster=look_settings.WITH))
remote_ropes.tick(6 * SECOND + 10 * MS)
check("a look changed during a shot waits for its end", remote_ropes._remotes[7].grapple is again)
remote_ropes.release(7, 6 * SECOND + 20 * MS)

# 3. The classic look: the game's rope in that player's colour.
remote_ropes.look(7, look_with(look=look_settings.CLASSIC, game_rope_colour="RED"))
for frame in range(0, 200):
    remote_ropes.tick(7 * SECOND + frame * 20 * MS)
beam = remote_ropes._remotes[7].grapple
check("with the classic look, the game's rope", type(beam).__name__ == "BeamGrapple")
remote_ropes.start(7, ANCHOR, 0.4, 12 * SECOND)
spawned = state["niagara"].spawned[-1]
check("it leaves from the left hand", (spawned["Location"].X, spawned["Location"].Z) == (10.0, 150.0))
check("in that player's colour", spawned["component"].colours.get("User.Color") == (*look_assets.COLOURS["RED"], 1.0))
check("lit", spawned["component"].activations == 1)
remote_ropes.tick(12 * SECOND + 10 * MS)
remote_ropes.release(7, 12 * SECOND + 20 * MS)
check("let go, it is put out", spawned["component"].alive is False and not beam.busy())

# 4. A rope hidden by its player: nothing drawn.
remote_ropes.look(7, look_with(shown=False))
remote_ropes.tick(13 * SECOND)
remote_ropes.start(7, ANCHOR, 0.4, 13 * SECOND)
check("a player who hides the rope has nothing drawn", remote_ropes._remotes[7].grapple is None)

# 5. A rope told before the character is found starts once it is.
remote_ropes.reset()
state["players"][:] = []
remote_ropes.look(8, look_with())
remote_ropes.start(8, ANCHOR, 0.4, 20 * SECOND)
remote_ropes.tick(20 * SECOND)
check("no character yet: kept", remote_ropes._remotes[8].waiting is not None)
late, _late_body = remote()
state["players"][:] = [types.SimpleNamespace(PlayerId=8, PawnPrivate=late)]
remote_ropes.tick(20 * SECOND + 10 * MS)
check("found: its rope starts", remote_ropes._remotes[8].grapple.busy())

# 6. A new character: the old one's pieces dropped, new ones built.
old = remote_ropes._remotes[8].grapple
new, _new_body = remote()
state["players"][:] = [types.SimpleNamespace(PlayerId=8, PawnPrivate=new)]
remote_ropes.tick(21 * SECOND)
check("a new character gets new pieces", remote_ropes._remotes[8].grapple is not old
      and remote_ropes._remotes[8].grapple.character() is new)

# A player out of its character for a while (a vehicle, between two lives) keeps its look; one who left the game
# is forgotten.
state["players"][:] = [types.SimpleNamespace(PlayerId=8, PawnPrivate=None)]
remote_ropes.tick(21 * SECOND + 10 * MS)
check("a player out of its character keeps its look, its pieces dropped",
      remote_ropes._remotes[8].look_number == look_with() and remote_ropes._remotes[8].grapple is None)
state["players"][:] = [types.SimpleNamespace(PlayerId=8, PawnPrivate=new)]
remote_ropes.tick(21 * SECOND + 20 * MS)
check("back on foot, drawn again without waiting for its look", remote_ropes._remotes[8].grapple is not None)

# 7. A hunter we do not know keeps the game's rope.
stranger, _stranger_body = remote("Char_Unknown")
state["players"][:] = [types.SimpleNamespace(PlayerId=8, PawnPrivate=new),
                       types.SimpleNamespace(PlayerId=9, PawnPrivate=stranger)]
remote_ropes.look(9, look_with())
remote_ropes.tick(22 * SECOND)
check("a hunter we do not know: the game's rope", type(remote_ropes._remotes[9].grapple).__name__ == "BeamGrapple")

# 8. A failure costs that player alone.
state["players"][:] = [types.SimpleNamespace(PlayerId=8, PawnPrivate=new),
                       types.SimpleNamespace(PlayerId=9, PawnPrivate=stranger)]
remote_ropes.tick(23 * SECOND)
remote_ropes._remotes[8].grapple.tick = lambda now_ns: (_ for _ in ()).throw(RuntimeError("broken piece"))
remote_ropes.tick(23 * SECOND + 10 * MS)
check("a failure stops that player's drawing, said once", remote_ropes._remotes[8].grapple is None
      and remote_ropes._remotes[8].broken
      and any("another player's grapple stopped being drawn" in line for line in state["errors"]))
check("the others go on", remote_ropes._remotes[9].grapple is not None)
check("the player's own rope still answers", rope.fire(player, 24 * SECOND) and rope.busy)

# 8b. Kevin's decision 2 of 2026-10-24: each look a player told built that player's grapple again, 24 to 55 ms on
# every other game and as often as told, so a modified game telling one at every frame froze every other game. A look
# changed is built at most once a second for each player; a new character or a return on foot is not held back.
built: list[int] = []
real_make = remote_ropes.make
remote_ropes.make = lambda character, number: (built.append(number), real_make(character, number))[1]
told = [look_with(look=look_settings.CLASSIC, hook_size=size) for size in ("A", "B") * 15]
for step, number in enumerate(told):
    remote_ropes.look(9, number)
    remote_ropes.tick(25 * SECOND + step * 16 * MS)
check("thirty looks told in half a second build that player's grapple once", len(built) == 1)
remote_ropes.tick(26 * SECOND)
check("a second after that build, the last look told is built", len(built) == 2 and built[-1] == told[-1])
remote_ropes.make = real_make

# 9. Bounded, and everything removed at switch-off.
for number in range(100, 100 + remote_ropes.MAX_PLAYERS + 5):
    remote_ropes.look(number, 0)
check("the players followed are bounded", len(remote_ropes._remotes) == remote_ropes.MAX_PLAYERS)
state["players"][:] = []
remote_ropes.tick(30 * SECOND)
check("players who left the game are forgotten", remote_ropes._remotes == {})
for number in range(100, 103):
    remote_ropes.look(number, 0)
remote_ropes.reset()
check("switching off forgets every player", remote_ropes._remotes == {})

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
