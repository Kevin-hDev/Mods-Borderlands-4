"""One small pending draft per framing group, persisted through the existing transaction."""
import time
from . import camera, camera_control_config as config, panel_framing as view, panel_theme as t


class Form:
    def __init__(self, form, widgets):
        self.form = form
        self.pending = {}
        self.changed_at = 0
        self.waiting = False
        self.saved = ()
        self.reset(widgets)

    def reset(self, widgets):
        self.pending.clear()
        self.saved = config.FRAMING_OPTIONS.snapshot()
        for index, (value, _custom) in enumerate(self.saved):
            option = config.FRAMING_OPTIONS.options[index * 2]
            widgets[f"setting:{option.identifier}"].SetValue(float(value))

    def enabled(self, group):
        shown = self.form.shown
        return (not camera.elected_elsewhere() and not self.form.model.transaction.pending
                and shown.get("third_person") is True and shown.get("orbit") is not True
                and (group.key != "zoom" or shown.get("third_person_ads") is True))

    def flush(self, widgets):
        if not self.pending:
            return True
        if camera.elected_elsewhere():
            self.reset(widgets)
            self.form.report(widgets, "camera_draft_discarded")
            return False
        if self.form.model.transaction.pending:
            return False
        changes = []
        for index, (value, custom) in self.pending.items():
            option, origin = config.FRAMING_OPTIONS.options[index * 2:index * 2 + 2]
            changes.extend(((option, value), (origin, custom)))
        success = self.form.model.save(tuple(changes), "write")
        self.reset(widgets)
        waiting = success is None and not self.form.model.transaction.rolling_back
        self.waiting = waiting
        self.form.report(widgets, self.saved_notice() if success else "ready" if waiting else self.form.failure_notice())
        return success is True

    @staticmethod
    def saved_notice():
        reason = camera.framing_status()
        if reason in ("zoom_unavailable", "position_unavailable"):
            return "framing_saved_partial"
        return "framing_saved_unavailable" if reason == "unavailable" else "saved"

    def refresh(self, widgets):
        if self.waiting and not self.form.model.transaction.pending:
            self.waiting = False
            if self.form.notice == "saved":
                self.form.report(widgets, self.saved_notice())
        if config.FRAMING_OPTIONS.snapshot() != self.saved:
            self.reset(widgets)
        if camera.elected_elsewhere() and self.pending:
            self.reset(widgets)
            self.form.report(widgets, "camera_draft_discarded")
        now = time.perf_counter_ns()
        for index, group in enumerate(config.FRAMING_GROUPS):
            option = config.FRAMING_OPTIONS.options[index * 2]
            enabled = self.enabled(group)
            current = self.pending.get(index, self.saved[index])
            choice = current
            for preset, (_label, value) in enumerate(group.presets):
                if self.form.take(widgets[f"framing:{group.key}:preset:{preset}"]) and enabled:
                    choice = value, False
                    widgets[f"setting:{option.identifier}"].SetValue(float(value))
            raw = widgets[f"setting:{option.identifier}"].GetValue()
            if enabled and abs(raw - choice[0]) >= group.step * 0.01:
                try:
                    choice = self.form.model.normalize(option, raw), True
                except (TypeError, ValueError, OverflowError):
                    self.reset(widgets)
                    self.form.report(widgets, "failed")
                    return
            if choice != current:
                self.pending[index] = choice
                self.changed_at = now
            view.show(widgets, group, option, choice, self.form.model.language,
                      enabled, camera.framing_status())
        if self.pending and now - self.changed_at >= t.SAVE_DELAY_NS:
            self.flush(widgets)


def refresh(form, widgets):
    if "heading:framing:zoom" not in widgets:
        return
    if not hasattr(form, "framing_form"):
        form.framing_form = Form(form, widgets)
    form.framing_form.refresh(widgets)
