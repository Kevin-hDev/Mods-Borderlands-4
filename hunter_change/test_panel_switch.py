"""The HUNTER page of the window: the window has two pages, APPEARANCE and HUNTER, each with its button in the sidebar;
the HUNTER page's cards never replace the APPEARANCE page's; nowhere, no card, no frame, no message, only a sentence
asking for a game; no change possible, no card and only why, or only the end of the last change when there is one, never
both, as any end is said alone whatever the page shows; a change running, no card; in a game, the cards and the orange
frame saying what a change keeps, YOUR HUNTER on the hunter played only and CHOSEN on none; at the title screen, the
cards and the sentence saying the change is made at once, or the end of the last change alone, naming the hunter asked
for; a click in a game, the cards and the sentence replaced by the message and its two buttons, the message telling
whether the new hunter's tree is kept; the texts in French; every end of a change said, every text in both languages
with the same blanks; the page's clicks read once, on its own cards only, RETURN TO MAIN MENU closing the window only
when the change is asked, the game followed with nothing clicked. No real save: the Documents folder is the fixture's,
and never asked."""

import re
import string
import sys
from types import SimpleNamespace

import sdk_stubs

state = sdk_stubs.install()

import panel_fixture  # noqa: E402
import save_fixture as fx  # noqa: E402
from hunter_change import hunters, leave, panel_assets, panel_en, panel_fonts, panel_form, panel_fr  # noqa: E402
from hunter_change import panel_hunters, panel_i18n as i18n, panel_model, panel_switch, panel_switch_text  # noqa: E402
from hunter_change import panel_view, save_places, switch  # noqa: E402
from hunter_change.switch_page import BUSY, CARDS, CONFIRM, NOWHERE, UNAVAILABLE, View  # noqa: E402

fails: list[str] = []
documents, _client = fx.saves_folder()
asked_documents: list[int] = []


def documents_asked() -> list:
    """Never the real Documents folder: the fixture's, and the question counted."""
    asked_documents.append(1)
    return [documents]


save_places.documents_candidates = documents_asked


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


panel_fixture.install()
panel_assets.texture = lambda _world, name=panel_assets.AVATAR: object()
panel_fonts.build = lambda _root: {"title": object(), "body": object()}
HARLOWE, AMON = hunters.by_code("Gravitar"), hunters.by_code("Paladin")

# 1. The two pages.
model = panel_model.Model(SimpleNamespace(is_enabled=True))
_root, window = panel_view.build_view(SimpleNamespace(), model)
nav = window["nav:appearance"]
check("two pages, APPEARANCE then HUNTER, each with its button in the sidebar",
      model.pages == ("appearance", panel_switch.KEY) == ("appearance", "hunter")
      and len(window["pages"].children) == 2 and "nav:hunter" in window
      and window["nav:hunter"] is not nav)

# The HUNTER page built as the window will build it, after the APPEARANCE page and into the same widgets.
widgets: dict = {}
owner = panel_fixture.Widget("WidgetSwitcher", None)
template = panel_fixture.Widget("InputKeySelector", None).WidgetStyle.Normal
panel_hunters.page(owner, "appearance", widgets, template, SimpleNamespace())
appearance = dict(widgets)
hunter_scroll = panel_switch.page(owner, panel_switch.KEY, widgets, template, SimpleNamespace())
check("the HUNTER page's cards never replace the APPEARANCE page's",
      all(widgets[name] is widget for name, widget in appearance.items())
      and all(widgets.get(f"switch:{hunter.code}") not in (None, widgets[f"hunter:{hunter.code}"])
              for hunter in hunters.HUNTERS)
      and [len(line.children) for line in widgets["switch_grid"].children] == [3, 3])


def tree(node) -> set[int]:
    return {id(node)}.union(*(tree(child) for child in node.children))


check("every widget of the HUNTER page in the page", all(
    id(widget) in tree(hunter_scroll) for name, widget in widgets.items() if name not in appearance))


def text(name: str) -> str:
    return panel_fixture.text(widgets, name)


def shown(name: str) -> bool:
    return widgets[name].calls["SetVisibility"][0] == "ESlateVisibility.Visible"


