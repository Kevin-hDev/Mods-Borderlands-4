"""Cleanup retries stay single, bounded and block a successor until release succeeds."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.cleanup_retry import CleanupRetry  # noqa: E402
from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bridge, Hooks, Manager, Settings  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class CleanupTarget:
    def __init__(self):
        self.cleanup_pending = True
        self.fail = True
        self.stops = 0

    def stop(self, stale=False, now_ns=None):
        self.stops += 1
        if self.fail:
            raise RuntimeError("still owned")
        self.cleanup_pending = False


hooks = Hooks()
messages = []
retry = CleanupRetry(hooks, "camera", clock=lambda: 100_000_000, log=messages.append)
target = CleanupTarget()
retry.schedule(target, now_ns=0, stale=True)
retry.schedule(target, now_ns=0, stale=True)
check("only one cleanup retry hook is pending", len(hooks.items) == 1)
retry.retry(target, 100_000_000)
check("a failed cleanup keeps its single hook", target.stops == 1 and len(hooks.items) == 1)
target.fail = False
retry.retry(target, 300_000_000)
check("a successful cleanup removes the retry hook", target.stops == 2 and hooks.items == {})

manager, bridge, owner_hooks = Manager(), Bridge(), Hooks()
actor = object()
old_pc = types.SimpleNamespace(_get_address=lambda: 10, OakCharacter=actor,
                               PlayerCameraManager=manager)
new_pc = types.SimpleNamespace(_get_address=lambda: 10, OakCharacter=object(),
                               PlayerCameraManager=manager)
controller = ThirdPersonController(owner_hooks, bridge, "owner", clock=lambda: 100_000_000)
settings = Settings()
controller.sync("apex", old_pc, settings, 0)
bridge.fail_stop = True
try:
    controller.sync("apex", new_pc, settings, 0)
except RuntimeError:
    pass
controller.sync("apex", new_pc, settings, 50_000_000)
check("an incomplete cleanup blocks the successor", bridge.starts == 1)
bridge.fail_stop = False
controller.sync("apex", new_pc, settings, 100_000_000)
check("the successor starts only after cleanup succeeds", bridge.starts == 2)
controller.stop()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
