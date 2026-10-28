"""The update notes in It Follows' window as built and polled (panel_updates.py, decision 117): a player updating, who
saw the welcome and never kept a version, sees the notes at the opening, the newest first, « 1 / 2 », NEXT and CLOSE,
the version installed remembered at once; while they show, START is not read; NEXT turns the page, the last without
NEXT; CLOSE closes them, never the window; reopened, nothing; CLOSE on the first page, Escape and a click beside close
them too; a new player sees the welcome and never the notes; a welcome due goes first, the notes at the next opening;
the notes in French, in English where a note has no French."""

import sys

import sdk_stubs

state = sdk_stubs.install()

import panel_fixture  # noqa: E402

panel_fixture.install()

import it_follows  # noqa: E402
from it_follows import panel_assets, panel_fonts, panel_form, panel_model, panel_view  # noqa: E402
from it_follows import release_notes, session, updates, welcome  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


panel_assets.texture = lambda _world, name=panel_assets.AVATAR: object()
panel_fonts.build = lambda _root: {"title": object(), "body": object()}
model = panel_model.Model(it_follows.mod)
release_notes.NOTES = (
    ("1.0.1", {"en": ("Shields for the enemies.", "Better aim."), "fr": ("Des boucliers.", "Une meilleure visée.")}),
    ("1.0.0", {"en": ("The first version.",)}),
)


def window():
    global widgets, form
    _root, made = panel_view.build_view(object(), model)
    widgets = made
    form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in made.items()}, model)


def press(name: str):
    widgets[name].SetIsChecked(True)
    return form.poll()


def text(name: str) -> str:
    return panel_fixture.text(widgets, name)


def shown(name: str) -> bool:
    return panel_fixture.visible(widgets, name)


def updating() -> None:
    """A player who saw the welcome and never kept a version: one coming from 1.0.0 or 1.0.1."""
    welcome.seen.value, updates.seen.value = welcome.EDITION, ""


started: list = []
session.start = lambda settings: started.append(settings) or "started"
widgets: dict = {}
form = None

try:
    updating()
    window()
    check("a player updating: the notes at the opening, the newest first, its place, its points, NEXT",
          form.popup == "updates" and shown("popup:updates") and text("heading:popup_updates") == "UPDATE 1.0.1"
          and text("group:popup_updates") == "1 / 2"
          and text("updates_points") == "• Shields for the enemies.\n\n• Better aim."
          and shown("updates_next_box") and text("updates_next_label") == "NEXT"
          and text("popup:updates:close_label") == "CLOSE")
    check("the version installed remembered as soon as they show", updates.seen.value == it_follows.__version__)
    check("while they show, START is not read", press("run_start") is False and not started
          and form.popup == "updates")
    check("NEXT turns to the older note, the last page without NEXT",
          press("updates_next") is False and form.popup == "updates" and text("heading:popup_updates") == "UPDATE 1.0.0"
          and text("group:popup_updates") == "2 / 2" and text("updates_points") == "• The first version."
          and not shown("updates_next_box"))
    check("NEXT on the last page does nothing", press("updates_next") is False and form.update_page == 1)
    check("CLOSE closes them, never the window", press("popup:updates:close") is False and form.popup is None
          and not shown("popup:updates"))
    window()
    check("reopened: nothing", form.popup is None)

    updating()
    window()
    check("CLOSE on the first page closes them at once", press("popup:updates:close") is False
          and form.popup is None and updates.seen.value == it_follows.__version__)
    updating()
    window()
    check("Escape closes them alone", form.escape() is False and form.popup is None)
    updating()
    window()
    check("a click beside closes them alone", press("popup:updates:beside") is False and form.popup is None)

    welcome.seen.value, updates.seen.value = 0, ""
    window()
    check("a new player: the welcome, the version installed remembered with it",
          form.popup == "welcome" and updates.seen.value == it_follows.__version__)
    press("welcome_next")
    press("welcome_go")
    window()
    check("then never the notes", form.popup is None)

    welcome.seen.value, updates.seen.value = 1, ""
    window()
    check("a welcome due goes first, the notes kept for later", form.popup == "welcome" and updates.seen.value == "")
    press("welcome_next")
    press("welcome_go")
    window()
    check("the notes at the next opening", form.popup == "updates")
    form.escape()

    updating()
    model.change_language("FR")
    window()
    check("in French: the title, NEXT, the points",
          text("heading:popup_updates") == "MISE À JOUR 1.0.1" and text("updates_next_label") == "SUIVANT"
          and text("updates_points") == "• Des boucliers.\n\n• Une meilleure visée."
          and text("popup:updates:close_label") == "FERMER")
    press("updates_next")
    check("a note without French in English", text("updates_points") == "• The first version.")
except Exception as error:
    check(f"exception {type(error).__name__}: {error}", False)
    import traceback
    traceback.print_exc()

print(f"RESULTAT: {'ECHEC' if fails else 'OK'} ({len(fails)} echec(s))")
sys.exit(1 if fails else 0)
