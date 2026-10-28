"""The optional visual layer must respect the menu and isolate a missing hand transform: the grapple gun's look for Vex,
our gestures instead of the game's, its hook out and back after the pull; another hunter, or ours unable to play, the
classic look; the classic look as it was."""

import sys

import sdk_stubs

state = sdk_stubs.install()
from apex_grapple import (beam, game, look_assets, look_choice, look_play, look_settings, look_shots, rope_visuals,
                          settings)
import look_fixture
import vex_fixture

fails = []
SECOND = 1_000_000_000


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def names(instance):
    return [name for _slot, name in vex_fixture.slots(instance)]


record = look_fixture.install(state)
vex_fixture.install(state)
vex_fixture.remember(state)
player = look_fixture.dress(sdk_stubs.FakeCharacter(), record)
hands, body = vex_fixture.dress(state, player)
hands.Outer.DoesSocketExist = lambda name: True
hands.Outer.GetSocketLocation = lambda name: sdk_stubs.vector(0, 0, 160)
vex_fixture.camera(state, player)
game.refresh(0, at_once=True)
ANCHOR = (2000.0, 0.0, 170.0)

rope_visuals.tick(player, 0)
check("the grapple gun's pieces are built before the first shot: pistol, holster, ropes",
      look_play.ready() and look_shots.built() and len(record["pieces"]) == 4 + 140)
rope_visuals.start(player, ANCHOR, 1 * SECOND, 0.4)
rope_visuals.tick(player, 1 * SECOND)
check("a shot of Vex plays the grapple gun's look with our gestures, not the game's arm, and no beam",
      look_play.busy() and names(hands)[0] == "AS_AG_Arms_Left" and "AS_Grapple" not in names(hands)
      and not state["niagara"].spawned and "[Apex Grapple] look: grapple gun" in state["misc"])
rope_visuals.follow(player, ANCHOR)
rope_visuals.tick(player, int(1.2 * SECOND))
place = next(one for one in look_shots._places if one.shot is not None)
check("its rope and hook show as the hook flies", look_fixture.shown(place.rope.strands[0][0]) > 0
      and place.hook.visible)
rope_visuals.hold(player, int(1.4 * SECOND), 1830.0, 600.0, 2500.0)
rope_visuals.pulled((1500.0, 0.0, 0.0), (2500.0, 0.0, 0.0))
rope_visuals.tick(player, int(1.5 * SECOND))
check("caught, Vex's body flies", "AS_RH_Grapple" in names(body))
rope_visuals.stop(2 * SECOND)
rope_visuals.tick(player, int(2.1 * SECOND))
check("the pull over, the hook comes back", look_shots.busy() and place.hook.visible)
for frame in range(130, 240):
    rope_visuals.tick(player, frame * SECOND // 60)
check("back in the muzzle and the arm out, nothing shows and nothing plays", not look_play.busy()
      and not place.hook.visible and look_fixture.shown(place.rope.strands[0][0]) == 0)

played = len(hands.played)
settings.show_rope.value = False
rope_visuals.start(player, ANCHOR, 4 * SECOND, 0.4)
rope_visuals.tick(player, 4 * SECOND)
check("rope hidden: no shot shows, and the built pieces are removed",
      not look_play.busy() and not look_play.built() and len(hands.played) == played
      and all(made.called("K2_DestroyComponent") for made in record["pieces"]))
settings.show_rope.value = True

paladin = look_fixture.dress(sdk_stubs.FakeCharacter(), record)
vex_fixture.dress(state, paladin, definition="Char_Newcomer")
state["anim_instances"] = [hands]
rope_visuals.start(paladin, ANCHOR, 5 * SECOND, 0.4)
check("a hunter we do not know: the classic look, the game's arm and beam, none of our pieces, and the page says why",
      len(state["niagara"].spawned) == 1 and not look_play.built()
      and look_choice.notice() == look_choice.UNKNOWN_HUNTER
      and "[Apex Grapple] look: classic" in state["misc"])
rope_visuals.stop(6 * SECOND)

look_settings.look.value = look_settings.CLASSIC
rope_visuals.start(player, ANCHOR, 6 * SECOND, 0.4)
check("the classic look chosen: the game's beam, none of our pieces", len(state["niagara"].spawned) == 2
      and not look_play.built())
rope_visuals.stop(6 * SECOND)
look_settings.look.value = look_settings.GRAPPLE_GUN

rope_visuals.tick(player, 7 * SECOND)
built = list(record["pieces"][-144:])
rope_visuals.start(player, ANCHOR, 8 * SECOND, 0.4)
for made in built[4:]:
    made.answers["K2_SetWorldLocationAndRotation"] = lambda *args: (_ for _ in ()).throw(RuntimeError("refused"))
rope_visuals.tick(player, int(8.2 * SECOND))
check("a piece refusing to move: ours gives way for good, every piece removed, said once with its cause",
      look_choice.notice() == look_choice.FAILED and not look_play.built()
      and all(made.called("K2_DestroyComponent") for made in built)
      and sum("RuntimeError('refused')" in line for line in state["errors"]) == 1)
rope_visuals.stop(9 * SECOND)
rope_visuals.start(player, ANCHOR, 10 * SECOND, 0.4)
check("the next shots are classic", len(state["niagara"].spawned) == 3 and not look_play.built())
rope_visuals.reset()

look_choice._stopped = None
for pair in look_fixture.every_asset():
    state["objects"].pop(pair, None)
look_fixture.install(state, missing=(look_assets.PIECES["hook"]["mesh"],))
rope_visuals.start(player, ANCHOR, 11 * SECOND, 0.4)
check("our container missing: the same shot plays the classic look, and the look page will say why",
      len(state["niagara"].spawned) == 4 and look_choice.notice() == look_choice.MISSING
      and any(look_assets.PIECES["hook"]["mesh"] in line for line in state["errors"]))
rope_visuals.reset()

settings.show_rope.value = False
look_settings.look.value = look_settings.CLASSIC
rope_visuals.start(player, (1000, 0, 0), 12 * SECOND, 0.1)
rope_visuals.follow(player, (1000, 0, 0))
check("hidden visuals spawn no beam", len(state["niagara"].spawned) == 4)
settings.show_rope.value = True
rope_visuals.start(player, (1000, 0, 0), 13 * SECOND, 0.1)
component = beam._component


def missing_hand(character):
    raise RuntimeError("hand disappeared")


game.hand_spot = missing_hand
rope_visuals.follow(player, (1000, 0, 0))
rope_visuals.follow(player, (1000, 0, 0))
check("a failed hand lookup releases the visual", component in state["destroyed"])
check("the failure is reported once", sum("RuntimeError('hand disappeared')" in line for line in state["errors"]) == 1)
rope_visuals.start(player, (1000, 0, 0), 14 * SECOND, 0.1)
check("a broken visual does not keep spawning", len(state["niagara"].spawned) == 5)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
