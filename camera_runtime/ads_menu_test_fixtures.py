"""The same persistent ADS contract is exercised against each real mod adapter."""

class AdsSettingsTests:
    def test_saved_choice_is_the_registered_sdk_option(self):
        choice = self.settings.ads.option
        options = getattr(self.settings, "OPTIONS", getattr(self.settings, "ALL", ()))
        self.assertEqual(sum(item.identifier == "third_person_ads" for item in options), 1)
        self.assertIn(choice, options)
        self.assertIs(choice.mod, self.mod)
        self.assertTrue(self.adapter.third_person_ads())
        self.assertFalse(self.settings.third_person.default_value)
        choice.value = False
        self.assertFalse(self.adapter.third_person_ads())
        choice.value = True
        self.assertTrue(self.adapter.third_person_ads())

    def test_save_failure_rolls_back_the_same_registered_option(self):
        choice = self.settings.ads.option
        previous, save = choice.value, self.mod.save_settings
        def fail():
            raise OSError("save refused")
        self.mod.save_settings = fail
        try:
            with self.assertRaises(OSError):
                self.settings.ads.save(not previous)
            self.assertIs(choice.value, previous)
        finally:
            self.mod.save_settings = save

    def test_real_sdk_base_option_keeps_the_orbit_entry_view(self):
        import sys
        from types import SimpleNamespace as NS
        camera = sys.modules[self.adapter.__class__.__module__]
        previous = camera._runtime, camera._registered, self.mod.is_enabled
        base = self.settings.third_person
        original = base.value
        try:
            camera._runtime = NS(base_view_locked=lambda _owner: True)
            camera._registered = self.mod.is_enabled = True
            with self.assertRaises(ValueError):
                base.value = not original
            self.assertIs(base.value, original)
            camera._runtime = NS(base_view_locked=lambda _owner: False)
            base.value = not original
            self.assertIs(base.value, not original)
        finally:
            base.commit(original)
            camera._runtime, camera._registered, self.mod.is_enabled = previous
