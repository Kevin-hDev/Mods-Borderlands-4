"""The wardrobe: a game without a choice left alone, nothing rebuilt nor resized, even a look the mod does not know;
a hunter worn in a game, remembered for it, with its size; the same game reloaded in the session keeps the look
without a rebuild, the size given to the new character; after a restart the choice comes back from the file; another
game of the same hunter gets its own look back; the own hunter worn forgets the choice; a character not ready waited
for; a hunter the mod does not know left alone; a look refused not remembered; nothing worn outside a game; the body
and head of an owned skin worn on another hunter's look and remembered, kept from one hunter to the next when owned,
worn again as remembered after a reload or a restart, another game of the same look getting its own skins; a skin
clicked acting on the look the window shows; the own parts back when the mod is turned off on other skins; a skin not
owned, on the own look or of no part refused; the window shown the hunter played, the look worn and the skins owned;
the mod turned off gives the own look and size back on the character and the own look on every picker dressed, the
choices kept."""

import sys

import sdk_stubs

state = sdk_stubs.install()

import fake_game  # noqa: E402
from fake_game import handed, rule  # noqa: E402
from hunter_change import choices, hunters, look, skins, wardrobe  # noqa: E402

fails: list[str] = []
HARLOWE_GAME, OTHER_HARLOWE_GAME = "8107146506D5906AD9BCCD4479661B4D", "0000000100000002000000030000000A"
harlowe, loveless = (hunters.by_code(code) for code in ("Gravitar", "CorpoHacker"))


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
check("a game without a choice left alone, nothing rebuilt nor resized", settle(character) == wardrobe.DONE
      and not handed and not state["structs"] and fake_game.size(character) == fake_game.own_size("Gravitar")
      and fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default")
body = fake_game.pickers_of("Gravitar")[0]
body.DefaultPart._name = "Cosmetics_Gravitar_Body00_Patched"
check("a look the mod does not know left alone in a game without a choice", settle(character) == wardrobe.DONE
      and not handed and not body.writes and body.DefaultPart._name == "Cosmetics_Gravitar_Body00_Patched")
body.DefaultPart._name = "Cosmetics_Gravitar_Body00_Default"

check("a hunter worn in a game", wardrobe.wear("Paladin")
      and fake_game.body_drawn(character) == "Cosmetics_Paladin_Body00_Default")
check("remembered for that game", choices.chosen(HARLOWE_GAME) == ("Paladin", "default", "default"))
check("with its size, lifted by the half height gained so the feet stay on the ground",
      fake_game.size(character) == fake_game.own_size("Paladin") and character.location.Z == 1000.0 + 115.0 - 86.0)

character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
check("the same game reloaded keeps the look without a rebuild, the size given to the new character",
      settle(character) == wardrobe.DONE and not handed
      and fake_game.size(character) == fake_game.own_size("Paladin"))

restart()
character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
check("after a restart the choice comes back from the file", settle(character) == wardrobe.DONE
      and fake_game.body_drawn(character) == "Cosmetics_Paladin_Body00_Default"
      and fake_game.size(character) == fake_game.own_size("Paladin"))

character = fake_game.load(state, "Gravitar", OTHER_HARLOWE_GAME)
check("another game of the same hunter gets its own look back", settle(character) == wardrobe.DONE
      and fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default"
      and fake_game.size(character) == fake_game.own_size("Gravitar"))

character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
settle(character)
check("the own hunter worn forgets the choice, the own size back, lowered to the ground",
      wardrobe.wear("Gravitar") and choices.chosen(HARLOWE_GAME) is None
      and fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default"
      and fake_game.size(character) == fake_game.own_size("Gravitar") and character.location.Z == 1000.0)

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
check("the window shown the hunter played, the look worn and the skins owned",
      wardrobe.status() == (harlowe, wardrobe.Look(loveless), ("default",)))
wardrobe.wear("Gravitar")
check("the own look shown as the hunter played twice",
      wardrobe.status() == (harlowe, wardrobe.Look(harlowe), ("default",)))
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
check("the mod turned off gives the own look and size back on the character",
      fake_game.body_drawn(rafa_character) == "Cosmetics_ExoSoldier_Body00_Default"
      and fake_game.size(rafa_character) == fake_game.own_size("ExoSoldier"))
check("and on every picker dressed, the choices kept",
      rafa_body.DefaultPart._name == "Cosmetics_ExoSoldier_Body00_Default"
      and harlowe_body.DefaultPart._name == "Cosmetics_Gravitar_Body00_Default"
      and choices.chosen(HARLOWE_GAME).hunter == "CorpoHacker")

OWNED = ("default", "prison", "premium")
skins.owned = lambda: owned
owned = OWNED
character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
body, head, _ = fake_game.pickers_of("Gravitar")
wardrobe.wear("CorpoHacker")
check("an owned body skin worn on another hunter's look", wardrobe.wear_skin(hunters.BODY, hunters.PREMIUM)
      and fake_game.body_drawn(character) == "Cosmetics_CorpoHacker_Body02_Premium")
check("an owned head skin worn too, the body kept", wardrobe.wear_skin(hunters.HEAD, hunters.PRISON)
      and head.DefaultPart._name == "Cosmetics_CorpoHacker_Head01_Prison"
      and body.DefaultPart._name == "Cosmetics_CorpoHacker_Body02_Premium")
check("both remembered for the game", choices.chosen(HARLOWE_GAME) == ("CorpoHacker", "premium", "prison"))
check("the window shown the skins worn",
      wardrobe.status() == (harlowe, wardrobe.Look(loveless, "premium", "prison"), OWNED))
check("kept from one hunter to the next", wardrobe.wear("Paladin")
      and fake_game.body_drawn(character) == "Cosmetics_Paladin_Body02_Premium"
      and head.DefaultPart._name == "Cosmetics_Paladin_Head01_Prison"
      and choices.chosen(HARLOWE_GAME) == ("Paladin", "premium", "prison"))
character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
handed.clear()
check("worn again as remembered on the game reloaded, without a rebuild", settle(character) == wardrobe.DONE
      and not handed)
restart()
owned = ("default",)
character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
check("worn again as remembered after a restart, before the game says what is owned",
      settle(character) == wardrobe.DONE and fake_game.body_drawn(character) == "Cosmetics_Paladin_Body02_Premium"
      and fake_game.pickers_of("Gravitar")[1].DefaultPart._name == "Cosmetics_Paladin_Head01_Prison")
owned = ("default", "prison")
check("a skin no longer owned dropped for the next hunter, the others kept", wardrobe.wear("DarkSiren")
      and fake_game.body_drawn(character) == "Cosmetics_DarkSiren_Body00_Default"
      and choices.chosen(HARLOWE_GAME) == ("DarkSiren", "default", "prison"))
errors = len(state["errors"])
check("a skin not owned refused, the look and choice unchanged",
      not wardrobe.wear_skin(hunters.BODY, hunters.PREMIUM) and len(state["errors"]) == errors + 1
      and fake_game.body_drawn(character) == "Cosmetics_DarkSiren_Body00_Default"
      and choices.chosen(HARLOWE_GAME) == ("DarkSiren", "default", "prison"))
check("a skin of no part refused", not wardrobe.wear_skin("_Legs", hunters.PRISON))
wardrobe.wear("Gravitar")
check("the own hunter forgets the skins too", choices.chosen(HARLOWE_GAME) is None)
check("a skin refused on the own look, whose skins are the game's",
      not wardrobe.wear_skin(hunters.BODY, hunters.PRISON)
      and fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default"
      and choices.chosen(HARLOWE_GAME) is None)
check("another hunter after the own one starts with the game's own skins", wardrobe.wear("Paladin")
      and choices.chosen(HARLOWE_GAME) == ("Paladin", "default", "default"))
wardrobe.wear("Gravitar")

owned = OWNED
wardrobe.wear("CorpoHacker")
wardrobe.wear_skin(hunters.BODY, hunters.PREMIUM)
character = fake_game.load(state, "Gravitar", OTHER_HARLOWE_GAME)
check("another game of the same hunter and look, but other skins, gets its own skins back",
      choices.choose(OTHER_HARLOWE_GAME, "CorpoHacker") and settle(character) == wardrobe.DONE
      and fake_game.body_drawn(character) == "Cosmetics_CorpoHacker_Body00_Default")
choices.choose(OTHER_HARLOWE_GAME, None)
settle(character)

character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
settle(character)
character = fake_game.load(state, "Gravitar", OTHER_HARLOWE_GAME)
# The game's own look not put back on this new character (its settle never ran): the window shows Loveless.
check("a skin clicked on the look the window shows, though the game's choice is its own look (audit, 2026-10-07)",
      wardrobe.status().worn == wardrobe.Look(loveless, "premium", "default")
      and wardrobe.wear_skin(hunters.HEAD, hunters.PRISON)
      and fake_game.pickers_of("Gravitar")[1].DefaultPart._name == "Cosmetics_CorpoHacker_Head01_Prison"
      and choices.chosen(OTHER_HARLOWE_GAME) == ("CorpoHacker", "premium", "prison"))
character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
settle(character)
wardrobe.undress()
check("the mod turned off on skins other than the base: the own parts back",
      fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default"
      and fake_game.pickers_of("Gravitar")[1].DefaultPart._name == "Cosmetics_Gravitar_Head00_Default")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
