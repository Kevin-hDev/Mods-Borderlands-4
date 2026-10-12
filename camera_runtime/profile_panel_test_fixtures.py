"""The camera profile window on each camera mod's actual generated window (decisions of 2026-10-12): the floppy hides
the menu and its blur and opens the window alone in the screen's corner on a new profile, every change reaches the
shared draft at once, the key rows refuse what cannot switch a profile, CANCEL puts the camera back, SAVE keeps and
switches on, both bring the menu back, and the menu opens on the window again while its draft waits. At the UMG
boundary, not in-game rendering."""

import pathlib
import tempfile
from types import SimpleNamespace as NS
from unittest.mock import patch

import ads_panel_test_fixtures
from ads_panel_test_fixtures import AdsPanelTests
from apex_camera_runtime import profile_store
from apex_camera_runtime.camera_distance import CLOSE, NORMAL
from apex_camera_runtime.profile_store import Store
from apex_camera_runtime.profile_values import DEFAULTS
from apex_camera_runtime.profiles import Profiles

SHOWN = "ESlateVisibility.SelfHitTestInvisible"
HIDDEN = "ESlateVisibility.Collapsed"


class Widget(ads_panel_test_fixtures.Widget):
    """A text box gives back its text, a key selector its chosen key and a panel its children, as UMG's do; focused
    tells whether the keyboard is in a widget's descendants."""
    focused = False

    def call(self, name, args):
        if name == "SetSelectedKey":
            self.SelectedKey = args[0]
        return super().call(name, args)

    def GetText(self):
        return self.calls.get("SetText", ("",))[0]

    def GetChildAt(self, index):
        return self.children[index]

    def HasFocusedDescendants(self):
        return self.focused


class Keys:
    def pressed(self, _pc, _profiles):
        return None

    def pause(self):
        pass


