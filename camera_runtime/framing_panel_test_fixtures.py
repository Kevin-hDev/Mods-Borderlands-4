"""Exercise each shipped window's presets through its real form and SDK settings."""
from ads_panel_test_fixtures import AdsPanelTests


class FramingPanelTests(AdsPanelTests):
    def setUp(self):
        super().setUp()
        self.settings.orbit.commit(False)
        for option in self.settings.framing.options:
            option.value = option.default_value

    def test_presets_custom_reopening_restore_and_undo(self):
        widgets, form = self.build()
        self.assertIn("framing:zoom:preset:2", widgets)
        widgets["framing:zoom:preset:2"].SetIsChecked(True)
        form.poll()
        self.assertTrue(form.flush(widgets))
        self.assertEqual(self.settings.framing.read("zoom"), (25, False))
        key = self.settings.framing.options[0].identifier
        widgets[f"setting:{key}"].SetValue(15)
        form.poll()
        self.assertTrue(form.flush(widgets))
        self.assertEqual(self.settings.framing.read("zoom"), (15, True))
        widgets, form = self.build()
        self.assertIn("Custom", widgets["group:framing:zoom"].calls["SetText"][0])
        self.assertTrue(form.model.restore())
        self.assertEqual(self.settings.framing.read("zoom"), (15, False))
        self.assertTrue(form.model.undo())
        self.assertEqual(self.settings.framing.read("zoom"), (15, True))

    def test_framing_failure_and_owner_change_do_not_save_a_stale_draft(self):
        widgets, form = self.build()
        key = self.settings.framing.options[2].identifier
        widgets[f"setting:{key}"].SetValue(37)
        form.poll()
        original = self.package.camera.elected_elsewhere
        self.package.camera.elected_elsewhere = lambda: True
        try:
            form.poll()
            self.assertEqual(self.settings.framing.read("horizontal"), (10, False))
            self.assertEqual(widgets[f"setting:{key}"].calls["SetIsEnabled"], (False,))
        finally:
            self.package.camera.elected_elsewhere = original
        form.poll()
        widgets[f"setting:{key}"].SetValue(20)
        form.poll()
        save = self.package.mod.save_settings
        self.package.mod.save_settings = lambda: (_ for _ in ()).throw(OSError("private"))
        try:
            self.assertFalse(form.flush(widgets))
            self.assertEqual(self.settings.framing.read("horizontal"), (10, False))
            self.assertEqual(widgets[f"setting:{key}"].GetValue(), 10)
        finally:
            self.package.mod.save_settings = save

    def test_framing_language_and_zoom_dependency(self):
        widgets, form = self.build()
        self.assertEqual(widgets["framing:height:preset:0_label"].calls["SetText"], ("Standard",))
        form.model.change_language("FR")
        form.refresh_labels(widgets)
        self.assertEqual(widgets["framing:height:preset:0_label"].calls["SetText"], ("Standard",))
        self.assertEqual(widgets["framing:zoom:preset:0_label"].calls["SetText"], ("Large",))
        self.settings.ads.option.value = False
        form.sync(widgets)
        key = self.settings.framing.options[0].identifier
        self.assertEqual(widgets[f"setting:{key}"].calls["SetIsEnabled"], (False,))

    def test_native_refusal_waits_for_rollback_before_unlocking_or_saving(self):
        widgets, form = self.build()
        confirmed, writes = [None], []
        original_confirm = self.settings.framing.confirm
        original_save = self.package.mod.save_settings
        self.settings.framing.confirm = lambda _restoring=False: confirmed[0]
        self.package.mod.save_settings = lambda: writes.append(self.settings.framing.snapshot())
        now = [1]
        form.model.transaction.clock = lambda: now[0]
        try:
            widgets["framing:zoom:preset:2"].SetIsChecked(True)
            form.poll()
            self.assertFalse(form.flush(widgets))
            self.assertTrue(form.model.transaction.pending)
            self.assertNotEqual(form.notice, "saved")
            self.assertEqual(writes, [])
            confirmed[0] = False
            form.poll()
            self.assertEqual(self.settings.framing.read("zoom"), (15, False))
            self.assertTrue(form.model.transaction.pending)
            self.assertFalse(form.close_ready())
            confirmed[0] = True
            now[0] = 3_000_000_000
            form.poll()
            self.assertFalse(form.model.transaction.pending)
            self.assertEqual(form.notice, "camera_refused")
            self.assertEqual(writes, [((15, False), (10, False), (0, False))])
        finally:
            self.settings.framing.confirm = original_confirm
            self.package.mod.save_settings = original_save

    def test_double_save_failure_keeps_controls_locked_until_compensation(self):
        widgets, form = self.build()
        original = self.package.mod.save_settings
        original_path = self.package.mod.settings_file
        # An opaque custom writer cannot prove that the original disk state survived.
        self.package.mod.settings_file = None
        now = [1]
        form.model.transaction.clock = lambda: now[0]
        self.package.mod.save_settings = lambda: (_ for _ in ()).throw(OSError("private"))
        try:
            widgets["framing:zoom:preset:2"].SetIsChecked(True)
            form.poll()
            self.assertFalse(form.flush(widgets))
            self.assertTrue(form.model.transaction.pending)
            self.assertFalse(form.close_ready())
            form.poll()
            self.assertEqual(widgets["framing:zoom:preset:2"].calls["SetIsEnabled"], (False,))
            self.assertEqual(self.settings.framing.read("zoom"), (15, False))
        finally:
            self.package.mod.save_settings = original
            self.package.mod.settings_file = original_path
        now[0] = 3_000_000_000
        form.poll()
        self.assertFalse(form.model.transaction.pending)
        self.assertEqual(form.notice, "failed")
