"""The Hunter Change window at work: opened in a game, the APPEARANCE page shows the hunter played in its own look and
the HUNTER page its cards; a card of APPEARANCE clicked dresses the character at once, remembers the choice for the game
and says it saved; a look the game refuses says it failed; on another hunter's look the BODY and HEAD rows show a
button for each skin owned only, the one worn in gold, and a click wears it at once and remembers it, a skin clicked
with a card dropped; the rows hidden on
the own look and with one skin owned; on the HUNTER page, a card clicked shows the message and its
two buttons without dressing anyone, CANCEL brings the cards back, RETURN TO MAIN MENU refused keeps the window and says
why on the cards, accepted closes the window for the return; a language change paints the HUNTER page again; the page
follows the game while open, a game left showing no card; ENABLED turns the mod off and the page shows the own look
again; CLOSE closes. No real save: the Documents folder is the fixture's, Harlowe's game in it, and leave.ask never
starts its Windows timer."""

import sys
import weakref
from types import SimpleNamespace

import sdk_stubs

state = sdk_stubs.install()

import fake_game  # noqa: E402
import panel_fixture  # noqa: E402
import save_fixture as fx  # noqa: E402
import hunter_change  # noqa: E402
from hunter_change import choices, hunters, leave, panel_assets, panel_buttons, panel_fonts, panel_form  # noqa: E402
from hunter_change import panel_model, skins  # noqa: E402
from hunter_change import panel_switch, panel_view, save_places  # noqa: E402
from hunter_change.switch_page import BUSY, CARDS, CONFIRM  # noqa: E402

fails: list[str] = []
HARLOWE_GAME = fx.HARLOWE_GAME
HARLOWE, AMON = hunters.by_code("Gravitar"), hunters.by_code("Paladin")
documents, client = fx.saves_folder()
asked_documents: list[int] = []
found_saves: list = []
real_find = save_places.find


def documents_asked() -> list:
    """Never the real Documents folder: the fixture's, and the question counted."""
    asked_documents.append(1)
    return [documents]


def find_noted(*args, **kwargs):
    """save_places.find, each save it gives noted, to prove that the window read the fixture's only."""
    save = real_find(*args, **kwargs)
    found_saves.append(save)
    return save


save_places.documents_candidates, save_places.find = documents_asked, find_noted
owned = [("default", "prison", "premium")]
skins.owned = lambda: owned[0]
asks: list[tuple] = []
accepts = [True]


def ask(game: str, current: str, wanted: str) -> bool:
    """leave.ask without its Windows timer: the request noted, accepted or refused as the test says."""
    asks.append((game, current, wanted))
    return accepts[0]


leave.ask = ask


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


panel_fixture.install()
panel_assets.texture = lambda _world, name=panel_assets.AVATAR: object()
panel_fonts.build = lambda _root: {"title": object(), "body": object()}

fx.put(client, 4, fx.game_text(HARLOWE_GAME, HARLOWE.code, HARLOWE.name, fx.TREES[HARLOWE.code]))
character = fake_game.load(state, HARLOWE.code, HARLOWE_GAME)
model = panel_model.Model(hunter_change.mod)
_root, widgets = panel_view.build_view(SimpleNamespace(), model)
form = panel_form.PanelForm({name: weakref.ref(widget) for name, widget in widgets.items()}, model)


def text(name: str) -> str | None:
    """None for a text never painted, so that a page left unpainted fails its check instead of stopping the test."""
    try:
        return panel_fixture.text(widgets, name)
    except KeyError:
        return None


def shown(name: str) -> bool:
    return widgets[name].calls.get("SetVisibility", (None,))[0] == "ESlateVisibility.Visible"


def gold(name: str) -> bool:
    """The button filled as the one chosen, in the switch style "on"."""
    return widgets[f"{name}_fill"].calls["SetBrushColor"] == (panel_buttons.w.linear(panel_buttons.colours("on")[0]),)


def click(name: str) -> object:
    widgets[name].checked = True
    return form.poll()


check("opened in a game, the page shows the hunter played in its own look",
      shown("hunter:Gravitar_own_tag") and not shown("hunter:Gravitar_chosen_tag")
      and text("hunter_state").startswith("You play Harlowe."))
check("opened in a game, the HUNTER page shows its cards", form.switch_page.view.kind == CARDS
      and form.switch_page.view.current == HARLOWE and shown("switch_grid") and not shown("switch_confirm")
      and text("switch_state") == "You play Harlowe. Choose a hunter to become them in this game.")

click("hunter:CorpoHacker")
check("a card clicked dresses the character at once",
      fake_game.body_drawn(character) == "Cosmetics_CorpoHacker_Body00_Default")
check("remembers the choice for the game and says it saved",
      choices.chosen(HARLOWE_GAME) == choices.Choice("CorpoHacker")
      and text("notice") == "Saved." and shown("hunter:CorpoHacker_chosen_tag")
      and not widgets["hunter:CorpoHacker"].checked)

fake_game.rule["setter_refused"] = True
click("hunter:Paladin")
check("a look the game refuses says it failed", text("notice") != "Saved."
      and fake_game.body_drawn(character) == "Cosmetics_CorpoHacker_Body00_Default"
      and choices.chosen(HARLOWE_GAME) == choices.Choice("CorpoHacker"))
fake_game.rule["setter_refused"] = False

