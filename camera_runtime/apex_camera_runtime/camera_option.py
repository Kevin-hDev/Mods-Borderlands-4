"""A visible bool whose live value is committed only by the camera runtime."""

from typing import Any, Callable

from mods_base import BoolOption


class CameraBoolOption(BoolOption):
    def __init__(self, identifier: str, value: bool, *, route: Callable[[bool], Any],
                 ready: Callable[[], bool] = lambda: True,
                 cancel: Callable[[], bool] = lambda: False,
                 **kwargs: Any) -> None:
        if (type(value) is not bool or not callable(route) or not callable(ready)
                or not callable(cancel)):
            raise ValueError("invalid camera option")
        super().__init__(identifier, value, **kwargs)
        self._camera_route = route
        self._camera_ready = ready
        self._camera_cancel = cancel
        self._camera_commit = False
        self._camera_status = "confirmed"

    def __setattr__(self, name: str, value: Any) -> None:
        if (name == "value" and hasattr(self, "_camera_route")
                and not getattr(self, "_camera_commit", False)
                and bool(getattr(getattr(self, "mod", None), "is_enabled", False))):
            if type(value) is bool:
                if getattr(self, "value", None) is value:
                    self._camera_status = "confirmed"
                    return
                if not self._camera_ready():
                    self._camera_status = "waiting"
                    return
                accepted = self._camera_route(value)
                if getattr(self, "value", None) is value:
                    self._camera_status = "confirmed"
                else:
                    self._camera_status = "pending" if accepted is True else "refused"
            return
        super().__setattr__(name, value)

    @property
    def camera_status(self) -> str:
        return self._camera_status

    def commit(self, value: bool) -> None:
        if type(value) is not bool:
            raise ValueError("invalid camera option value")
        self._camera_commit = True
        try:
            self.value = value
            self._camera_status = "confirmed"
        finally:
            self._camera_commit = False

    def reject(self) -> None:
        self._camera_status = "refused"

    def cancel_pending(self) -> bool:
        if self._camera_status == "waiting":
            self._camera_status = "refused"
            return True
        if self._camera_status != "pending":
            return False
        try:
            accepted = self._camera_cancel() is True
        except Exception:
            accepted = False
        if accepted:
            self._camera_status = "refused"
        return accepted