class ProfilePanelTests:
    """The aiming window tests' set-up and build, without running their tests a second time."""

    def setUp(self):
        AdsPanelTests.setUp(self)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = pathlib.Path(folder.name) / profile_store.FILE_NAME
        self.profiles = self.shared = Profiles(Store(lambda: self.path), Keys())
        camera = self.package.camera
        # The menu reaches the profiles through these two (camera.py); they are checked on their own below.
        self.camera_reads = camera.profiles, camera.shown_fov
        for name, value in (("profiles", lambda: self.shared), ("shown_fov", lambda: 104.4)):
            patcher = patch.object(camera, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def build(self):
        with patch.object(ads_panel_test_fixtures, "Widget", Widget):
            return AdsPanelTests.build(self)

    def opened(self):
        widgets, form = self.build()
        widgets["profile:floppy"].SetIsChecked(True)
        form.poll()
        return widgets, form

    @staticmethod
    def visible(widget):
        return widget.calls["SetVisibility"][0] in ("ESlateVisibility.Visible", SHOWN)

    def test_the_camera_gives_its_profiles_only_while_its_camera_is_shown(self):
        camera, (profiles, shown_fov) = self.package.camera, self.camera_reads
        # Third Person & FOV's tests start its camera for real; unregistered, it gives nothing.
        with patch.object(camera, "_registered", False):
            self.assertEqual((profiles(), shown_fov()), (None, None))
        for runtime, elsewhere, expected in ((NS(profiles=self.profiles, fov=NS(seen=104.4)), False, self.profiles),
                                             (NS(profiles=self.profiles, fov=NS(seen=104.4)), True, None),
                                             # A runtime from an older mod's copy has no profiles.
                                             (NS(), False, None)):
            with (patch.object(camera, "_registered", True), patch.object(camera, "_runtime", runtime),
                  patch.object(camera, "elected_elsewhere", lambda elsewhere=elsewhere: elsewhere)):
                self.assertIs(profiles(), expected)
                self.assertEqual(shown_fov(), None if runtime == NS() else 104.4)

    def test_the_floppy_shows_only_where_a_profile_can_be_kept(self):
        widgets, form = self.build()
        form.poll()
        self.assertTrue(self.visible(widgets["profile:floppy_body"]))
        self.assertFalse(self.visible(widgets["profile:window"]))
        with patch.object(self.package.camera, "elected_elsewhere", lambda: True):
            form.poll()
            self.assertFalse(self.visible(widgets["profile:floppy_body"]))
        self.shared = None
        form.poll()
        self.assertFalse(self.visible(widgets["profile:floppy_body"]))
        self.path.write_bytes(b"{}")
        with patch.object(pathlib.Path, "read_bytes", side_effect=PermissionError("locked")):
            self.shared = Profiles(Store(lambda: self.path), Keys())
            form.poll()
            self.assertFalse(self.visible(widgets["profile:floppy_body"]))
        self.shared = self.profiles
        form.poll()
        self.assertTrue(self.visible(widgets["profile:floppy_body"]))

    def test_the_floppy_opens_a_new_profile_from_what_the_camera_shows(self):
        widgets, form = self.opened()
        draft = self.profiles.draft
        self.assertEqual((draft.name, draft.values.fov, draft.editing), ("Profile 1", 104, None))
        self.assertTrue(self.visible(widgets["profile:window"]))
        self.assertEqual(widgets["label:profile:close"].calls["SetText"], ("DISTANCE: CLOSE",))
        self.assertEqual(widgets["profile:name"].GetText(), "Profile 1")
        self.assertEqual(widgets["setting:profile:fov"].GetValue(), 104.0)
        self.assertEqual(widgets["heading:profile_window"].calls["SetText"], ("NEW PROFILE",))
        self.assertEqual(widgets["profile:save_label"].calls["SetText"], ("SAVE",))
        self.assertEqual(widgets["value:profile:fov"].calls["SetText"], ("104",))

    def test_a_page_change_still_waiting_is_saved_before_the_window_opens(self):
        widgets, form = self.build()
        widgets["setting:camera_distance_far"].SetValue(4.2)
        form.poll()
        self.assertEqual(form.pending, {"camera_distance_far": 4.2})
        widgets["profile:floppy"].SetIsChecked(True)
        form.poll()
        self.assertEqual(form.pending, {})
        self.assertEqual(form.model.options["camera_distance_far"].value, 4.2)
        # The window starts from what the page has just saved.
        self.assertEqual(self.profiles.draft.values.far, 4.2)

    def test_every_change_reaches_the_camera_at_once(self):
        widgets, form = self.opened()
        widgets["setting:profile:fov"].SetValue(121.4)
        widgets["setting:profile:close"].SetValue(1.237)
        widgets["profile:spacing:preset:0"].SetIsChecked(True)
        form.poll()
        shown = self.profiles.shown()
        self.assertEqual((shown.fov, shown.close, shown.spacing), (121, 1.24, -40))
        self.assertEqual(self.profiles.distance(NORMAL), CLOSE)
        self.assertEqual(widgets["setting:profile:spacing"].GetValue(), -40.0)
        self.assertEqual(widgets["value:profile:spacing"].calls["SetText"], ("-40%",))
        # The preset lit, the others not.
        self.assertNotEqual(widgets["profile:spacing:preset:0_fill"].calls["SetBrushColor"],
                            widgets["profile:spacing:preset:1_fill"].calls["SetBrushColor"])
        widgets["setting:profile:height"].SetValue(25)
        form.poll()
        self.assertEqual(widgets["value:profile:height"].calls["SetText"], ("+25%",))

    def test_the_window_shows_alone_in_the_corner_over_the_game(self):
        widgets, form = self.build()
        corner, menu, backdrop = (widgets[name] for name in ("profile:window", "profile:menu", "profile:backdrop"))
        # On the screen's layer beside the menu, over the blur panel_modal lays first.
        self.assertEqual((corner.owner.kind, backdrop.kind), ("CanvasPanel", "BackgroundBlur"))
        self.assertIs(backdrop, corner.owner.children[0])
        self.assertIn(corner, corner.owner.children)
        widgets["profile:floppy"].SetIsChecked(True)
        form.poll()
        self.assertEqual(menu.calls["SetVisibility"], (HIDDEN,))
        self.assertEqual(backdrop.calls["SetBlurStrength"], (0.0,))
        self.assertEqual(corner.calls["SetVisibility"], (SHOWN,))
        self.assertIn("SetKeyboardFocus", widgets["profile:name"].calls)
        # The keyboard already in the window stays where it is.
        del widgets["profile:name"].calls["SetKeyboardFocus"]
        corner.focused = True
        form.poll()
        self.assertNotIn("SetKeyboardFocus", widgets["profile:name"].calls)
        widgets["profile:cancel"].SetIsChecked(True)
        form.poll()
        self.assertEqual(menu.calls["SetVisibility"], ("ESlateVisibility.Visible",))
        self.assertEqual(backdrop.calls["SetBlurStrength"], (6.0,))
        self.assertEqual(corner.calls["SetVisibility"], (HIDDEN,))
        self.assertIn("SetKeyboardFocus", widgets["focus"].calls)

    def test_only_cancel_and_save_close_the_window(self):
        widgets, form = self.opened()
        for name in ("profile:floppy", "close"):
            widgets[name].SetIsChecked(True)
            self.assertFalse(form.poll())
            self.assertIsNotNone(self.profiles.draft)
            self.assertTrue(self.visible(widgets["profile:window"]))
        widgets["close"].SetIsChecked(False)
        widgets["profile:cancel"].SetIsChecked(True)
        form.poll()
        self.assertIsNone(self.profiles.draft)
        self.assertIsNone(self.profiles.shown())
        self.assertFalse(self.visible(widgets["profile:window"]))

    def test_escape_closes_the_menu_and_the_window_waits_for_its_reopening(self):
        widgets, form = self.opened()
        widgets["profile:name"].SetText("Combat")
        widgets["setting:profile:far"].SetValue(4.5)
        form.poll()
        self.assertTrue(form.escape())
        widgets, form = self.build()
        # Shown as the menu is made, before its first turn: the menu never shows in between.
        self.assertTrue(self.visible(widgets["profile:window"]))
        self.assertEqual(widgets["profile:menu"].calls["SetVisibility"], (HIDDEN,))
        form.poll()
        self.assertEqual(widgets["profile:name"].GetText(), "Combat")
        self.assertEqual(widgets["setting:profile:far"].GetValue(), 4.5)

    def test_the_name_is_bounded_and_checked_at_save(self):
        widgets, form = self.opened()
        widgets["profile:name"].SetText("x" * 30)
        form.poll()
        self.assertEqual(self.profiles.draft.name, "x" * 24)
        self.assertEqual(widgets["profile:name"].GetText(), "x" * 24)
        widgets["profile:name"].SetText("  ")
        widgets["profile:save"].SetIsChecked(True)
        form.poll()
        self.assertIsNotNone(self.profiles.draft)
        self.assertIn("Name refused", widgets["profile:status"].calls["SetText"][0])

    def test_the_key_rows_refuse_what_cannot_switch_a_profile(self):
        self.profiles.ready().put(None, "Sniper", DEFAULTS, "F6")
        widgets, form = self.opened()
        selector = widgets["command:profile:keyboard"]
        for key, status in (("F5", None), ("P", "camera command"), ("F6", "Another profile"), ("Escape", None)):
            selector.SelectedKey = NS(Key=NS(KeyName=key))
            form.poll()
            self.assertEqual(self.profiles.draft.keyboard, "F5")
            self.assertEqual(selector.SelectedKey.Key.KeyName, "None")
            if status is not None:
                self.assertIn(status, widgets["profile:status"].calls["SetText"][0])
        self.assertEqual(widgets["value:profile:keyboard"].calls["SetText"], ("F5",))
        widgets["clear:profile:keyboard"].SetIsChecked(True)
        form.poll()
        self.assertIsNone(self.profiles.draft.keyboard)
        widgets["command:profile:controller"].selecting = True
        self.assertTrue(form.selecting())
        form.poll()
        self.assertEqual(selector.calls["SetIsEnabled"], (False,))

    def test_save_keeps_the_profile_and_switches_it_on(self):
        widgets, form = self.opened()
        widgets["profile:name"].SetText("Combat")
        widgets["setting:profile:height"].SetValue(25)
        form.poll()
        widgets["profile:save"].SetIsChecked(True)
        form.poll()
        self.assertIsNone(self.profiles.draft)
        store = self.profiles.ready()
        self.assertEqual([(profile.name, profile.values.height) for profile in store.profiles], [("Combat", 25)])
        self.assertEqual(store.active, store.profiles[0].ident)
        self.assertFalse(self.visible(widgets["profile:window"]))
        widgets["profile:floppy"].SetIsChecked(True)
        form.poll()
        self.assertEqual(self.profiles.draft.name, "Profile 1")

    def test_a_failed_write_keeps_the_window_and_says_so(self):
        widgets, form = self.opened()
        with patch.object(pathlib.Path, "write_bytes", side_effect=PermissionError("locked")):
            widgets["profile:save"].SetIsChecked(True)
            form.poll()
        self.assertIsNotNone(self.profiles.draft)
        self.assertIn("could not be written", widgets["profile:status"].calls["SetText"][0])

    def test_the_window_speaks_french(self):
        self.package.panel_preferences.french.value = True
        widgets, _form = self.opened()
        self.assertEqual(self.profiles.draft.name, "Profil 1")
        self.assertEqual(widgets["heading:profile_window"].calls["SetText"], ("NOUVEAU PROFIL",))
        self.assertEqual(widgets["profile:cancel_label"].calls["SetText"], ("ANNULER",))
        self.assertEqual(widgets["label:profile:far"].calls["SetText"], ("DISTANCE : LOIN",))
        self.assertEqual(widgets["profile:spacing:preset:0_label"].calls["SetText"], ("Serrer",))

    def test_with_ten_profiles_the_floppy_says_so_rather_than_open_a_window_it_could_not_save(self):
        store = self.profiles.ready()
        for number in range(profile_store.MAX_PROFILES):
            store.put(None, f"Profile {number}", DEFAULTS)
        widgets, _form = self.opened()
        self.assertIsNone(self.profiles.draft)
        self.assertFalse(self.visible(widgets["profile:window"]))
        self.assertEqual(widgets["notice"].calls["SetText"], ("You already have 10 profiles: delete one in PROFILES.",))

    def commands(self):
        """The window on its COMMANDS page, F5 held by the profile COMBAT."""
        self.profiles.ready().put(None, "Combat", DEFAULTS, "F5")
        widgets, form = self.build()
        # The commands' keys live in the mod's options, shared by every test: they are put back after this one.
        commands = form.model.command_actions.commands
        self.addCleanup(commands.set_values, form.model.command_actions.snapshot())
        form.poll()
        widgets["tab:options:commands" if "tab:options:commands" in widgets else "nav:commands"].SetIsChecked(True)
        form.poll()
        self.assertEqual(form.model.pages[form.page], "commands")
        return widgets, form

    @staticmethod
    def command_key(form):
        """Third person's keyboard key, which every camera mod has."""
        return form.model.command_options[form.model.command_actions.commands.identifier("third_person",
                                                                                          "keyboard")].value

    def test_the_commands_page_refuses_a_key_a_profile_holds_and_names_the_profile(self):
        widgets, form = self.commands()
        before = self.command_key(form)
        selector = widgets["command:third_person:keyboard"]
        selector.SelectedKey = NS(Key=NS(KeyName="F5"))
        form.poll()
        self.assertEqual(self.command_key(form), before)
        self.assertEqual(widgets["commands_status"].calls["SetText"],
                         ("The profile “COMBAT” already has this key: choose another one, or change the profile's key "
                          "in PROFILES.",))
        selector.SelectedKey = NS(Key=NS(KeyName="F7"))
        form.poll()
        self.assertEqual(self.command_key(form), "F7")

    def test_neither_reset_nor_undo_gives_a_command_back_a_key_a_profile_took(self):
        widgets, form = self.commands()
        default = self.command_key(form)
        widgets["command:third_person:keyboard"].SelectedKey = NS(Key=NS(KeyName="F7"))
        form.poll()
        store = self.profiles.ready()
        sniper = store.put(None, "Sniper", DEFAULTS, default)
        back = "A camera profile has a key a command would take back: change the profile's key in PROFILES first."
        widgets["commands_reset"].SetIsChecked(True)
        form.poll()
        self.assertEqual((self.command_key(form), widgets["commands_status"].calls["SetText"]), ("F7", (back,)))
        widgets["restore"].SetIsChecked(True)
        form.poll()
        self.assertEqual((self.command_key(form), widgets["notice"].calls["SetText"]), ("F7", (back,)))
        store.delete(sniper.ident)
        widgets["restore"].SetIsChecked(True)
        form.poll()
        self.assertEqual(self.command_key(form), default)
        store.put(None, "Sniper", DEFAULTS, "F7")
        widgets["undo"].SetIsChecked(True)
        form.poll()
        self.assertEqual((self.command_key(form), widgets["notice"].calls["SetText"]), (default, (back,)))