# A refused rebuild leaves the pickers on the own look (look.dress): the card is clicked again.
click("hunter:CorpoHacker")
check("on another hunter's look, the BODY and HEAD rows with a button per skin owned, the game's own in gold",
      shown("skins") and all(shown(f"skin:{part}:{skin}_box") for part in ("body", "head")
                             for skin in ("default", "prison", "premium"))
      and text("label:skin_body") == "Body"
      and text("description:skin_head") == "Loveless's head, to mix with any body."
      and text("skin:body:premium_label") == "PREMIUM" and gold("skin:body:default") and not gold("skin:body:premium"))
click("skin:body:premium")
check("a skin clicked worn at once, remembered and said saved, in gold",
      fake_game.body_drawn(character) == "Cosmetics_CorpoHacker_Body02_Premium"
      and choices.chosen(HARLOWE_GAME) == choices.Choice("CorpoHacker", "premium") and text("notice") == "Saved."
      and gold("skin:body:premium") and not gold("skin:body:default") and gold("skin:head:default")
      and not widgets["skin:body:premium"].checked)
owned[0] = ("default", "premium")
form.poll()
check("a skin not owned has no button", shown("skin:head:premium_box") and not shown("skin:head:prison_box"))
owned[0] = ("default",)
form.poll()
check("the rows hidden with the game's own skin alone", not shown("skins"))
owned[0] = ("default", "prison", "premium")
click("hunter:Gravitar")
check("the rows hidden on the own look", not shown("skins") and choices.chosen(HARLOWE_GAME) is None
      and fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default")
widgets["skin:body:prison"].checked = True
click("hunter:CorpoHacker")
form.poll()
check("a skin clicked with a card dropped: the card worn, the skin neither worn then nor at the next poll",
      fake_game.body_drawn(character) == "Cosmetics_CorpoHacker_Body00_Default"
      and choices.chosen(HARLOWE_GAME) == choices.Choice("CorpoHacker") and not widgets["skin:body:prison"].checked)

# The HUNTER page, in the same window.
click("nav:hunter")
check("the HUNTER page shown from its button in the sidebar", widgets["pages"].calls["SetActiveWidgetIndex"][0] == 1)
answer = click("switch:Paladin")
check("a card of the HUNTER page clicked shows the message and its two buttons, dressing no one",
      answer is False and form.switch_page.view.kind == CONFIRM and form.switch_page.view.wanted == AMON
      and shown("switch_confirm") and not shown("switch_grid") and not shown("switch_state")
      and text("switch_message").startswith("You will become Amon in this game")
      and text("switch_leave_label") == "RETURN TO MAIN MENU" and text("switch_cancel_label") == "CANCEL"
      and not widgets["switch:Paladin"].checked and not asks
      and fake_game.body_drawn(character) == "Cosmetics_CorpoHacker_Body00_Default")
check("CANCEL brings the cards back", click("switch_cancel") is False and form.switch_page.view.kind == CARDS
      and shown("switch_grid") and shown("switch_state") and not shown("switch_confirm"))

click("switch:Paladin")
accepts[0] = False
answer = click("switch_leave")
check("RETURN TO MAIN MENU refused keeps the window and says why on the cards",
      answer is False and asks == [(HARLOWE_GAME, "Gravitar", "Paladin")] and form.switch_page.view.kind == CARDS
      and shown("switch_grid") and not shown("switch_confirm")
      and text("switch_state") == "The game could not go back to the main menu. Nothing was changed. Try again.")

click("switch:Paladin")
accepts[0] = True
asks.clear()
answer = click("switch_leave")
check("RETURN TO MAIN MENU with the change asked closes the window for the return",
      answer == panel_switch.LEAVE == "leave" and asks == [(HARLOWE_GAME, "Gravitar", "Paladin")]
      and form.switch_page.view.kind == BUSY)

# The fake request never makes leave.py busy: the page follows back to its cards, then its texts change language.
click("FR")
check("a language change paints the HUNTER page again", text("switch_leave_label") == "REVENIR AU MENU PRINCIPAL"
      and text("switch_cancel_label") == "ANNULER"
      and text("switch_state") == "Tu joues Harlowe. Choisis un chasseur pour le devenir dans cette partie.")
click("EN")
check("and back in English", text("switch_leave_label") == "RETURN TO MAIN MENU"
      and text("switch_state") == "You play Harlowe. Choose a hunter to become them in this game.")

state["pc"] = None
form.poll()
check("the page follows the game while open, a game left showing no card",
      not shown("hunter_grid") and not shown("hunter_applies") and text("hunter_state") == "Load a game to choose a look.")

# The same game loaded again: its choice is put back by the mod, then the window is back on it.
character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
hunter_change.lifecycle.on_frame(1.0)
form.poll()
click("enabled")
form.poll()
check("ENABLED turns the mod off and the page shows the own look again", not hunter_change.mod.is_enabled
      and fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default"
      and text("hunter_state").startswith("You play Harlowe."))
chosen_before = choices.chosen(HARLOWE_GAME)
click("hunter:Paladin")
check("with the mod off, a card clicked changes nothing, the cards greyed and the frame saying to turn it on",
      fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default"
      and choices.chosen(HARLOWE_GAME) == chosen_before and not widgets["hunter:Paladin"].checked
      and widgets["hunter_grid"].calls["SetIsEnabled"] == (False,)
      and text("notice:applies").startswith("HUNTER CHANGE IS OFF"))

check("CLOSE closes", click("close") is True)
check("the saves read are the fixture's only, from its Documents folder",
      asked_documents and found_saves and save_places.documents_candidates is documents_asked
      and all(save is not None and save.path.is_relative_to(documents) for save in found_saves))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
