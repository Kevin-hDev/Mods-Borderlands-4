"""A camera qualification refusal stays bounded and never becomes a late activation."""
import types
import unittest
from concurrent.futures import Future

from apex_camera_runtime.build_preflight import BuildPreflight


class Function:
    def __init__(self, result):
        self.result, self.calls = result, 0

    def __call__(self):
        self.calls += 1
        return self.result


class BuildPreflightTests(unittest.TestCase):
    def test_refusal_is_logged_once_without_rehashing_each_frame(self):
        library = types.SimpleNamespace(ads_verify_files=Function(21), view_game_build=Function(0))
        messages = []
        job = BuildPreflight(library, messages.append)
        job.start()
        job.future.result(timeout=2)
        for _ in range(120):
            self.assertFalse(job.ready())
        self.assertEqual(library.ads_verify_files.calls, 1)
        self.assertEqual(library.view_game_build.calls, 0)
        self.assertEqual(len(messages), 1)
        self.assertIn("native_status=21", messages[0])

    def test_ready_build_is_identifiable_in_the_log_once(self):
        library = types.SimpleNamespace(ads_verify_files=Function(0), view_game_build=Function(2))
        messages = []
        job = BuildPreflight(library, messages.append)
        job.start()
        job.future.result(timeout=2)
        for _ in range(120):
            self.assertTrue(job.ready())
        self.assertEqual(library.ads_verify_files.calls, 1)
        self.assertEqual(len(messages), 2)
        self.assertIn("store=Epic", messages[-1])

    def test_pending_does_not_read_or_log_a_profile(self):
        library = types.SimpleNamespace(ads_verify_files=Function(0), view_game_build=Function(2))
        messages = []
        job = BuildPreflight(library, messages.append)
        from time import perf_counter
        job.future, job._started = Future(), perf_counter()
        self.assertFalse(job.ready())
        self.assertEqual(library.view_game_build.calls, 0)
        self.assertEqual(messages, [])
        job.future.set_result((0, 1.0))
        self.assertTrue(job.ready())


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