def page_shows(view: View, language: str) -> tuple[bool, bool, bool, bool]:
    """Paints the view; then whether the frame, the cards, the sentence and the confirmation are shown."""
    panel_switch.paint(widgets, view, language)
    return shown("switch_keeps"), shown("switch_grid"), shown("switch_state"), shown("switch_confirm")


def said(reason: str) -> switch.Outcome:
    return switch.Outcome(reason)


# 2. The page for each kind of view.
check("nowhere, no card, no frame, no message, only a sentence asking for a game",
      page_shows(View(NOWHERE), "EN") == (False, False, True, False)
      and text("switch_state") == "Load a game, or select one at the title screen, to change its hunter."
      and text("switch_message") == "")
reasons = {why: all(page_shows(View(UNAVAILABLE, in_game, why=why), language) == (False, False, True, False)
                    and text("switch_state") == i18n.text(f"why:{why}", language)
                    for in_game in (True, False) for language in ("EN", "FR"))
           for why in ("no_save", "two_saves", "saves_unsure", "save_damaged", "unknown_hunter", "trees_unreadable",
                       "not_this_hunter")}
check("no change possible, no card and only why, for each reason", all(reasons.values())
      and page_shows(View(UNAVAILABLE, why="not_this_hunter"), "EN")[1] is False
      and text("switch_state") == "This game's hunter cannot be changed: its save does not show the hunter you play. "
                                  "Load it again.")
page_shows(View(UNAVAILABLE, why="no_save", said=said("restore_failed"), said_to=AMON), "EN")
after_en = text("switch_state")
page_shows(View(UNAVAILABLE, why="no_save", said=said("restore_failed"), said_to=AMON), "FR")
check("no change possible after the end of the last change: only the end, never why beside it",
      after_en == "The save could not be written or put back. Do not load this game and ask for help on the mod's "
                  "page: the mod kept a backup copy of it."
      and text("switch_state") == "La sauvegarde n'a pas pu être écrite ni remise. Ne charge pas cette partie et "
                                  "demande de l'aide sur la page du mod : le mod en a gardé une copie de sécurité."
      and i18n.text("why:no_save", "EN") not in after_en
      and i18n.text("why:no_save", "FR") not in text("switch_state"))


def state_after(view: View, language: str) -> str:
    page_shows(view, language)
    return text("switch_state")


check("an end and why saying the same thing, said once",
      all(state_after(View(UNAVAILABLE, in_game, why=why, said=said(reason), said_to=AMON), language)
          == i18n.text(panel_switch_text.SAID[reason], language)
          for why, reason in (("no_save", "no_save"), ("trees_unreadable", "trees_unreadable"))
          for in_game in (True, False) for language in ("EN", "FR")))
gave_up = {language: i18n.text("said:gave_up", language) for language in ("EN", "FR")}
check("an end said alone whatever the page shows", all(
    panel_switch_text.state(View(kind, True, HARLOWE, AMON, why="no_save", said=said(leave.GAVE_UP), said_to=AMON),
                            language) == gave_up[language]
    for kind in (NOWHERE, UNAVAILABLE, BUSY, CARDS, CONFIRM) for language in ("EN", "FR")))
page_shows(View(UNAVAILABLE, True, why="no_save"), "EN")
no_save_en = text("switch_state")
page_shows(View(UNAVAILABLE, True, why="no_save"), "FR")
check("no save, said as it is, the game said untouched",
      no_save_en == "This game's hunter cannot be changed: the mod does not find its save in the game's saves folder. "
                    "Your game is untouched and plays as before."
      and text("switch_state") == "Le chasseur de cette partie ne peut pas être changé : le mod ne trouve pas sa "
                                  "sauvegarde dans le dossier des sauvegardes du jeu. Ta partie n'est pas touchée et "
                                  "se joue comme avant.")
