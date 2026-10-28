"""Orbit's real camera forms keep their base view stable, including synthetic clicks."""


class OrbitPanelTests:
    def test_orbit_locks_base_switch_and_unlocks_it_live(self):
        camera = self.package.camera
        original = camera.base_view_locked
        locked = [True]
        camera.base_view_locked = lambda: locked[0]
        try:
            widgets, form = self.build()
            self.assertEqual(widgets['setting:third_person'].calls['SetIsEnabled'], (False,))
            widgets['setting:third_person'].SetIsChecked(True)
            form.poll()
            self.assertNotIn('third_person', form.pending)
            self.assertTrue(self.settings.third_person_enabled())
            locked[0] = False
            form.poll()
            self.assertEqual(widgets['setting:third_person'].calls['SetIsEnabled'], (True,))
        finally:
            camera.base_view_locked = original

    def test_orbit_page_does_not_require_third_person(self):
        self.settings.third_person.commit(False)
        widgets, form = self.build()
        self.assertEqual(widgets['setting:orbit'].calls['SetIsEnabled'], (True,))
        if hasattr(self.package, 'panel_camera_pages'):
            pages = self.package.panel_camera_pages
            group = next(group for group in form.model.groups if group.identifier == 'orbit_camera_menu')
            message = pages.description(form, group, 'orbit_camera', 'FR')
            self.assertNotIn(self.package.panel_i18n.text('third_person_needed', 'FR'), message)
