"""Exercise real camera forms at the UMG boundary, not in-game rendering."""

from types import SimpleNamespace as NS


class Struct:
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        value = Struct()
        setattr(self, name, value)
        return value


class Enum:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, name):
        return f"{self.name}.{name}"


class Widget:
    def __init__(self, kind, owner):
        self.kind, self.owner = kind, owner
        self.children, self.calls = [], {}
        self.checked = self.selecting = False
        self.value = 0.0
        self.Font = Struct()
        self.SelectedKey = NS(Key=NS(KeyName="None"))

    def __getattr__(self, name):
        if name.startswith("Set") or name.startswith("AddChild"):
            return lambda *args: self.call(name, args)
        if name[:1].isupper():
            value = Struct()
            setattr(self, name, value)
            return value
        raise AttributeError(name)

    def call(self, name, args):
        if name == "SetContent":
            self.children[:] = [args[0]]
        elif name.startswith("AddChild"):
            self.children.append(args[0])
            return Widget("Slot", self)
        elif name == "SetIsChecked":
            self.checked = args[0]
        elif name == "SetValue":
            self.value = args[0]
        self.calls[name] = args

    def IsChecked(self):
        return self.checked

    def GetValue(self):
        return self.value

    def GetIsSelectingKey(self):
        return self.selecting


class AdsPanelTests:
    def build(self):
        import unrealsdk
        package = self.package
        unrealsdk.construct_object = Widget
        unrealsdk.find_enum = Enum
        unrealsdk.make_struct = lambda _name, **kwargs: NS(**kwargs)
        unrealsdk.find_all = lambda *_args, **_kwargs: []
        package.panel_assets.texture = lambda _world: None
        package.panel_fonts.build = lambda _root: {"title": object(), "body": object()}
        model = package.panel_model.Model(package.mod)
        for group in model.groups:
            if not hasattr(group, "description"):
                group.description = ""
        _root, widgets = package.panel_view.build_view(NS(), model)
        refs = {key: (lambda item=item: item) for key, item in widgets.items()}
        return widgets, package.panel_form.PanelForm(refs, model)

    def setUp(self):
        # These window tests have no renderer; native confirmation is exercised separately.
        self.settings.framing.confirm = lambda _restoring=False: True
        self.settings.third_person.value = True
        self.settings.ads.option.value = True
        self.package.panel_preferences.french.value = False

    def test_choice_labels_in_both_languages_and_reopening(self):
        widgets, form = self.build()
        key = "setting:third_person_ads_label"
        self.assertEqual(widgets[key].calls["SetText"], ("Third Person",))
        self.assertTrue(form.model.write({"third_person_ads": False}))
        widgets, form = self.build()
        self.assertEqual(widgets[key].calls["SetText"], ("First Person",))
        self.assertTrue(form.model.change_language("FR"))
        widgets, form = self.build()
        self.assertEqual(widgets[key].calls["SetText"], ("Première personne",))
        self.assertEqual(widgets["label:third_person_ads"].calls["SetText"], ("VISÉE",))

    def test_disabled_third_person_greys_the_choice(self):
        self.settings.third_person.value = False
        widgets, _form = self.build()
        self.assertEqual(widgets["setting:third_person_ads"].calls["SetIsEnabled"], (False,))

    def test_restore_and_undo_include_the_aim_choice(self):
        _widgets, form = self.build()
        self.assertTrue(form.model.write({"third_person_ads": False}))
        self.assertTrue(form.model.restore())
        self.assertTrue(self.settings.ads.enabled())
        self.assertTrue(form.model.undo())
        self.assertFalse(self.settings.ads.enabled())

    def test_save_failure_restores_choice_and_shown_label(self):
        widgets, form = self.build()
        save = self.package.mod.save_settings
        def fail():
            raise OSError("save unavailable")
        self.package.mod.save_settings = fail
        try:
            widgets["setting:third_person_ads"].SetIsChecked(True)
            form.poll()
            self.assertFalse(form.flush(widgets))
            self.assertTrue(self.settings.ads.enabled())
            self.assertEqual(widgets["setting:third_person_ads_label"].calls["SetText"], ("Third Person",))
        finally:
            self.package.mod.save_settings = save

    def test_runtime_notice_refreshes_without_reopening_and_is_translated(self):
        camera = self.package.camera
        original = getattr(camera, "aim_status", None)
        current = ["cleanup_pending"]
        camera.aim_status = lambda: (current[0], "Returning to the game view.") if current[0] else None
        try:
            widgets, form = self.build()
            self.assertIn("Returning to the game view.", widgets["description:third_person_ads"].calls["SetText"][0])
            form.model.change_language("FR")
            form.poll()
            self.assertIn("Retour à la vue du jeu", widgets["description:third_person_ads"].calls["SetText"][0])
            current[0] = None
            form.poll()
            self.assertNotIn("Retour à la vue du jeu", widgets["description:third_person_ads"].calls["SetText"][0])
        finally:
            if original is None:
                del camera.aim_status
            else:
                camera.aim_status = original

    def test_ownership_change_blocks_the_choice_without_erasing_it(self):
        camera = self.package.camera
        original = getattr(camera, "elected_elsewhere", None)
        current = [False]
        camera.elected_elsewhere = lambda: current[0]
        try:
            widgets, form = self.build()
            current[0] = True
            form.poll()
            self.assertEqual(widgets["setting:third_person_ads"].calls["SetIsEnabled"], (False,))
            widgets["setting:third_person_ads"].SetIsChecked(True)
            form.poll()
            self.assertTrue(self.settings.ads.enabled())
            current[0] = False
            form.poll()
            self.assertEqual(widgets["setting:third_person_ads"].calls["SetIsEnabled"], (True,))
        finally:
            if original is None:
                del camera.elected_elsewhere
            else:
                camera.elected_elsewhere = original

    def test_ownership_loss_discards_a_preexisting_aim_draft_only(self):
        camera = self.package.camera
        original = camera.elected_elsewhere
        current = [False]
        camera.elected_elsewhere = lambda: current[0]
        try:
            widgets, form = self.build()
            widgets["setting:third_person_ads"].SetIsChecked(True)
            form.poll()
            self.assertIs(form.pending["third_person_ads"], False)
            other = next((key for key, option in form.model.options.items()
                          if key not in form.model.camera_options and type(option.default_value) is bool), None)
            if other is not None:
                widgets[f"setting:{other}"].SetIsChecked(True)
                form.poll()
                draft = form.pending[other]
            current[0] = True
            form.poll()
            self.assertNotIn("third_person_ads", form.pending)
            self.assertTrue(form.shown["third_person_ads"])
            if other is not None:
                self.assertIs(form.pending[other], draft)
            form.flush(widgets)
            self.assertTrue(self.settings.ads.enabled())
            self.assertFalse(form.model.write({"third_person_ads": False}))
        finally:
            camera.elected_elsewhere = original

    def test_pending_restore_remains_visible_with_first_person_selected(self):
        camera = self.package.camera
        original = camera.aim_status
        camera.aim_status = lambda: ("cleanup_pending", "Returning to the game view.")
        try:
            self.settings.ads.option.value = False
            widgets, _form = self.build()
            self.assertIn("Returning to the game view.", widgets["description:third_person_ads"].calls["SetText"][0])
            self.settings.third_person.value = False
            widgets, _form = self.build()
            self.assertIn("Returning to the game view.", widgets["description:third_person_ads"].calls["SetText"][0])
        finally:
            camera.aim_status = original