page_shows(View(UNAVAILABLE, True, why="two_saves"), "EN")
two_saves_en = text("switch_state")
page_shows(View(UNAVAILABLE, True, why="two_saves"), "FR")
check("a game in two saves, said as it is, with what the player can do",
      two_saves_en == "This game's hunter cannot be changed: this game is in several save files, and the mod cannot "
                      "tell which one the game uses. Your game is untouched and plays as before. If one is an old "
                      "copy you no longer need, move it out of the game's saves folder to change hunters."
      and text("switch_state") == "Le chasseur de cette partie ne peut pas être changé : cette partie est dans "
                                  "plusieurs fichiers de sauvegarde, et le mod ne sait pas lequel le jeu utilise. Ta "
                                  "partie n'est pas touchée et se joue comme avant. Si l'un est une ancienne copie "
                                  "dont tu n'as plus besoin, déplace-le hors du dossier des sauvegardes du jeu pour "
                                  "pouvoir changer de chasseur.")
page_shows(View(UNAVAILABLE, True, why="saves_unsure"), "FR")
check("saves that could not all be read, said with the likely cause and to try again",
      text("switch_state") == "Le chasseur de cette partie ne peut pas être changé pour l'instant : le mod n'a pas pu "
                              "lire toutes les sauvegardes du jeu ; un autre programme, comme OneDrive, les utilisait "
                              "peut-être. Ta partie n'est pas touchée. Rouvre cette fenêtre dans un moment.")
page_shows(View(UNAVAILABLE, True, why="save_damaged"), "EN")
damaged_en = text("switch_state")
page_shows(View(UNAVAILABLE, True, why="unknown_hunter"), "EN")
check("a save not read whole, and a hunter the mod does not know, each said as it is",
      damaged_en == "This game's hunter cannot be changed: its save could not be read whole, so the mod leaves it "
                    "untouched."
      and text("switch_state") == "This game's hunter cannot be changed: the mod does not know this game's hunter "
                                  "yet. Your game is untouched and plays as before.")
page_shows(View(UNAVAILABLE, why="trees_unreadable"), "EN")
trees_en = text("switch_state")
page_shows(View(UNAVAILABLE, why="trees_unreadable"), "FR")
check("no tree file, the games said untouched",
      trees_en == "No hunter can be changed: the mod's file of kept skill trees could not be read. Your games are "
                  "untouched and play as before."
      and text("switch_state") == "Aucun chasseur ne peut être changé : le fichier des arbres de compétences gardés "
                                  "par le mod est illisible. Tes parties ne sont pas touchées et se jouent comme "
                                  "avant.")
NEXT = {
    "no_save": "The mod did not find this game's save. Nothing was changed: your game plays as before.",
    "two_saves": "This game is in several save files, and the mod cannot tell which one the game uses. Nothing was "
                 "changed: your game plays as before. If one is an old copy you no longer need, move it out of the "
                 "game's saves folder to change hunters.",
    "saves_unsure": "The mod could not read all of the game's saves; another program, such as OneDrive, may have been "
                    "using them. Nothing was changed. Try again in a moment.",
    "save_damaged": "This game's save could not be read whole. Nothing was changed: the mod leaves it untouched.",
    "not_this_hunter": "This game's save changed meanwhile. Nothing was changed. Try again.",
    "foreign_tree": "This game's skill tree could not be changed safely. Nothing was changed: the game plays as "
                    "before.",
    "trees_unreadable": "The mod's file of kept skill trees could not be read. Nothing was changed: the game plays as "
                        "before.",
    leave.NO_RETURN: "The game could not go back to the main menu. Nothing was changed. Try again.",
    leave.GAVE_UP: "The game took too long to reach the main menu. Nothing was changed. Try again.",
    leave.LOADED: "A game was loaded before the hunter could be changed. Nothing was changed. Try again.",
}
NEXT_FR = {
    "no_save": "Le mod n'a pas trouvé la sauvegarde de cette partie. Rien n'a changé : ta partie se joue comme avant.",
    "two_saves": "Cette partie est dans plusieurs fichiers de sauvegarde, et le mod ne sait pas lequel le jeu "
                 "utilise. Rien n'a changé : ta partie se joue comme avant. Si l'un est une ancienne copie dont tu "
                 "n'as plus besoin, déplace-le hors du dossier des sauvegardes du jeu pour pouvoir changer de "
                 "chasseur.",
    "saves_unsure": "Le mod n'a pas pu lire toutes les sauvegardes du jeu ; un autre programme, comme OneDrive, les "
                    "utilisait peut-être. Rien n'a changé. Réessaie dans un moment.",
    "save_damaged": "La sauvegarde de cette partie n'a pas pu être lue en entier. Rien n'a changé : le mod n'y touche "
                    "pas.",
    "not_this_hunter": "La sauvegarde de cette partie a changé entre-temps. Rien n'a changé. Réessaie.",
    "prepare_failed": "L'arbre de compétences de cette partie n'a pas pu être changé sans risque. Rien n'a changé : "
                      "la partie se joue comme avant.",
    "trees_unreadable": "Le fichier des arbres de compétences gardés par le mod est illisible. Rien n'a changé : la "
                        "partie se joue comme avant.",
    leave.NO_RETURN: "Le jeu n'a pas pu revenir au menu principal. Rien n'a changé. Réessaie.",
    leave.GAVE_UP: "Le jeu a mis trop de temps à revenir au menu principal. Rien n'a changé. Réessaie.",
    leave.LOADED: "Une partie a été chargée avant que le chasseur puisse être changé. Rien n'a changé. Réessaie.",
}


