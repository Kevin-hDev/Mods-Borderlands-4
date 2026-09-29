"""The wardrobe: a game without a choice left alone, nothing rebuilt nor fitted, even a look the mod does not know; a
hunter worn in a game, remembered for it, the legs fitted; the same game reloaded in the session keeps the look
without a rebuild, legs fitted on the new character; after a restart the choice comes back from the file; another
game of the same hunter gets its own look back; the own hunter worn forgets the choice; a character not ready waited
for; a hunter the mod does not know left alone; a look refused not remembered; nothing worn outside a game; the mod
turned off gives the own look back on the character and on every picker dressed, the choices kept."""

import math
import sys

import sdk_stubs

state = sdk_stubs.install()

import fake_game  # noqa: E402
from fake_game import handed, rule  # noqa: E402
from hunter_change import choices, hunters, look, wardrobe  # noqa: E402

fails: list[str] = []
HARLOWE_GAME, OTHER_HARLOWE_GAME = "8107146506D5906AD9BCCD4479661B4D", "0000000100000002000000030000000A"
harlowe, loveless, amon = (hunters.by_code(code) for code in ("Gravitar", "CorpoHacker", "Paladin"))


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def settle(character: object) -> str:
    return wardrobe.settle(character, state["pc"].PlayerState)


def restart() -> None:
    """The game closed and launched again: new pickers, the mod's memory gone, its file kept."""
    fake_game._pickers.clear()
    look._dressed.clear()
    choices.forget()


character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
check("a game without a choice left alone, nothing rebuilt, the legs untouched", settle(character) == wardrobe.DONE
      and not handed and not state["structs"]
      and fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default")
body = fake_game.pickers_of("Gravitar")[0]
body.DefaultPart._name = "Cosmetics_Gravitar_Body00_Patched"
check("a look the mod does not know left alone in a game without a choice", settle(character) == wardrobe.DONE
      and not handed and not body.writes and body.DefaultPart._name == "Cosmetics_Gravitar_Body00_Patched")
body.DefaultPart._name = "Cosmetics_Gravitar_Body00_Default"

check("a hunter worn in a game", wardrobe.wear("Paladin")
      and fake_game.body_drawn(character) == "Cosmetics_Paladin_Body00_Default")
check("remembered for that game", choices.chosen(HARLOWE_GAME) == "Paladin")
check("the legs fitted", math.isclose(fake_game.legs_scale(character), hunters.legs_scale(harlowe, amon)))

character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
check("the same game reloaded keeps the look without a rebuild, legs fitted on the new character",
      settle(character) == wardrobe.DONE and not handed
      and math.isclose(fake_game.legs_scale(character), hunters.legs_scale(harlowe, amon)))

restart()
character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
check("after a restart the choice comes back from the file", settle(character) == wardrobe.DONE
      and fake_game.body_drawn(character) == "Cosmetics_Paladin_Body00_Default"
      and math.isclose(fake_game.legs_scale(character), hunters.legs_scale(harlowe, amon)))

character = fake_game.load(state, "Gravitar", OTHER_HARLOWE_GAME)
check("another game of the same hunter gets its own look back", settle(character) == wardrobe.DONE
      and fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default"
      and fake_game.legs_scale(character) == 1.0)

character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
settle(character)
check("the own hunter worn forgets the choice", wardrobe.wear("Gravitar") and choices.chosen(HARLOWE_GAME) is None
      and fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default"
      and fake_game.legs_scale(character) == 1.0)

character = fake_game.load(state, "Gravitar", "0" * 32)
check("a game whose id is not set yet waited for", settle(character) == wardrobe.WAIT)
character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
character.GbxActorPartOwnerState.ReplicatedSelections = []
check("a character without its pickers yet waited for", settle(character) == wardrobe.WAIT)
character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
state["pc"].PlayerState.ReplicatedCharacterDef = "Char_Echo4"
check("a hunter the mod does not know left alone", settle(character) == wardrobe.DONE and not handed
      and not wardrobe.wear("Paladin"))

character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
rule["setter_refused"] = True
check("a look refused not remembered", not wardrobe.wear("CorpoHacker") and choices.chosen(HARLOWE_GAME) is None)
choices.choose(HARLOWE_GAME, "CorpoHacker")
check("a choice that cannot be worn said failed on a new character", settle(character) == wardrobe.FAILED)
rule["setter_refused"] = False
choices.choose(HARLOWE_GAME, None)
look.dress(character, state["pc"].PlayerState, harlowe, harlowe)

character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
wardrobe.wear("CorpoHacker")
check("the look shown to the window: the hunter played and the look worn",
      wardrobe.status() == (harlowe, loveless))
wardrobe.wear("Gravitar")
check("the own look shown as the hunter played twice", wardrobe.status() == (harlowe, harlowe))
state["pc"].PlayerState.ActiveCharGuid = fake_game.id_words("0" * 32)
check("no look shown while the game is not ready", wardrobe.status() is None)

state["pc"] = None
check("nothing worn outside a game", not wardrobe.wear("Paladin") and wardrobe.status() is None)

character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
wardrobe.wear("CorpoHacker")
rafa_character = fake_game.load(state, "ExoSoldier", "4F3ED67C7CDBB85DD75426BD679FD6BC")
wardrobe.wear("Paladin")
wardrobe.undress()
rafa_body = fake_game.pickers_of("ExoSoldier")[0]
harlowe_body = fake_game.pickers_of("Gravitar")[0]
check("the mod turned off gives the own look back on the character, legs whole",
      fake_game.body_drawn(rafa_character) == "Cosmetics_ExoSoldier_Body00_Default"
      and fake_game.legs_scale(rafa_character) == 1.0)
check("and on every picker dressed, the choices kept",
      rafa_body.DefaultPart._name == "Cosmetics_ExoSoldier_Body00_Default"
      and harlowe_body.DefaultPart._name == "Cosmetics_Gravitar_Body00_Default"
      and choices.chosen(HARLOWE_GAME) == "CorpoHacker")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
