"""The look: the body and head pickers found among the selections, within their bound; the hunter worn told by the body
picker's default; the outfit worn read as its chosen parts in order; another hunter dressed with its defaults written
typed and read back, the rest of the outfit handed back after one own body part, whatever the body and head chosen;
the own look given back with the outfit worn as it is; a default refused or not taken puts the own ones back and
hands nothing; a refused rebuild said and the own defaults put back; a character without the two pickers refused; the
other hunters' pickers dressed this session undressed all at once, without a rebuild."""

import sys
import types

import sdk_stubs

state = sdk_stubs.install()

import fake_game  # noqa: E402
from fake_game import handed, rule  # noqa: E402
from hunter_change import hunters, look  # noqa: E402

fails: list[str] = []
HARLOWE_GAME, RAFA_GAME = "8107146506D5906AD9BCCD4479661B4D", "4F3ED67C7CDBB85DD75426BD679FD6BC"
harlowe, rafa, loveless, amon = (hunters.by_code(code) for code in ("Gravitar", "ExoSoldier", "CorpoHacker", "Paladin"))


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def player_state() -> object:
    return state["pc"].PlayerState


character = fake_game.load(state, "Gravitar", HARLOWE_GAME, "gap,Cosmetics_Colorization_Primary[Colour9]")
body, head, _skin = fake_game.pickers_of("Gravitar")
check("the body and head pickers found among the selections", look.pickers(character) == {
    hunters.BODY: body, hunters.HEAD: head})
far = types.SimpleNamespace(GbxActorPartOwnerState=types.SimpleNamespace(ReplicatedSelections=[
    types.SimpleNamespace(SelectorDef=fake_game.colour_picker)] * look.MAX_SELECTIONS
    + character.GbxActorPartOwnerState.ReplicatedSelections))
check("the pickers searched within their bound", look.pickers(far) is None)
check("the hunter worn told by the body picker's default", look.wearing(look.pickers(character)) == harlowe)
check("the outfit worn read as its chosen parts in order",
      look.outfit(character) == [("Cosmetics_Colorization_Primary", "Colour9")]
      and look.outfit_text(look.outfit(character)) == "gap,Cosmetics_Colorization_Primary[Colour9]")

check("another hunter dressed", look.dress(character, player_state(), harlowe, loveless)
      and look.wearing(look.pickers(character)) == loveless)
check("its defaults written typed as the pickers' own and read back",
      body.DefaultPart._name == "Cosmetics_CorpoHacker_Body00_Default" and body.DefaultPart._type is fake_game.GESTALT
      and head.DefaultPart._name == "Cosmetics_CorpoHacker_Head00_Default")
check("the rest of the outfit handed back after one own body part, the other hunter's body drawn",
      handed == ["gap,Cosmetics_Gravitar_Body[Cosmetics_Gravitar_Body01_Prison]",
                 "gap,Cosmetics_Colorization_Primary[Colour9]"]
      and fake_game.body_drawn(character) == "Cosmetics_CorpoHacker_Body00_Default")

handed.clear()
check("the own look given back", look.dress(character, player_state(), harlowe, harlowe)
      and body.DefaultPart._name == "Cosmetics_Gravitar_Body00_Default"
      and fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default")
check("with the outfit worn as it is", handed[-1] == "gap,Cosmetics_Colorization_Primary[Colour9]")

chosen = ("gap,Cosmetics_ExoSoldier_Body[Cosmetics_ExoSoldier_Body01_Prison],"
          "Cosmetics_ExoSoldier_Head[Cosmetics_ExoSoldier_Head00_Default_Alt],"
          "Cosmetics_ExoSoldier_Skin[Cosmetics_ExoSoldier_SkinFilter01_Prison],Cosmetics_Colorization_Primary[Colour9]")
character = fake_game.load(state, "ExoSoldier", RAFA_GAME, chosen)
look.dress(character, player_state(), rafa, loveless)
check("the body and head chosen left out, the rest kept, the other hunter drawn (essai 31)",
      handed[-1] == "gap,Cosmetics_ExoSoldier_Skin[Cosmetics_ExoSoldier_SkinFilter01_Prison],"
                    "Cosmetics_Colorization_Primary[Colour9]"
      and fake_game.body_drawn(character) == "Cosmetics_CorpoHacker_Body00_Default")
look.dress(character, player_state(), rafa, rafa)

rafa_body, rafa_head, _ = fake_game.pickers_of("ExoSoldier")
handed.clear()
rule["refuse"] = "Cosmetics_Paladin_Head00_Default"
check("a default refused puts the own ones back and hands nothing",
      not look.dress(character, player_state(), rafa, amon) and not handed
      and rafa_body.DefaultPart._name == "Cosmetics_ExoSoldier_Body00_Default"
      and "Amon" in state["errors"][-1])
rule["refuse"], rule["ignore"] = None, "Cosmetics_Paladin_Body00_Default"
check("a default not taken puts the own ones back and hands nothing",
      not look.dress(character, player_state(), rafa, amon) and not handed
      and rafa_head.DefaultPart._name == "Cosmetics_ExoSoldier_Head00_Default")
rule["ignore"] = None
rule["setter_refused"] = True
errors = len(state["errors"])
check("a refused rebuild said, the own defaults put back to match the character still drawn",
      not look.dress(character, player_state(), rafa, amon) and len(state["errors"]) == errors + 1
      and rafa_body.DefaultPart._name == "Cosmetics_ExoSoldier_Body00_Default"
      and look.wearing(look.pickers(character)) == rafa)
rule["setter_refused"] = False
look.dress(character, player_state(), rafa, rafa)
bare = fake_game.Character([types.SimpleNamespace(SelectorDef=fake_game.colour_picker)], fake_game.Legs())
check("a character without the two pickers refused", not look.dress(bare, player_state(), rafa, amon))

character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
look.dress(character, player_state(), harlowe, amon)
character = fake_game.load(state, "ExoSoldier", RAFA_GAME)
look.dress(character, player_state(), rafa, loveless)
handed.clear()
look.undress_all()
check("the pickers dressed this session undressed all at once, without a rebuild",
      body.DefaultPart._name == "Cosmetics_Gravitar_Body00_Default"
      and head.DefaultPart._name == "Cosmetics_Gravitar_Head00_Default"
      and rafa_body.DefaultPart._name == "Cosmetics_ExoSoldier_Body00_Default" and not handed)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
