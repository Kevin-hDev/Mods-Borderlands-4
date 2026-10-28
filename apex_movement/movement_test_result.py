"""Fail-closed test result; its two local copies are verified byte for byte."""

import atexit
import os
import sys


class Reporter:
    def __init__(self, label: str) -> None:
        self.label = label
        self.passed = False
        atexit.register(self._write)

    def success(self) -> None:
        self.passed = True

    def _write(self) -> None:
        state = "OK" if self.passed else "ECHEC"
        print(f"RESULTAT: {state} | {self.label}", flush=True)
        if not self.passed:
            sys.stderr.flush()
            os._exit(1)
