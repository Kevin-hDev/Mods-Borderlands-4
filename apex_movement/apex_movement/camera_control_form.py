"""Immediate capture for camera commands; at most one action/device/key draft exists."""

import unrealsdk

from .camera_control_config import SLOTS


class Form:
    def __init__(self, widgets, actions):
        self.widgets, self.actions = widgets, actions
        self.draft = ()
        self.changed, self.notice = False, "ready"

    def resolve(self):
        widgets = {name: reference() for name, reference in self.widgets.items()}
        if any(widget is None for widget in widgets.values()):
            raise ValueError("Window widget unavailable")
        return widgets

    @staticmethod
    def take(widget):
        if not widget.IsChecked():
            return False
        widget.SetIsChecked(False)
        return True

    @staticmethod
    def clear_selector(widget):
        empty = unrealsdk.make_struct("InputChord", Key=unrealsdk.make_struct("Key", KeyName="None"))
        widget.SetSelectedKey(empty)

    def selecting(self):
        widgets = self.resolve()
        return any(widgets[f"command:{action}:{device}"].GetIsSelectingKey()
                   for action, device in SLOTS)

    def set_enabled(self, enabled):
        widgets = self.resolve()
        for action, device in SLOTS:
            widgets[f"command:{action}:{device}"].SetIsEnabled(enabled)
            widgets[f"clear:{action}:{device}"].SetIsEnabled(enabled)
        widgets["commands_reset"].SetIsEnabled(enabled)

    def _finish(self, widgets, action, device, key):
        self.draft = (action, device, key)
        assign = getattr(self.actions, "assign_command", None) or self.actions.assign
        success = assign(action, device, key)
        self.changed = True
        status_owner = getattr(self.actions, "command_actions", self.actions)
        self.notice = "saved" if success else getattr(status_owner, "last_status", "failed")
        widgets["commands_status"].SetText(self.notice)
        self.clear_selector(widgets[f"command:{action}:{device}"])
        self.draft = ()

    def poll(self):
        widgets = self.resolve()
        self.changed = False
        if self.take(widgets["commands_reset"]):
            restore = getattr(self.actions, "default_commands", None) or self.actions.defaults
            success = restore()
            self.changed, self.notice = True, "restored" if success else "failed"
            widgets["commands_status"].SetText(self.notice)
            return False
        active = [f"command:{action}:{device}" for action, device in SLOTS
                  if widgets[f"command:{action}:{device}"].GetIsSelectingKey()]
        if active:
            for action, device in SLOTS:
                name = f"command:{action}:{device}"
                widgets[name].SetIsEnabled(name == active[0])
            return False
        for action, device in SLOTS:
            widgets[f"command:{action}:{device}"].SetIsEnabled(True)
        for action, device in SLOTS:
            selector = widgets[f"command:{action}:{device}"]
            if self.take(widgets[f"clear:{action}:{device}"]):
                self._finish(widgets, action, device, None)
                return False
            key = str(selector.SelectedKey.Key.KeyName)
            if key in ("", "None"):
                continue
            if key in ("Escape", "LeftMouseButton"):
                self.clear_selector(selector)
                return False
            self._finish(widgets, action, device, key)
            return False
        return False
