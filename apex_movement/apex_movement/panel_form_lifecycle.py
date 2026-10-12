"""Shared settings-form widget lifetime, closing and transaction notices."""


class Lifecycle:
    # The open pop-up's key (panel_popup.py), or None.
    popup = None
    # The camera profile window's form (panel_profile_form.py), made by the camera mods' form only.
    profile_form = None

    def resolve(self):
        widgets = {name: reference() for name, reference in self.widgets.items()}
        if any(widget is None for widget in widgets.values()):
            raise ValueError("Window widget unavailable")
        return widgets

    def close_deadline(self):
        return self.model.transaction.deadline

    def close_ready(self):
        return self.model.cancel_transaction()

    def close_abort(self):
        self.model.transaction.abort()

    def escape(self):
        """Escape closes an open pop-up alone; otherwise the window, as the Close button does, saving what is still
        pending (control_escape)."""
        if self.popup is not None:
            from . import panel_popup
            panel_popup.hide(self, self.resolve())
            return False
        return self.flush(self.resolve())

    def poll_popup(self, widgets):
        """True while a pop-up or the camera profile window is open: it alone takes the clicks."""
        if self.profile_form is not None and self.profile_form.poll(widgets):
            return True
        if self.popup is None:
            return False
        from . import panel_popup
        panel_popup.poll(self, widgets)
        return True

    def failure_notice(self):
        return getattr(self.model.transaction, "failure_reason", "failed") or "failed"
