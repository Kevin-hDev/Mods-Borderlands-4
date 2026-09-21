"""Window actions and draft keys; the binding service owns persistence."""

import unrealsdk

from .control_bindings import RESERVED

CHOOSE_ONE = "Choose a key. It will be saved immediately."
CHOOSE_TWO = "Choose both keys. Hold them together to grapple."
MISSING = ("", "None")


class Form:
    def __init__(self, widgets, bindings):
        self.widgets, self.bindings = widgets, bindings
        self.two = False
        self.last_keys = None

    def resolve(self):
        widgets = {name: value() for name, value in self.widgets.items()}
        if any(value is None for value in widgets.values()):
            raise ValueError("Window widget unavailable")
        return widgets

    def selecting(self):
        widgets = self.resolve()
        return any(widgets[name].GetIsSelectingKey() for name in ("first", "second"))

    def clear(self, widgets):
        empty = unrealsdk.make_struct("InputChord", Key=unrealsdk.make_struct("Key", KeyName="None"))
        for name in ("first", "second"):
            widgets[name].SetSelectedKey(empty)
        self.last_keys = None

    def show_result(self, widgets, result):
        success, message = result
        widgets["status"].SetText(message)
        widgets["current"].SetText(self.bindings.summary())
        unrealsdk.logging.info(f"[GrappleUIWindow] action_saved={success}")

    def poll(self):
        widgets = self.resolve()
        if widgets["close"].IsChecked():
            return True
        if widgets["reset"].IsChecked():
            widgets["reset"].SetIsChecked(False)
            result = self.bindings.reset()
            self.show_result(widgets, result)
            if result[0]:
                self.two = False
                widgets["two"].SetIsChecked(False)
                widgets["second"].SetIsEnabled(False)
                self.clear(widgets)
            return False
        two = bool(widgets["two"].IsChecked())
        if two != self.two:
            self.two = two
            self.clear(widgets)
            widgets["second"].SetIsEnabled(two)
            widgets["status"].SetText(CHOOSE_TWO if two else CHOOSE_ONE)
            return False
        chosen = tuple(str(widgets[name].SelectedKey.Key.KeyName)
                       for name in (("first", "second") if two else ("first",)))
        if any(key in MISSING for key in chosen) or chosen == self.last_keys or self.selecting():
            return False
        # Remember even a rejected choice: never retry a failed disk write every frame.
        self.last_keys = chosen
        result = self.bindings.save(chosen)
        self.show_result(widgets, result)
        if not result[0] and result[1] == RESERVED:
            # A rejected console key must not look like the saved grapple key.
            self.clear(widgets)
        return False