def end_said(reason: str, language: str) -> str:
    page_shows(View(CARDS, False, HARLOWE, said=said(reason), said_to=AMON), language)
    return text("switch_state")


check("each end that changed nothing says what to do next",
      all(end_said(reason, "EN") == sentence for reason, sentence in NEXT.items())
      and all(end_said(reason, "FR") == sentence for reason, sentence in NEXT_FR.items()))
check("a change running, no card",
      page_shows(View(BUSY, True), "EN") == (False, False, True, False)
      and text("switch_state") == "Hunter Change is changing this game's hunter. Wait a few seconds, then open this "
                                  "window again.")

check("in a game, the cards and the orange frame saying what a change keeps",
      page_shows(View(CARDS, True, HARLOWE), "EN") == (True, True, True, False)
      and text("notice:keeps") == "SAME LEVEL, SAME BACKPACK, SAME STORY. EACH HUNTER KEEPS THEIR SKILL TREE."
      and text("switch_state") == "You play Harlowe. Choose a hunter to become them in this game.")
check("YOUR HUNTER on the hunter played only and CHOSEN on none",
      text("switch:Gravitar_own") == "YOUR HUNTER"
      and [hunter.code for hunter in hunters.HUNTERS if shown(f"switch:{hunter.code}_own_tag")] == ["Gravitar"]
      and not any(shown(f"switch:{hunter.code}_chosen_tag") for hunter in hunters.HUNTERS)
      and text("switch:Paladin_name") == "AMON" and text("switch:Paladin_class") == "FORGEKNIGHT")

check("at the title screen, the cards and the sentence saying the change is made at once",
      page_shows(View(CARDS, False, HARLOWE), "EN") == (True, True, True, False)
      and text("switch_state") == "This game's hunter is Harlowe. Choose a hunter: the change is made at once.")
page_shows(View(CARDS, False, HARLOWE, said=said(switch.DONE), said_to=AMON), "EN")
check("or the end of the last change alone, naming the hunter asked for",
      text("switch_state") == "Amon is now this game's hunter. Close this window, click another game, then this one "
                              "again: it will show Amon.")

check("a click in a game, the cards and the sentence replaced by the message and its two buttons",
      page_shows(View(CONFIRM, True, HARLOWE, AMON), "EN") == (False, False, False, True)
      and text("switch_leave_label") == "RETURN TO MAIN MENU" and text("switch_cancel_label") == "CANCEL")
check("the message telling how each hunter's skill tree is kept, and all points free the first time",
      text("switch_message") == "You will become Amon in this game: same level, same backpack, same story. For each "
                                "hunter, the first time you become them in this game, their skill tree starts over "
                                "with all your points to spend; the next times, the points you already spent stay in "
                                "place. Harlowe's skill tree is kept for Harlowe's return. Amon has no skill tree in "
                                "this game yet: all your points will be free to spend. The game saves your game and "
                                "takes you back to the main menu. There, wait 5 seconds, click another game, then "
                                "this one again: it will show Amon. Then Continue.")
