# Generated: the window Kevin's mods share, taken from Hunter Change's plain window, under It Follows'
# names. Its comments may speak of other mods. Never edited by hand: docs/RUN/outils/menu_window.py
# writes this file.
"""Shared settings-form widget lifetime, closing and transaction notices."""

_MISSING = object()
_updates = _MISSING


def updates_module():
    """The update notes' pop-up where this file ships one, panel_updates.py (Apex Movement's full pack, Kevin,
    2026-10-17); None in every other window made from this one, which ship none and so never show notes. Looked up
    once: the window polls every frame."""
    global _updates
    if _updates is _MISSING:
        _updates = None
    return _updates


class Lifecycle:
    # The open pop-up's key (panel_popup.py), or None.
    popup = None
    # The update notes on show and the page open (panel_updates.py).
    update_notes = ()
    update_page = 0

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
        """True while a pop-up is open: it alone takes the clicks."""
        updates = updates_module()
        if updates is not None and updates.poll(self, widgets):
            return True
        if self.popup is None:
            return False
        from . import panel_popup
        panel_popup.poll(self, widgets)
        return True

    def open_updates(self, widgets):
        updates = updates_module()
        if updates is not None:
            updates.open_if_due(self, widgets)

    def failure_notice(self):
        return getattr(self.model.transaction, "failure_reason", "failed") or "failed"
