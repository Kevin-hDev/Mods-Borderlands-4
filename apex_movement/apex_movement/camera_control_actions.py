"""Atomic persistence for five camera actions and their ten live assignments."""

from . import report


class Actions:
    def __init__(self, commands, mod):
        self.commands, self.mod = commands, mod
        self.last_status = "ready"

    def snapshot(self):
        return {option.identifier: option.value for option in self.commands.options}

    def assign(self, action, device, key):
        try:
            identifier = self.commands.identifier(action, device)
        except ValueError:
            self.last_status = "refused"
            return False
        return self.apply({identifier: key})

    def defaults(self):
        return self.apply(self.commands.defaults())

    def apply(self, changes):
        previous = self.snapshot()
        if not self.prepare(changes):
            return False
        try:
            self.mod.save_settings()
        except Exception:
            self.last_status = "failed"
            self._restore(previous)
            return False
        self.last_status = "saved"
        return True

    def prepare(self, changes, *, restoring=False):
        """Prepare live bindings without saving; the containing transaction owns persistence."""
        try:
            normalized = self.commands.validate(changes)
        except (TypeError, ValueError):
            self.last_status = "refused"
            return False
        previous = self.snapshot()
        try:
            self.commands.set_values(normalized)
            self.commands.align()
        except Exception:
            self.last_status = "failed"
            if restoring:
                # Old saved values remain the authority even if live binding recovery fails.
                report.error_once("commands:restore", "Controls restoration could not be confirmed.")
                return False
            try:
                self.commands.set_values(previous)
                self.commands.align()
            except Exception:
                report.error_once("commands:prepare", "Controls restoration could not be confirmed.")
            return False
        self.last_status = "ready"
        return True

    def _restore(self, previous):
        try:
            self.commands.set_values(previous)
            self.mod.save_settings()
        except Exception:
            report.error_once("commands:rollback", "Controls restoration could not be confirmed.")
            return
        try:
            self.commands.align()
        except Exception:
            report.error_once("commands:rollback", "Controls restoration could not be confirmed.")