page_shows(View(CONFIRM, True, HARLOWE, AMON, kept=True), "EN")
check("or given back when kept",
      "Harlowe's return. Amon gets their skill tree back, with the points you spent. The game saves"
      in text("switch_message"))

page_shows(View(CONFIRM, True, HARLOWE, AMON), "FR")
check("the texts in French: the message and its buttons",
      text("switch_message") == "Tu vas devenir Amon dans cette partie : même niveau, même sac, même histoire. "
                                "Pour chaque chasseur, la première fois que tu le deviens dans cette partie, son "
                                "arbre de compétences est remis à zéro et tous tes points sont à placer ; les fois "
                                "suivantes, les points que tu lui as déjà placés restent en place. Harlowe garde le "
                                "sien pour son retour. Amon n'a pas encore d'arbre de compétences dans cette partie : "
                                "tous tes points seront à placer. Le jeu enregistre ta partie et te ramène au menu "
                                "principal. Là, attends 5 secondes, clique sur une autre partie, puis de nouveau sur "
                                "celle-ci : elle affichera Amon. Puis Continuer."
      and text("switch_leave_label") == "REVENIR AU MENU PRINCIPAL" and text("switch_cancel_label") == "ANNULER")
page_shows(View(CONFIRM, True, HARLOWE, AMON, kept=True), "FR")
check("the texts in French: a tree given back",
      "pour son retour. Amon retrouve le sien, avec les points que tu lui avais placés. Le jeu"
      in text("switch_message"))
page_shows(View(CARDS, True, HARLOWE), "FR")
check("the texts in French: the cards in a game",
      text("notice:keeps") == "MÊME NIVEAU, MÊME SAC, MÊME HISTOIRE. CHAQUE CHASSEUR GARDE SON ARBRE DE "
                               "COMPÉTENCES."
      and text("switch_state") == "Tu joues Harlowe. Choisis un chasseur pour le devenir dans cette partie."
      and text("switch:Gravitar_own") == "TON CHASSEUR")
check("the texts in French: at the title screen",
      page_shows(View(CARDS, False, HARLOWE), "FR")[1]
      and text("switch_state") == "Le chasseur de cette partie est Harlowe. Choisis un chasseur : le changement se "
                                  "fait tout de suite.")
page_shows(View(CARDS, False, HARLOWE, said=said(leave.ERROR), said_to=AMON), "FR")
check("the texts in French: an end of a change",
      text("switch_state") == "Un problème est survenu pendant le changement de la sauvegarde. Clique sur une autre "
                              "partie, puis de nouveau sur celle-ci, pour voir son chasseur.")
check("the texts in French: nowhere and busy",
      page_shows(View(NOWHERE), "FR")[2]
      and text("switch_state") == "Charge une partie, ou sélectionne-la à l'écran titre, pour changer son chasseur."
      and page_shows(View(BUSY, True), "FR")[2]
      and text("switch_state") == "Hunter Change est en train de changer le chasseur de cette partie. Attends quelques "
                                  "secondes, puis rouvre cette fenêtre.")

# 3. Every end said, every text in both languages.
ends = (switch.DONE, *switch.REFUSALS, *switch.FAILURES, leave.NO_RETURN, leave.GAVE_UP, leave.LOADED, leave.ERROR)
check("every end of a change said", set(panel_switch_text.SAID) == set(ends)
      and all(key in panel_en.TEXT and key in panel_fr.TEXT for key in panel_switch_text.SAID.values()))
ADDED = ("hunter", "keeps", "switch_nowhere", "switch_busy", "why:no_save", "why:two_saves", "why:saves_unsure",
         "why:save_damaged", "why:unknown_hunter", "why:trees_unreadable",
         "why:not_this_hunter", "switch_in_game", "switch_at_title", "confirm", "tree_first", "tree_back",
         "leave_button", "cancel_button", *panel_switch_text.SAID.values())


def blanks(sentence: str) -> set[str]:
    return {field for _, field, _, _ in string.Formatter().parse(sentence) if field is not None}


def formats(sentence: str) -> bool:
    try:
        sentence.format(**{field: "X" for field in blanks(sentence)})
        return True
    except (IndexError, KeyError, ValueError):
        return False


