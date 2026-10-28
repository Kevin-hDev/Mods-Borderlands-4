"""The PROFILES page on each camera mod's actual generated window (decisions of 2026-10-12, mockup profils/3_page.png
to 5_allume.png): the page and its button show only while a profile is saved, each row switches, edits or deletes its
profile, DELETE asks first, the menu leaves the page when its last profile goes, and a profile switched on greys its
five settings on CAMERA VIEW and SHOULDER VIEW with its name. At the UMG boundary, not in-game rendering."""

import pathlib
from unittest.mock import patch

from apex_camera_runtime.profile_values import make
from profile_panel_test_fixtures import HIDDEN, ProfilePanelTests

COMBAT = make(fov=100, close=1.4, far=3.2, spacing=-40, height=25)
EXPLORATION = make(fov=120, close=1.8, far=4.5, spacing=10, height=0)


class ProfilePageTests:
    """The profile window tests' set-up and build, without running their tests a second time."""

    def setUp(self):
        ProfilePanelTests.setUp(self)

    def build(self):
        return ProfilePanelTests.build(self)

    visible = staticmethod(ProfilePanelTests.visible)

    def saved(self):
        """COMBAT, switched on with F5; EXPLORATION, off and without keys."""
        store = self.profiles.ready()
        combat = store.put(None, "Combat", COMBAT, "F5", None, activate=True)
        exploration = store.put(None, "Exploration", EXPLORATION)
        return combat, exploration

    @staticmethod
    def click(widgets, form, name):
        widgets[name].SetIsChecked(True)
        form.poll()

    @staticmethod
    def shown(widget):
        return widget.calls["SetVisibility"][0] != HIDDEN

    @staticmethod
    def page(form):
        return "options" if getattr(form, "options_open", False) else form.model.pages[form.page]

    def opened_page(self):
        """The window on the PROFILES page, opened from its tab or sidebar button."""
        widgets, form = self.build()
        form.poll()
        self.click(widgets, form, "tab:options:profiles" if "tab:options:profiles" in widgets else "nav:profiles")
        self.assertEqual(self.page(form), "profiles")
        return widgets, form

    def test_the_page_and_its_button_show_only_while_a_profile_is_saved(self):
        widgets, form = self.build()
        buttons = form.profile_form.page.buttons
        # Apex Movement's tab on each of its nine Options heads, the other camera mods' sidebar button.
        self.assertIn(len(buttons), (1, 9))
        form.poll()
        self.assertFalse(any(self.shown(widgets[name]) for name in buttons))
        self.saved()
        form.poll()
        self.assertTrue(all(self.shown(widgets[name]) for name in buttons))
        with patch.object(self.package.camera, "elected_elsewhere", lambda: True):
            form.poll()
            self.assertFalse(any(self.shown(widgets[name]) for name in buttons))

    def test_the_menu_opens_with_its_page_drawn(self):
        self.saved()
        widgets, form = self.build()
        # Before the menu's first turn: the button does not show a turn late.
        self.assertTrue(all(self.shown(widgets[name]) for name in form.profile_form.page.buttons))
        self.assertEqual(widgets["profiles:0:name"].calls["SetText"], ("COMBAT",))

    def test_edit_saves_first_what_the_page_had_pending(self):
        combat, _exploration = self.saved()
        self.profiles.toggle(combat.ident)
        widgets, form = self.build()
        widgets["setting:camera_distance_far"].SetValue(4.2)
        form.poll()
        self.assertEqual(form.pending, {"camera_distance_far": 4.2})
        self.click(widgets, form, "profiles:0:edit")
        self.assertEqual(form.pending, {})
        self.assertEqual(form.model.options["camera_distance_far"].value, 4.2)
        self.assertEqual(self.profiles.draft.editing, combat.ident)

    def test_each_row_shows_its_profile(self):
        self.saved()
        widgets, _form = self.opened_page()
        self.assertEqual([self.shown(widgets[f"profiles:{index}"]) for index in range(3)], [True, True, False])
        self.assertEqual(widgets["heading:profiles"].calls["SetText"], ("PROFILES",))
        self.assertEqual(widgets["profiles:0:name"].calls["SetText"], ("COMBAT",))
        self.assertEqual(widgets["profiles:0:switch_label"].calls["SetText"], ("ON",))
        self.assertEqual(widgets["profiles:1:switch_label"].calls["SetText"], ("OFF",))
        self.assertEqual(widgets["value:profiles:0:keyboard"].calls["SetText"], ("F5",))
        self.assertEqual(widgets["value:profiles:1:keyboard"].calls["SetText"], ("NONE",))
        self.assertEqual(widgets["profiles:0:values"].calls["SetText"],
                         ("FOV 100 · close 1.40 m · far 3.20 m · spacing -40% · height +25%. Controller: none.",))

    def test_the_page_speaks_french(self):
        self.package.panel_preferences.french.value = True
        self.saved()
        widgets, _form = self.opened_page()
        self.assertEqual(widgets["heading:profiles"].calls["SetText"], ("PROFILS",))
        self.assertEqual(widgets["profiles:0:switch_label"].calls["SetText"], ("ALLUMÉ",))
        self.assertEqual(widgets["profiles:1:edit_label"].calls["SetText"], ("MODIFIER",))
        self.assertEqual(widgets["profiles:1:values"].calls["SetText"],
                         ("FOV 120 · proche 1,80 m · loin 4,50 m · écart +10 % · hauteur +0 %. Manette : aucune.",))

    def test_the_switch_switches_a_profile_on_and_back(self):
        combat, exploration = self.saved()
        widgets, form = self.opened_page()
        self.click(widgets, form, "profiles:1:switch")
        self.assertEqual(self.profiles.ready().active, exploration.ident)
        self.assertEqual(widgets["profiles:0:switch_label"].calls["SetText"], ("OFF",))
        self.assertEqual(widgets["profiles:1:switch_label"].calls["SetText"], ("ON",))
        self.click(widgets, form, "profiles:1:switch")
        self.assertIsNone(self.profiles.ready().active)
        self.assertEqual(self.profiles.shown(), None)

    def test_a_switch_the_file_refuses_changes_nothing_and_says_so(self):
        combat, _exploration = self.saved()
        widgets, form = self.opened_page()
        with patch.object(pathlib.Path, "write_bytes", side_effect=PermissionError("locked")):
            self.click(widgets, form, "profiles:1:switch")
        self.assertEqual(self.profiles.ready().active, combat.ident)
        self.assertEqual(widgets["profiles:status"].calls["SetText"],
                         ("The profiles' file could not be written: nothing changed.",))
        self.click(widgets, form, "profiles:1:switch")
        self.assertEqual(widgets["profiles:status"].calls["SetText"], ("",))

    def test_edit_opens_the_window_on_the_profile(self):
        combat, _exploration = self.saved()
        widgets, form = self.opened_page()
        self.click(widgets, form, "profiles:0:edit")
        draft = self.profiles.draft
        self.assertEqual((draft.editing, draft.name, draft.values, draft.keyboard),
                         (combat.ident, "Combat", COMBAT, "F5"))
        self.assertTrue(self.visible(widgets["profile:window"]))
        self.assertEqual(widgets["heading:profile_window"].calls["SetText"], ("EDIT PROFILE",))
        self.assertEqual(widgets["profile:name"].GetText(), "Combat")
        widgets["setting:profile:fov"].SetValue(90)
        form.poll()
        self.click(widgets, form, "profile:save")
        store = self.profiles.ready()
        self.assertEqual([(profile.name, profile.values.fov) for profile in store.profiles],
                         [("Combat", 90), ("Exploration", 120)])
        self.assertEqual(store.active, combat.ident)
        # The page is drawn again at the menu's next turn, the window's last one being SAVE's.
        form.poll()
        self.assertEqual(widgets["profiles:0:values"].calls["SetText"][0][:7], "FOV 90 ")

    def test_delete_asks_first_then_deletes(self):
        combat, exploration = self.saved()
        widgets, form = self.opened_page()
        self.click(widgets, form, "profiles:0:delete")
        self.assertTrue(self.shown(widgets["popup:profile_delete"]))
        self.assertEqual(widgets["heading:popup_profile_delete"].calls["SetText"], ("DELETE THE PROFILE",))
        text = widgets["profile_delete:text"].calls["SetText"][0]
        self.assertIn("“COMBAT” and its key", text)
        self.assertIn("It is on", text)
        # The pop-up's own CLOSE gives way to CANCEL and DELETE.
        self.assertFalse(self.shown(widgets["popup:profile_delete:close_frame"]))
        self.click(widgets, form, "profile_delete:cancel")
        self.assertFalse(self.shown(widgets["popup:profile_delete"]))
        self.assertEqual(len(self.profiles.ready().profiles), 2)
        self.click(widgets, form, "profiles:1:delete")
        self.assertIn("“EXPLORATION” will be deleted", widgets["profile_delete:text"].calls["SetText"][0])
        self.assertNotIn("It is on", widgets["profile_delete:text"].calls["SetText"][0])
        self.click(widgets, form, "profile_delete:confirm")
        store = self.profiles.ready()
        self.assertEqual(([profile.name for profile in store.profiles], store.active), (["Combat"], combat.ident))
        self.assertFalse(self.shown(widgets["popup:profile_delete"]))
        self.assertFalse(self.shown(widgets["profiles:1"]))

    def test_a_click_beside_or_escape_closes_the_question_without_deleting(self):
        self.saved()
        widgets, form = self.opened_page()
        self.click(widgets, form, "profiles:0:delete")
        self.click(widgets, form, "popup:profile_delete:beside")
        self.assertFalse(self.shown(widgets["popup:profile_delete"]))
        self.click(widgets, form, "profiles:0:delete")
        self.assertFalse(form.escape())
        self.assertFalse(self.shown(widgets["popup:profile_delete"]))
        self.assertEqual(len(self.profiles.ready().profiles), 2)

    def test_the_menu_leaves_the_page_when_its_last_profile_goes(self):
        camera = "options" if "tab:options:profiles" in self.build()[0] else "camera"
        self.saved()
        widgets, form = self.opened_page()
        for index in (1, 0):
            self.click(widgets, form, f"profiles:{index}:delete")
            self.click(widgets, form, "profile_delete:confirm")
        self.assertEqual(self.profiles.ready().profiles, ())
        self.assertEqual(self.page(form), camera)
        self.assertEqual(form.model.page, camera)
        # Closed on the page, the menu opens on the camera's while no profile is left.
        self.saved()
        self.opened_page()
        store = self.profiles.ready()
        for profile in store.profiles:
            store.delete(profile.ident)
        _widgets, form = self.build()
        form.poll()
        self.assertEqual(self.page(form), camera)

    def test_a_profile_switched_on_greys_its_five_settings_and_names_itself(self):
        combat, _exploration = self.saved()
        widgets, form = self.build()
        form.poll()
        framing = {field: option.identifier for field, (option, group) in
                   self.package.panel_profile_window.sources(form.model).items() if group is not None}
        held = ("fov", "camera_distance_close", "camera_distance_far", *framing.values())
        self.assertTrue(all(widgets[f"setting:{key}"].calls["SetIsEnabled"] == (False,) for key in held))
        self.assertLess(widgets["row:camera_distance_far"].calls["SetRenderOpacity"][0], 1)
        self.assertEqual(widgets["profile_notice:camera"].calls["SetText"],
                         ("FOV and distances set by the profile “COMBAT”. Switch it off in PROFILES or with its key.",))
        self.assertTrue(self.shown(widgets["profile_notice:camera"]))
        self.assertTrue(self.shown(widgets["profile_notice:framing:height"]))
        self.assertFalse(self.shown(widgets["profile_notice:framing:zoom"]))
        self.profiles.toggle(combat.ident)
        form.poll()
        # Each row as a menu opened without a profile shows it: Apex Movement greys its FOV while Custom FOV is off.
        fresh, fresh_form = self.build()
        fresh_form.poll()
        self.assertEqual([key for key in held if widgets[f"setting:{key}"].calls.get("SetIsEnabled", (True,))
                          != fresh[f"setting:{key}"].calls.get("SetIsEnabled", (True,))], [])
        self.assertFalse(self.shown(widgets["profile_notice:camera"]))

    def test_every_row_a_profile_greys_is_one_the_menu_sets_again_each_turn(self):
        """The greying only switches rows off (panel_profile_grey.rows); the menu's own greying switches them back
        (panel_form.DEPENDS_ON), so a row it does not list would stay grey once the profile goes off."""
        _widgets, form = self.build()
        held = [key for key in self.package.panel_profile_window.OPTIONS.values() if key in form.model.options]
        self.assertEqual(len(held), 3)
        self.assertEqual([key for key in held if key not in self.package.panel_form.DEPENDS_ON], [])
