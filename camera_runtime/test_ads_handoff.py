"""The elected mod cannot take over while the previous HUD lease needs restoration."""
import unittest
from types import SimpleNamespace as NS
from apex_camera_runtime.runtime import CameraRuntime


class Third:
    def __init__(self):
        self.ads = NS(pending=False)
        self.cleanup_retry = NS(waiting=False)
        self.syncs = []
        self.stops = 0

    def sync(self, owner, *_args):
        self.syncs.append(owner)

    def stop(self):
        self.stops += 1


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.applied = []
        self.third = Third()
        fov = NS(stop=lambda: None, apply=lambda owner, *_: self.applied.append(owner))
        self.runtime = CameraRuntime(fov, self.third)
        self.runtime.register("omni_sprint", 100, object())
        self.runtime.register("apex_movement", 200, object())
        self.runtime.tick(object(), 1)

    def test_new_owner_waits_then_starts_after_natural_restoration(self):
        self.third.ads.pending = True
        self.runtime.unregister("apex_movement")
        for frame in range(2, 12):
            self.runtime.tick(object(), frame)
        self.assertEqual(self.third.syncs, ["apex_movement"])
        self.assertEqual(self.applied, ["apex_movement"])
        self.third.ads.pending = False
        self.runtime.tick(object(), 12)
        self.assertEqual(self.third.syncs[-1], "omni_sprint")
        self.assertEqual(self.applied[-1], "omni_sprint")

    def test_same_owner_cannot_restart_during_cleanup_observer_wait(self):
        self.third.cleanup_retry.waiting = True
        self.runtime.tick(object(), 2)
        self.assertEqual(self.third.syncs, ["apex_movement"])

    def test_normal_hud_restoration_keeps_the_same_owner_camera_running(self):
        stops = self.third.stops
        self.third.ads.pending = True
        self.runtime.tick(object(), 2)
        self.assertEqual(self.third.stops, stops)
        self.assertEqual(self.third.syncs, ["apex_movement", "apex_movement"])

    def test_controller_cannot_be_replaced_while_it_owns_pending_hud(self):
        self.third.ads.pending = True
        replacement = Third()
        with self.assertRaises(RuntimeError):
            self.runtime.set_third_person(replacement)
        self.assertIs(self.runtime.third_person, self.third)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HandoffTests))
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
