"""Native boundary failures identify their stage and type without leaking exception text."""
import contextlib
import io
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from native_camera import check_outside_game


class OutsideGameTests(unittest.TestCase):
    def test_loader_exception_identifies_stage_and_type(self):
        output = io.StringIO()
        with patch.object(check_outside_game.sys, "argv", ["check", "C:/scratch/check.dll"]), \
                patch.object(check_outside_game.ctypes, "CDLL", side_effect=OSError("C:/private/secret.dll")), \
                contextlib.redirect_stdout(output):
            self.assertEqual(check_outside_game.main(), 1)
        self.assertIn("stage=load", output.getvalue())
        self.assertIn("error_type=OSError", output.getvalue())
        self.assertNotIn("private", output.getvalue())
        self.assertNotIn("secret", output.getvalue())

    def test_worker_failure_identifies_verification_without_exception_text(self):
        def verify():
            raise RuntimeError("C:/private/secret.dll")
        library = NS(ads_prepare=lambda: 1, ads_verify_files=verify)
        output = io.StringIO()
        with patch.object(check_outside_game.sys, "argv", ["check", "C:/scratch/check.dll"]), \
                patch.object(check_outside_game.ctypes, "CDLL", return_value=library), \
                contextlib.redirect_stdout(output):
            self.assertEqual(check_outside_game.main(), 1)
        self.assertIn("stage=verification", output.getvalue())
        self.assertIn("error_type=RuntimeError", output.getvalue())
        self.assertNotIn("private", output.getvalue())


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
