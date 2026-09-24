"""Process-wide coordinator for the elected mod's camera settings."""

from typing import Any

from .arbitration import Arbiter, Client
from .constants import PROTOCOL

CHECK_NS = 500_000_000


class CameraRuntime:
    def __init__(self, fov_engine: Any, third_person: Any = None) -> None:
        self.arbiter = Arbiter()
        self.fov = fov_engine
        self.third_person = third_person
        self._active_client: Client | None = None
        self._next_fov_ns = 0
        self._setup_owner: str | None = None
        self._setup_failed = False

    def register(self, owner: str, priority: int, settings: Any, protocol: int = PROTOCOL) -> None:
        self.arbiter.register(Client(owner, priority, settings), protocol)

    def unregister(self, owner: str) -> None:
        active = self.arbiter.active()
        error = None
        try:
            if active is not None and active.owner == owner:
                self._stop_active()
        except Exception as caught:
            error = caught
        finally:
            self.arbiter.unregister(owner)
            if self._setup_owner == owner:
                self._setup_owner, self._setup_failed = None, False
        if error is not None:
            raise error

    def set_third_person(self, controller: Any) -> None:
        if self.third_person is not None and self.third_person is not controller:
            self.third_person.stop()
        self.third_person = controller

    def prepare_third_person(self, owner: str, enabled: bool, setup: Any) -> Exception | None:
        active = self.arbiter.active()
        if active is None or active.owner != owner:
            return None
        if self._setup_owner != owner:
            self._setup_owner, self._setup_failed = owner, False
        if not enabled:
            self._setup_failed = False
            return None
        if self.third_person is not None or self._setup_failed:
            return None
        try:
            setup(self)
        except Exception as error:
            self._setup_failed = True
            return error
        return None

    def toggle_third_person(self, owner: str) -> bool:
        """Toggle only the elected owner's saved setting, so one key press has one authority."""
        client = self.arbiter.active()
        if client is None or client.owner != owner:
            return False
        try:
            client.settings.set_third_person(not client.settings.third_person_enabled())
        except Exception:
            client.settings.note("third person shortcut: setting could not be saved")
            return False
        return True

    def tick(self, context: Any, now_ns: int) -> None:
        client = self.arbiter.active()
        if client is not self._active_client:
            # The elected owner must advance even if the old native unit needs its bounded cleanup worker.
            try:
                self._stop_active()
            finally:
                self._active_client = client
                self._next_fov_ns = 0
        if client is None:
            return
        if self.third_person is not None:
            self.third_person.sync(client.owner, context, client.settings, now_ns)
        player = context
        if hasattr(context, "Player"):
            player = context.Player if getattr(context, "OakCharacter", None) is not None else None
        if player is None:
            # Gameplay departure is a boundary, not a periodic refresh: one callback must release the owned FOV.
            self._next_fov_ns = 0
        if now_ns >= self._next_fov_ns:
            self._next_fov_ns = now_ns + CHECK_NS
            self.fov.apply(client.owner, player, client.settings)

    def _stop_active(self) -> None:
        errors = []
        try:
            self.fov.stop()
        except Exception as error:
            errors.append(error)
        if self.third_person is not None:
            try:
                self.third_person.stop()
            except Exception as error:
                errors.append(error)
        self._active_client, self._next_fov_ns = None, 0
        if errors:
            raise RuntimeError("camera cleanup incomplete") from errors[0]

    def stop(self) -> None:
        self._stop_active()
