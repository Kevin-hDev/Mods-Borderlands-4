"""Process-wide coordinator for the elected mod's camera settings."""

from typing import Any

from .arbitration import Arbiter, Client
from .constants import PROTOCOL
from .ads_coordination import transfer_pending
from .orbit_entry import OrbitEntry
from .speed_fov import SpeedFov, step as speed_step

CHECK_NS = 500_000_000


class CameraRuntime:
    def __init__(self, fov_engine: Any, third_person: Any = None) -> None:
        self.arbiter = Arbiter()
        self.fov = fov_engine
        self.third_person = third_person
        self.loot = None
        # The framing at the wheel (vehicle_framing.py), made by shared.py as the loot unit.
        self.vehicle = None
        self._active_client: Client | None = None
        self._next_fov_ns = 0
        self._setup_owner: str | None = None
        self._setup_failed = False
        self.orbit_entry = OrbitEntry()
        self.speed_fov = SpeedFov()

    def register(self, owner: str, priority: int, settings: Any, protocol: int = PROTOCOL) -> None:
        self.arbiter.register(Client(owner, priority, settings), protocol)

    def ads_status(self, owner: str) -> str | None:
        from .ads_status import for_owner
        return for_owner(self, owner)

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
        # The shared runtime must refuse replacement while the previous controller still owns HUD state.
        if self.third_person is not None and self.third_person is not controller:
            self.third_person.stop()
            if transfer_pending(self.third_person):
                raise RuntimeError("camera restoration pending")
        self.third_person = controller

    def prepare_third_person(self, owner: str, enabled: bool, setup: Any) -> Exception | None:
        active = self.arbiter.active()
        if active is None or active.owner != owner:
            return None
        if self._setup_owner != owner:
            self._setup_owner, self._setup_failed = owner, False
        if not (enabled or getattr(active.settings, 'orbit_enabled', lambda: False)()
                or self.orbit_entry.pending):
            self._setup_failed = False
            return None
        if self.third_person is not None or self._setup_failed:
            return None
        try:
            setup(self)
        except Exception as error:
            self._setup_failed = True
            self.orbit_entry.cancel(active)
            return error
        return None

    def toggle_third_person(self, owner: str) -> bool:
        """Toggle only the elected owner's saved setting, so one key press has one authority."""
        client = self.arbiter.active()
        if client is None or client.owner != owner:
            return False
        try:
            if self.base_view_locked(owner):
                return False
            client.settings.set_third_person(not client.settings.third_person_enabled())
        except Exception:
            client.settings.note("third person shortcut: setting could not be saved")
            return False
        return True

    def base_view_locked(self, owner: str) -> bool:
        return self.orbit_entry.base_view_locked(self, owner)

    def camera_ready(self, owner: str) -> bool:
        client = self.arbiter.active()
        if client is None or client.owner != owner:
            return False
        return bool((self.third_person is not None and self.third_person.orbit_available())
                    or self.orbit_entry.ready(self, client))

    def toggle_shoulder(self, owner: str) -> bool:
        client = self.arbiter.active()
        if client is None or client.owner != owner:
            return False
        try:
            left = client.settings.shoulder_left()
        except Exception:
            return False
        return self.set_shoulder(owner, not left)

    def set_shoulder(self, owner: str, left: bool) -> bool:
        client = self.arbiter.active()
        if (type(left) is not bool or client is None or client.owner != owner
                or self.third_person is None):
            return False
        try:
            if (not client.settings.third_person_enabled()
                    or not self.third_person.shoulder_available()):
                return False
            return bool(self.third_person.set_shoulder(client.settings, left))
        except Exception:
            client.settings.note("shoulder shortcut: setting could not be saved")
            return False

    def toggle_orbit(self, owner: str) -> bool:
        client = self.arbiter.active()
        if client is None or client.owner != owner:
            return False
        try:
            if self.third_person is not None and self.third_person.orbit_available():
                return bool(self.third_person.toggle_orbit(client.settings, self.third_person.clock()))
            return self.orbit_entry.request(self, client, not client.settings.orbit_enabled())
        except Exception:
            client.settings.note("orbit shortcut: setting could not be saved")
            return False

    def set_orbit(self, owner: str, enabled: bool) -> bool:
        client = self.arbiter.active()
        if type(enabled) is not bool or client is None or client.owner != owner:
            return False
        try:
            if self.third_person is None or not self.third_person.orbit_available():
                return self.orbit_entry.request(self, client, enabled)
            return bool(self.third_person.set_orbit(
                client.settings, enabled, self.third_person.clock()))
        except Exception:
            client.settings.note("orbit setting: camera change was refused")
            return False

    def adjust_orbit_zoom(self, owner: str, direction: int) -> bool:
        client = self.arbiter.active()
        if (client is None or client.owner != owner or self.third_person is None
                or self.third_person.zoom.settings is not client.settings):
            return False
        try:
            return self.third_person.zoom.change(client.settings, direction)
        except Exception:
            client.settings.note("Orbit Camera zoom unavailable. Please retry.")
            return False

    def cancel_orbit(self, owner: str, *, restore: bool = True) -> bool:
        from .runtime_cancellation import cancel
        return cancel(self, owner, restore=restore)

    def tick(self, context: Any, now_ns: int) -> None:
        client = self.arbiter.active()
        retry = getattr(self.third_person, "cleanup_retry", None)
        # Normal HUD restoration is not a camera teardown; only handoff or explicit shutdown waits.
        if transfer_pending(self.third_person) and (
                client is not self._active_client or getattr(retry, "waiting", False)):
            self.third_person.stop()
            if transfer_pending(self.third_person):
                return
        if client is not self._active_client:
            # The elected owner must advance even if the old native unit needs its bounded cleanup worker.
            try:
                self._stop_active()
            finally:
                self._active_client = None if transfer_pending(self.third_person) else client
                self._next_fov_ns = 0
            if transfer_pending(self.third_person):
                return
        if client is None:
            return
        self.orbit_entry.observe(client, context)
        if self.loot is not None:
            self.loot.sync(client.owner, context, client.settings, now_ns)
        self.orbit_entry.sync(self, client, context, now_ns)
        if self.vehicle is not None:
            self.vehicle.sync(client.settings)
        player = context
        if hasattr(context, "Player"):
            player = context.Player if getattr(context, "OakCharacter", None) is not None else None
        if player is None:
            # Gameplay departure is a boundary, not a periodic refresh: one callback must release the owned FOV.
            self._next_fov_ns = 0
        # The speed gain moves every frame; without it, ownership is checked twice a second.
        gain = speed_step(self.speed_fov, client.settings, context if player is not None else None, now_ns)
        if now_ns >= self._next_fov_ns or self.speed_fov.moved:
            self._next_fov_ns = now_ns + CHECK_NS
            self.fov.apply(client.owner, player, client.settings, gain, self.speed_fov.ceiling)

    def _stop_active(self) -> None:
        self.orbit_entry.retirement.retire(self.third_person)
        self.orbit_entry.reset()
        errors = []
        for unit in (self.loot, self.fov, self.vehicle):
            if unit is not None:
                try:
                    unit.stop()
                except Exception as error:
                    errors.append(error)
        if self.third_person is not None:
            try:
                self.third_person.stop()
            except Exception as error:
                errors.append(error)
        self._active_client, self._next_fov_ns = None, 0
        self.speed_fov.reset()
        if errors:
            raise RuntimeError("camera cleanup incomplete") from errors[0]

    def stop(self) -> None:
        self._stop_active()
