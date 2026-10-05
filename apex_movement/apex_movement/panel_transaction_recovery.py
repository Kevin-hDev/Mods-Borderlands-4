"""Bounded rollback restores memory even when native acknowledgement is unavailable."""
from . import panel_transaction_config as config


class Recovery:
    def _fail(self):
        if self.rolling_back:
            self.rollback_failures += 1
            if self.rollback_failures >= config.ROLLBACK_ATTEMPTS:
                return self._abandon_rollback()
            self.retry_after = self.clock() + config.TRANSACTION_TIMEOUT_NS * self.rollback_failures
            self.confirm_since = 0
            return None
        self.changes = self._ordered(self.previous)
        self.index = 0
        self.waiting = False
        self.waiting_since = self.confirm_since = 0
        self.rolling_back = True
        self.rollback_deadline = min(self.deadline, self.clock() + config.ROLLBACK_TIMEOUT_NS)
        return self._run()

    def _abandon_rollback(self, *, restore_camera=True):
        if self.rolling_back and self.restoration_confirmed:
            # A write failure after confirmed local recovery is still a write failure.
            if self.persistence_failed:
                self.failure_reason = "failed"
            self.report("panel:persistence", config.SAVE_FAILURE)
            return self._finish(False)
        self.failure_reason = "rollback_abandoned"
        # Logical cancellation and local restoration are distinct from physical camera cleanup.
        # Never save a failed batch, and never leave its scalar writes for an unrelated save.
        for option, value in self.previous:
            camera = callable(getattr(option, "commit", None)) and hasattr(option, "camera_status")
            if camera:
                try:
                    self._cancel_current(option, restore=restore_camera)
                except Exception:
                    self.report("panel:cancel", config.RESTORE_FAILURE)
            try:
                if camera:
                    option.commit(value)
                    option.reject()
                else:
                    option.value = value
            except Exception:
                self.report("panel:cancel", config.RESTORE_FAILURE)
        if self.finalize is not None:
            try:
                if self.finalize(True) is not True:
                    self.report("panel:controls", config.RESTORE_FAILURE)
            except Exception:
                self.report("panel:controls", config.RESTORE_FAILURE)
        self.report("panel:save", config.RESTORE_FAILURE)
        return self._finish(False)

    def _expired(self):
        return self.clock() >= self.deadline

    def abort(self):
        """Revoke a failed window operation; physical cleanup must validate current ownership."""
        return self._abandon_rollback(restore_camera=False) if self.pending else None
