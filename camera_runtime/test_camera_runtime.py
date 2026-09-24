"""Shared camera arbitration and FOV ownership, without the game SDK."""

import pathlib
import sys
import weakref

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.arbitration import Arbiter, Client  # noqa: E402
from apex_camera_runtime.constants import PROTOCOL  # noqa: E402
from apex_camera_runtime.fov import FovEngine  # noqa: E402
from apex_camera_runtime.runtime import CameraRuntime  # noqa: E402
from apex_camera_runtime.shared import reset_for_tests, shared  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Settings:
    def __init__(self, enabled: bool, wanted: float, saved=(None, None)) -> None:
        self.is_enabled = enabled
        self.wanted = wanted
        self.saved = saved
        self.notes: list[str] = []
        self.third_person = False
        self.toggle_calls = 0

    def fov_enabled(self):
        return self.is_enabled

    def fov_value(self):
        return self.wanted

    def saved_fov_pair(self):
        return self.saved

    def remember_fov_pair(self, native, applied):
        self.saved = (native, applied)

    def note(self, message):
        self.notes.append(message)

    def third_person_enabled(self):
        return self.third_person

    def set_third_person(self, value):
        self.third_person = value
        self.toggle_calls += 1


class Player:
    def __init__(self, address: int, fov: float) -> None:
        self.address = address
        self.BaseFOV = fov


arbiter = Arbiter(max_clients=3)
omni = Client("omni_sprint", 100, object())
apex = Client("apex_movement", 200, object())
arbiter.register(omni, PROTOCOL)
check("the first enabled mod owns the camera", arbiter.active() is omni)
arbiter.register(apex, PROTOCOL)
check("Apex Movement has priority over Omni Sprint", arbiter.active() is apex)
arbiter.unregister("apex_movement")
check("Omni Sprint resumes when Apex Movement leaves", arbiter.active() is omni)
arbiter.register(omni, PROTOCOL)
check("registering one owner twice stays idempotent", arbiter.active() is omni and len(arbiter) == 1)
try:
    arbiter.register(Client("wrong", 300, object()), PROTOCOL + 1)
    check("an incompatible protocol is refused", False)
except RuntimeError:
    check("an incompatible protocol is refused", len(arbiter) == 1)
arbiter.register(Client("second", 10, object()), PROTOCOL)
arbiter.register(Client("third", 20, object()), PROTOCOL)
try:
    arbiter.register(Client("fourth", 30, object()), PROTOCOL)
    check("the externally fed client collection is bounded", False)
except RuntimeError:
    check("the externally fed client collection is bounded", len(arbiter) == 3)

engine = FovEngine(weakref.ref, lambda player: player.address)
omni_settings = Settings(True, 140.0)
apex_settings = Settings(True, 120.0)
player = Player(1, 90.0)
engine.apply("omni_sprint", player, omni_settings)
check("the FOV is applied after its native value is saved",
      player.BaseFOV == 140.0 and omni_settings.saved == (90.0, 140.0))
engine.apply("apex_movement", player, apex_settings)
check("a new owner restores the old value before applying its own",
      player.BaseFOV == 120.0 and apex_settings.saved == (90.0, 120.0))
player.BaseFOV = 105.0
engine.stop()
check("stopping leaves a newer external FOV untouched", player.BaseFOV == 105.0)

engine = FovEngine(weakref.ref, lambda player: player.address)
first, second = Player(1, 90.0), Player(2, 100.0)
engine.apply("omni_sprint", first, omni_settings)
engine.apply("omni_sprint", second, omni_settings)
check("changing player restores the old player and uses the new baseline",
      first.BaseFOV == 90.0 and second.BaseFOV == 140.0)
engine.stop()
check("stopping restores the current player", second.BaseFOV == 100.0)

recovery = Settings(False, 140.0, (98.0, 140.0))
reloaded = Player(3, 140.0)
engine.apply("omni_sprint", reloaded, recovery)
check("a disabled option repairs a persisted override after reload", reloaded.BaseFOV == 98.0)

runtime = CameraRuntime(FovEngine(weakref.ref, lambda item: item.address))
runtime.register("omni_sprint", 100, omni_settings, PROTOCOL)
runtime.tick(Player(4, 90.0), 1_000_000_000)
runtime.register("apex_movement", 200, apex_settings, PROTOCOL)
active_player = Player(5, 95.0)
runtime.tick(active_player, 1_500_000_000)
check("the runtime applies only the elected client's FOV", active_player.BaseFOV == 120.0)
runtime.unregister("apex_movement")
runtime.tick(active_player, 2_000_000_000)
check("the fallback client takes over after unregister", active_player.BaseFOV == 140.0)
runtime.unregister("omni_sprint")
check("removing the last client restores the game", active_player.BaseFOV == 95.0)

