"""Disk verification must never run on the camera caller or outlive its worker."""
import threading
from concurrent.futures import Future
import unittest
from unittest.mock import patch
from apex_camera_runtime.ads_bridge import AdsBridge
from test_ads_bridge import Function
from types import SimpleNamespace as NS


class PreflightTests(unittest.TestCase):
    def bridge(self, verify, prepare=lambda: 0, log=lambda _message: None):
        library = NS(**{name: Function(lambda *_: 0) for name in
                     ("ads_identify", "ads_publish", "ads_clear", "ads_release", "ads_stats")})
        library.ads_verify_files, library.ads_prepare = Function(verify), Function(prepare)
        return AdsBridge(library, log)

    def test_pending_disk_io_does_not_install_hooks_or_block_the_caller(self):
        entered, release = threading.Event(), threading.Event()
        workers, installers = [], []
        def verify():
            workers.append(threading.current_thread())
            entered.set()
            if not release.wait(2):
                raise RuntimeError("Test verification was not released")
            return 0
        bridge = self.bridge(verify, lambda: installers.append(threading.get_ident()) or 0)
        self.assertTrue(callable(getattr(bridge, "start_preflight", None)))
        try:
            bridge.start_preflight()
            self.assertTrue(entered.wait(2))
            for _ in range(10):
                self.assertIsNone(bridge.prepare())
                bridge.start_preflight()
            self.assertEqual(installers, [])
        finally:
            release.set()
        bridge._preflight.future.result(timeout=2)
        self.assertTrue(bridge.prepare())
        self.assertTrue(bridge.prepare())
        self.assertEqual(installers, [threading.get_ident()])
        self.assertEqual(len(workers), 1)
        self.assertNotEqual(workers[0].ident, threading.get_ident())
        workers[0].join(2)
        self.assertFalse(workers[0].is_alive())

    def test_failure_or_exception_is_terminal_and_never_installs(self):
        def broken():
            raise OSError("private path must not escape")
        for verify in (lambda: 1, broken):
            installed = []
            bridge = self.bridge(verify, lambda: installed.append(True) or 0)
            bridge.start_preflight()
            try:
                bridge._preflight.future.result(timeout=2)
            except OSError:
                pass  # Production prepare must turn this worker failure into a safe refusal.
            for _ in range(3):
                self.assertFalse(bridge.prepare())
            self.assertEqual(installed, [])

    def test_worker_creation_failure_is_terminal_without_a_synchronous_fallback(self):
        called = []
        bridge = self.bridge(lambda: called.append("disk"), lambda: called.append("hooks"))
        with patch("apex_camera_runtime.ads_preflight.ThreadPoolExecutor", side_effect=RuntimeError):
            bridge.start_preflight()
        for _ in range(3):
            self.assertFalse(bridge.prepare())
        self.assertEqual(called, [])

    def test_native_installation_failure_is_not_retried_after_successful_verification(self):
        installed = []
        bridge = self.bridge(lambda: 0, lambda: installed.append(True) or 1)
        bridge.start_preflight()
        bridge._preflight.future.result(timeout=2)
        for _ in range(3):
            self.assertFalse(bridge.prepare())
        self.assertEqual(installed, [True])

    def test_timeout_is_terminal_even_when_the_worker_later_succeeds(self):
        entered, release = threading.Event(), threading.Event()
        installed, logs = [], []
        def verify():
            entered.set()
            if not release.wait(2):
                raise RuntimeError("Test worker not released")
            return 0
        bridge = self.bridge(verify, lambda: installed.append(True) or 0, logs.append)
        with patch("apex_camera_runtime.ads_preflight.perf_counter", return_value=0):
            bridge.start_preflight()
        try:
            self.assertTrue(entered.wait(2))
            with patch("apex_camera_runtime.ads_preflight.perf_counter", return_value=20):
                self.assertIsNone(bridge.prepare())
            with patch("apex_camera_runtime.ads_preflight.perf_counter", return_value=60):
                for _ in range(3):
                    self.assertIs(bridge.prepare(), False)
            self.assertEqual(installed, [])
            self.assertEqual(len(logs), 1)
            self.assertIn("timeout", logs[0])
        finally:
            release.set()
        bridge._preflight.future.result(timeout=2)
        self.assertFalse(bridge.prepare())
        self.assertEqual(installed, [])

    def test_worker_and_install_exceptions_log_types_without_private_details(self):
        def broken():
            raise OSError("C:/private/secret.dll")
        for verify, install, expected_stage in ((broken, lambda: 0, "verification"),
                                                 (lambda: 0, broken, "installation")):
            with self.subTest(stage=expected_stage):
                logs = []
                bridge = self.bridge(verify, install, logs.append)
                bridge.start_preflight()
                try:
                    bridge._preflight.future.result(timeout=2)
                except OSError:
                    pass
                for _ in range(3):
                    self.assertFalse(bridge.prepare())
                details = [message for message in logs if "OSError" in message]
                self.assertEqual(len(details), 1)
                self.assertIn(expected_stage, details[0])
                self.assertFalse(any("private" in message or "secret" in message for message in logs))

    def test_delayed_worker_cannot_escape_the_global_startup_budget(self):
        installed = []
        bridge = self.bridge(lambda: 0, lambda: installed.append(True) or 0)
        preflight = bridge._preflight
        preflight._started = 0
        with patch("apex_camera_runtime.ads_preflight.perf_counter", side_effect=[30, 31]):
            result = preflight._run()
        preflight.future = Future()
        preflight.future.set_result(result)
        with patch("apex_camera_runtime.ads_preflight.perf_counter", return_value=31):
            self.assertFalse(bridge.prepare())
        self.assertEqual(installed, [])
        self.assertEqual(preflight.failure, "verification_timeout")

    def test_fast_verification_is_not_refused_just_because_polling_is_late(self):
        installed = []
        bridge = self.bridge(lambda: 0, lambda: installed.append(True) or 0)
        preflight = bridge._preflight
        preflight._started = 0
        with patch("apex_camera_runtime.ads_preflight.perf_counter", side_effect=[1, 2]):
            result = preflight._run()
        preflight.future = Future()
        preflight.future.set_result(result)
        with patch("apex_camera_runtime.ads_preflight.perf_counter", return_value=31):
            self.assertTrue(bridge.prepare())
        self.assertEqual(installed, [True])

    def test_absent_native_error_code_is_not_diagnosed_as_invalid(self):
        logs = []
        bridge = self.bridge(lambda: 0, log=logs.append)
        preflight = bridge._preflight
        preflight.start()
        preflight.future.result(timeout=2)
        self.assertTrue(bridge.prepare())
        self.assertIn('native_status=none', logs[0])
        logs.clear()
        bridge = self.bridge(lambda: 0, log=logs.append)
        preflight = bridge._preflight
        preflight._started = 0
        preflight.future = Future()
        with patch('apex_camera_runtime.ads_preflight.perf_counter', return_value=31):
            self.assertFalse(bridge.prepare())
        self.assertIn('native_status=none', logs[0])


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