check("every text in both languages with the same blanks, each sentence filled without error",
      all(key in panel_en.TEXT and key in panel_fr.TEXT for key in ADDED)
      and all(blanks(panel_en.TEXT[key]) == blanks(panel_fr.TEXT[key]) for key in ADDED)
      and all(formats(panel_en.TEXT[key]) and formats(panel_fr.TEXT[key]) for key in ADDED)
      and panel_fr.GROUPS.get("hunter") == "Deviens un autre chasseur dans cette partie.")
check("no French sentence puts de before a hunter's name, as de Amon would read",
      not any(re.search(r"\bde [AEIOU]", panel_fr.TEXT[key].format(**dict.fromkeys(blanks(panel_fr.TEXT[key]),
                                                                                   hunter.name)))
              for key in ADDED for hunter in hunters.HUNTERS))
check("no long dash in the French texts",
      not any("\u2014" in value for value in (*panel_fr.TEXT.values(), *panel_fr.GROUPS.values())))


# 4. The page's clicks.
class Page:
    """switch_page.SwitchPage as poll sees it: each call noted."""

    def __init__(self) -> None:
        self.view, self.calls = View(CARDS, True, HARLOWE), []
        self.leaves, self.follows = True, False

    def click(self, code: str) -> None:
        self.calls.append(("click", code))
        self.view = View(CONFIRM, True, HARLOWE, hunters.by_code(code))

    def cancel(self) -> None:
        self.calls.append(("cancel",))
        self.view = View(CARDS, True, HARLOWE)

    def leave(self) -> bool:
        self.calls.append(("leave",))
        return self.leaves

    def follow(self) -> bool:
        self.calls.append(("follow",))
        return self.follows


fake = Page()
form = SimpleNamespace(take=panel_form.PanelForm.take, switch_page=fake, model=SimpleNamespace(language="EN"))


def poll(*clicked: str) -> object:
    """One poll with these widgets clicked; the sentence's last text forgotten, so that a repaint shows."""
    for name in clicked:
        widgets[name].checked = True
    fake.calls.clear()
    widgets["switch_state"].calls.pop("SetText", None)
    return panel_switch.poll(form, widgets)


def painted() -> bool:
    return "SetText" in widgets["switch_state"].calls


panel_switch.paint(widgets, fake.view, "EN")
answer = poll("switch:Paladin")
check("a card clicked asks for it and shows the message, read once",
      answer is True and fake.calls == [("click", "Paladin")] and shown("switch_confirm")
      and text("switch_message").startswith("You will become Amon") and not widgets["switch:Paladin"].checked
      and poll() is False and fake.calls == [("follow",)])
answer = poll("switch:Paladin", "switch:DarkSiren")
check("two cards clicked in one poll: one asked, both dropped", answer is True
      and fake.calls == [("click", "DarkSiren")]
      and not widgets["switch:Paladin"].checked and not widgets["switch:DarkSiren"].checked
      and poll() is False and fake.calls == [("follow",)])
check("CANCEL cancels and shows the cards again", poll("switch_cancel") is True and fake.calls == [("cancel",)]
      and shown("switch_grid") and not shown("switch_confirm"))
fake.view = View(CONFIRM, True, HARLOWE, AMON)
check("RETURN TO MAIN MENU closes the window when the change is asked",
      poll("switch_leave") == panel_switch.LEAVE == "leave" and fake.calls == [("leave",)])
fake.leaves = False
check("RETURN TO MAIN MENU refused keeps the window and paints the page again",
      poll("switch_leave") is True and fake.calls == [("leave",)] and painted())
fake.follows = True
check("nothing clicked, the game followed and the page painted again", poll() is False and painted()
      and fake.calls == [("follow",)])
fake.follows = False
check("nothing at all, nothing painted", poll() is False and not painted())
check("a card of the APPEARANCE page never read by the HUNTER page",
      poll("hunter:Paladin") is False and fake.calls == [("follow",)] and widgets["hunter:Paladin"].checked)
widgets["hunter:Paladin"].checked = False
check("the Documents folder never asked", not asked_documents)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
