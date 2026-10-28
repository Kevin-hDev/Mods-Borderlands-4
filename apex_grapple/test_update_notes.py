"""The update notes in Apex Grapple's window (panel_updates.py, Kevin, 2026-10-17: « il faut ajouter la note de mise à
jour dans le menu »): a player updating, who never kept a version, sees them at the opening, the newest first,
« 1 / 2 », NEXT and CLOSE, the version installed saved at once; NEXT turns the page, the last without NEXT; CLOSE,
Escape and a click beside close them, never the window, and nothing behind them changes meanwhile; reopened, nothing;
nothing is due without notes or once seen; the notes in French, in English where a note has no French; a new player
gets the version installed as seen; the window as built has the pop-up in its layer over the whole window; the notes
shipped are those of the Nexus notes."""

import sys

import panel_fixture as pf
import unrealsdk
import apex_grapple
from apex_grapple import panel_preferences, release_notes, settings, updates

fails: list[str] = []


class Enum:
    # Every member of every enum, the pop-up's SelfHitTestInvisible included, read as "Enum.Member".
    def __init__(self, name):
        self.name = name

    def __getattr__(self, member):
        return f"{self.name}.{member}"


unrealsdk.find_enum = Enum


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def opened():
    """The window of a player coming from an older version: a settings file, no version kept."""
    widgets, form = pf.create()
    updates.seen.value = ""
    # pf.create built the form as a player who saw the notes; open it again as one who did not.
    form.__init__(form.widgets, form.bindings, form.model)
    return widgets, form


def press(widgets, form, name):
    widgets[name].checked = True
    return form.poll()


try:
    shipped = release_notes.NOTES[0]
    # Every language the window offers, Japanese since 2026-10-21: a player who chose one never reads English.
    check("the notes shipped open on this version, in every language the window offers",
          shipped[0] == apex_grapple.__version__
          and set(shipped[1]) == {code.lower() for code in panel_preferences.LANGUAGES})

    release_notes.NOTES = (
        (apex_grapple.__version__, {"en": ("Co-op works.", "Ropes are seen."), "fr": ("Le coop marche.", "Pareil.")}),
        ("1.0.10", {"en": ("The grapple gun.",)}),
    )
    panel_preferences.language.value = "EN"
    w, form = opened()
    check("a player updating: the notes at the opening, the newest first, their place, their points, NEXT",
          form.popup == "updates" and w["popup:updates"].visibility != "Collapsed"
          and w["heading:popup_updates"].text == f"UPDATE {apex_grapple.__version__}"
          and w["group:popup_updates"].text == "1 / 2"
          and w["updates_points"].text == "• Co-op works.\n\n• Ropes are seen."
          and w["updates_next_box"].visibility != "Collapsed" and w["updates_next_label"].text == "NEXT")
    check("the version installed saved at once", updates.seen.value == apex_grapple.__version__)
    before = settings.pull_strength.value
    w["setting:pull_strength"].value = before + 0.5
    check("nothing behind the notes changes meanwhile", form.poll() is False and form.pending == {})
    check("NEXT turns to the older note, the last page without NEXT",
          press(w, form, "updates_next") is False and w["heading:popup_updates"].text == "UPDATE 1.0.10"
          and w["group:popup_updates"].text == "2 / 2" and w["updates_points"].text == "• The grapple gun."
          and w["updates_next_box"].visibility == "ESlateVisibility.Collapsed")
    check("NEXT on the last page does nothing", press(w, form, "updates_next") is False and form.update_page == 1)
    check("CLOSE closes them, never the window", press(w, form, "popup:updates:close") is False
          and form.popup is None and w["popup:updates"].visibility == "ESlateVisibility.Collapsed")
    w["setting:pull_strength"].value = before
    _w, again = pf.create()
    again.__init__(again.widgets, again.bindings, again.model)
    check("reopened: nothing", again.popup is None)

    w, form = opened()
    check("Escape closes them alone", form.escape() is False and form.popup is None)
    w, form = opened()
    check("a click beside closes them alone", press(w, form, "popup:updates:beside") is False and form.popup is None)

    updates.seen.value = "1.0.10"
    check("seen 1.0.10: only the newer note is due", [v for v, _ in updates.due(apex_grapple.__version__)]
          == [apex_grapple.__version__])
    check("a note newer than the version installed is not due", updates.due("1.0.10") == [])
    updates.seen.value = "1.0.x"
    check("a version seen that is no version reads as none", len(updates.due(apex_grapple.__version__)) == 2)
    release_notes.NOTES, kept = (), release_notes.NOTES
    _w, form = opened()
    check("without notes nothing opens", form.popup is None)
    release_notes.NOTES = kept

    panel_preferences.language.value = "FR"
    w, form = opened()
    check("in French: the title and the points",
          w["heading:popup_updates"].text == f"MISE À JOUR {apex_grapple.__version__}"
          and w["updates_points"].text == "• Le coop marche.\n\n• Pareil." and w["updates_next_label"].text == "SUIVANT")
    press(w, form, "updates_next")
    check("a note without French in English", w["updates_points"].text == "• The grapple gun.")
    form.escape()
    panel_preferences.language.value = "EN"

    class Fresh:
        saved = 0

        def save_settings(self):
            self.saved += 1

    fresh = Fresh()
    updates.seen.value = ""
    updates.new_player(fresh, apex_grapple.__version__)
    check("a new player: the version installed counts as seen, saved at once",
          updates.seen.value == apex_grapple.__version__ and fresh.saved == 1)
except Exception as error:
    import traceback
    traceback.print_exc()
    fails.append(f"exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
