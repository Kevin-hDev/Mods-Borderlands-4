"""The PROFILES page at work (decisions of 2026-10-12): a row's switch switches its profile on, or back to the pages'
settings when it is the one on; EDIT opens the profile window on it; DELETE asks first. The page and its tab or sidebar
button show only while a profile is saved (« elle n'existe qu'à partir du premier profil »): when the last one goes, the
menu goes to the camera's page.

The profile form (panel_profile_form.py) gives it a turn while its window is closed.
"""

from . import panel_buttons as b, panel_camera_commands as commands, panel_framing as framing, panel_glyphs
from . import panel_i18n as i18n, panel_popup as popup, panel_profile_page as view, panel_profile_text as words
from . import panel_widgets as w

# The button of the camera's page, clicked when this page goes away so the menu leaves it as a player would: Apex
# Movement's CAMERA VIEW tab, the other camera mods' CAMERA page.
LEAVE = ("tab:options:options", "nav:camera")


def metres(value, language):
    text = f"{value:.2f} m"
    return text.replace(".", ",") if language == "FR" else text


def values(profile, language, family):
    """The row's line under the name: the five values, then the controller key the box on the right does not show."""
    found = profile.values
    controller = (panel_glyphs.label(profile.controller, family, language) if profile.controller
                  else words.text("profile_no_key", language))
    return words.text("profile_values", language).format(
        fov=found.fov, close=metres(found.close, language), far=metres(found.far, language),
        spacing=framing.percent(found.spacing, language), height=framing.percent(found.height, language),
        controller=controller)


class ProfileList:
    def __init__(self, form, widgets):
        self.form = form
        # Apex Movement's PROFILES tab on each Options tab's head, or the other camera mods' sidebar button.
        self.buttons = tuple(name for name in widgets if name.endswith(f":{view.PAGE}_body"))
        self.leave = next((name for name in LEAVE if name in widgets), None)
        self.deleting = None
        # A refusal of the page's (panel_profile_text.py), shown until its next action.
        self.notice = None
        self.shown = False
        self.painted = None

    def poll(self, widgets, profiles):
        """Each turn while the profile window is closed: the draft EDIT opened, or None."""
        if self.form.popup == view.POPUP:
            self._confirm(widgets, profiles)
        # Read after DELETE, so the page and its rows follow it in the same turn.
        listed = () if profiles is None else profiles.ready().profiles
        self._show(widgets, bool(listed))
        if not listed:
            # Hidden with its button: nothing to click or draw.
            return None
        # A pop-up over the window takes every click (panel_popup.py).
        draft = None if self.form.popup is not None else self._rows(widgets, profiles, listed)
        if draft is None:
            self._paint(widgets, profiles, listed)
        return draft

    def _show(self, widgets, shown):
        if shown != self.shown:
            self.shown = shown
            for name in self.buttons:
                widgets[name].SetVisibility(w.enum("ESlateVisibility", "Visible" if shown else "Collapsed"))
        form = self.form
        on_page = not getattr(form, "options_open", False) and form.model.pages[form.page] == view.PAGE
        if not shown and on_page and self.leave is not None:
            # The form takes the click later in this turn, saving first what the page had pending.
            widgets[self.leave].SetIsChecked(True)

    def _rows(self, widgets, profiles, listed):
        for index, profile in enumerate(listed):
            name = f"profiles:{index}"
            if self.form.take(widgets[f"{name}:switch"]):
                self._write(lambda: profiles.toggle(profile.ident), "toggle_failed")
            elif self.form.take(widgets[f"{name}:edit"]):
                # What the page had pending is saved first, as before any change of page (panel_options_tabs.show).
                if not self.form.flush(widgets):
                    self.form.report(widgets, "failed")
                    return None
                self.notice = None
                profiles.open_edit(profile.ident)
                return profiles.draft
            elif self.form.take(widgets[f"{name}:delete"]):
                self.deleting = profile.ident
                self._ask(widgets, profile, profiles.ready().active == profile.ident)
                return None
        return None

    def _write(self, change, failure):
        """A switch or a deletion, written before the camera takes it (profile_store.py): a file that cannot be
        written leaves everything as it was, and the page says so."""
        try:
            change()
            self.notice = None
        except OSError:
            self.notice = failure

    def _ask(self, widgets, profile, on):
        language = self.form.model.language
        keys = sum(key is not None for key in (profile.keyboard, profile.controller))
        sentence = ("profile_delete_plain", "profile_delete_key", "profile_delete_keys")[keys]
        lines = [words.text(sentence, language).format(name=profile.name.upper())]
        if on:
            lines.append(words.text("profile_delete_on", language))
        lines.append(words.text("profile_delete_rest", language))
        widgets[f"heading:popup_{view.POPUP}"].SetText(words.text("profile_delete_title", language))
        widgets[f"group:popup_{view.POPUP}"].SetText("")
        widgets[f"{view.POPUP}:text"].SetText("\n\n".join(lines))
        widgets[f"{view.POPUP}:cancel_label"].SetText(words.text("profile_cancel", language))
        widgets[f"{view.POPUP}:confirm_label"].SetText(words.text("profile_delete", language))
        popup.show(self.form, widgets, view.POPUP)

    def _confirm(self, widgets, profiles):
        """CANCEL or DELETE; a click beside or Escape closes the pop-up as any other (panel_popup.py)."""
        if self.form.take(widgets[f"{view.POPUP}:cancel"]):
            popup.hide(self.form, widgets)
        elif self.form.take(widgets[f"{view.POPUP}:confirm"]):
            popup.hide(self.form, widgets)
            if profiles is not None and profiles.ready().profile(self.deleting) is not None:
                self._write(lambda: profiles.delete(self.deleting), "delete_failed")

    def _paint(self, widgets, profiles, listed):
        model = self.form.model
        active = None if profiles is None else profiles.ready().active
        state = (listed, active, self.notice, model.language, model.controller_icons)
        if state == self.painted:
            return
        self.painted = state
        language, family = model.language, model.controller_icons
        widgets[f"heading:{view.PAGE}"].SetText(i18n.text(view.PAGE, language))
        widgets[f"group:{view.PAGE}"].SetText(words.text("profiles_desc", language))
        widgets["profiles:status"].SetText(words.text(self.notice, language) if self.notice else "")
        for index in range(view.MAX_PROFILES):
            name = f"profiles:{index}"
            profile = listed[index] if index < len(listed) else None
            widgets[name].SetVisibility(w.enum("ESlateVisibility", "Collapsed" if profile is None else "Visible"))
            if profile is None:
                continue
            on = profile.ident == active
            widgets[f"{name}:name"].SetText(profile.name.upper())
            for part, key in (("switch", "profile_on" if on else "profile_off"), ("edit", "profile_modify"),
                              ("delete", "profile_delete")):
                widgets[f"{name}:{part}_label"].SetText(words.text(key, language))
            b.paint(widgets, f"{name}:switch", "on" if on else "off")
            commands._show_value(widgets, f"{name}:keyboard", profile.keyboard, family, language,
                                 self.form.command_catalogue)
            widgets[f"{name}:values"].SetText(values(profile, language, family))