toggle_runtime = CameraRuntime(FovEngine(weakref.ref, lambda item: item.address))
toggle_omni = Settings(False, 90.0)
toggle_apex = Settings(False, 90.0)
toggle_runtime.register("omni_sprint", 100, toggle_omni, PROTOCOL)
toggle_runtime.register("apex_movement", 200, toggle_apex, PROTOCOL)
check("the inactive camera owner cannot react to the shared shortcut",
      not toggle_runtime.toggle_third_person("omni_sprint") and toggle_omni.toggle_calls == 0)
check("the elected camera owner toggles exactly once",
      toggle_runtime.toggle_third_person("apex_movement") and toggle_apex.third_person
      and toggle_apex.toggle_calls == 1)
toggle_runtime.stop()

reset_for_tests()


class Third:
    def __init__(self):
        self.calls = []

    def sync(self, owner, context, settings, now_ns):
        self.calls.append((owner, context, settings, now_ns))

    def stop(self):
        pass


third = Third()
context_runtime = CameraRuntime(FovEngine(weakref.ref, lambda item: item.address), third)
context_settings = Settings(True, 130.0)
context_runtime.register("apex_movement", 200, context_settings, PROTOCOL)
context = type("Context", (), {"OakCharacter": object(), "Player": Player(6, 92.0)})()
context_runtime.tick(context, 3_000_000_000)
check("the game controller goes to third person while its Player owns FOV",
      context.Player.BaseFOV == 130.0 and third.calls[0][1] is context
      and third.calls[0][3] == 3_000_000_000)
context_runtime.stop()

setup_runtime = CameraRuntime(FovEngine(weakref.ref, lambda item: item.address))
setup_runtime.register("apex_movement", 200, context_settings, PROTOCOL)
setup_attempts = []


def failing_setup(_runtime):
    setup_attempts.append(True)
    raise RuntimeError("native library blocked")


first_error = setup_runtime.prepare_third_person("apex_movement", True, failing_setup)
setup_runtime.tick(context, 3_100_000_000)
second_error = setup_runtime.prepare_third_person("apex_movement", True, failing_setup)
check("a native setup failure is latched while FOV continues",
      isinstance(first_error, RuntimeError) and second_error is None
      and len(setup_attempts) == 1 and context.Player.BaseFOV == 130.0)
setup_runtime.prepare_third_person("apex_movement", False, failing_setup)
setup_runtime.prepare_third_person("apex_movement", True, failing_setup)
check("turning third person off and on rearms one native setup attempt", len(setup_attempts) == 2)
setup_runtime.stop()

title_runtime = CameraRuntime(FovEngine(weakref.ref, lambda item: item.address))
title_runtime.register("apex_movement", 200, context_settings, PROTOCOL)
title_player = Player(7, 94.0)
title_runtime.tick(type("Game", (), {"OakCharacter": object(), "Player": title_player})(),
                   4_000_000_000)
title_runtime.tick(type("Title", (), {"OakCharacter": None, "Player": title_player})(),
                   4_100_000_000)
check("leaving gameplay gives the game its FOV back without waiting for the periodic check",
      title_player.BaseFOV == 94.0)
title_runtime.stop()


class FailingThird(Third):
    def __init__(self):
        super().__init__()
        self.armed = False

    def sync(self, owner, context, settings, now_ns):
        super().sync(owner, context, settings, now_ns)
        self.armed = True

    def stop(self):
        if self.armed:
            raise RuntimeError("cleanup failed")


failing_runtime = CameraRuntime(FovEngine(weakref.ref, lambda item: item.address), FailingThird())
failing_runtime.register("apex_movement", 200, context_settings, PROTOCOL)
failing_runtime.tick(context, 3_500_000_000)
try:
    failing_runtime.unregister("apex_movement")
except RuntimeError:
    pass
check("unregister removes the client even when third-person cleanup reports an error",
      failing_runtime.arbiter.active() is None and failing_runtime._active_client is None)

first_runtime = shared(weakref.ref, lambda item: item.address)
second_runtime = shared(weakref.ref, lambda item: item.address)
check("both packaged mods receive the same process-wide runtime", first_runtime is second_runtime)
reset_for_tests()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
