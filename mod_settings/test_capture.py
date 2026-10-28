# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of capture.py with a stand-in for the Windows calls. python test_capture.py"""

import copy
import sys
import threading
import time

import package_path  # noqa: F401  (before the package's modules)
import capture as key_capture
import protocol

BASE = protocol.load_constants()
FAILURES = []


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


class Keys:
    """Which virtual keys are down, and whether the game's window is in front."""

    def __init__(self, down=(), focused=True):
        self.down = set(down)
        self.in_front = focused
        self.lock = threading.Lock()

    def pressed(self, code):
        with self.lock:
            return code in self.down

    def focused(self):
        return self.in_front

    def set(self, *codes):
        with self.lock:
            self.down = set(codes)


def capture(keys, **settings):
    constants = copy.deepcopy(BASE)
    constants["capture"].update(settings)
    ends = []
    return key_capture.KeyCapture(constants, keys, lambda *end: ends.append(end)), ends


def wait_end(cap, seconds=2.0):
    limit = time.monotonic() + seconds
    while cap.status()[0] == "waiting" and time.monotonic() < limit:
        time.sleep(0.01)
    return cap.status()


VK = BASE["capture"]["keys"]

keys = Keys()
cap, ends = capture(keys)
check("starts", cap.start("sample_key"))
check("one capture at a time", not cap.start("sample_key"))
time.sleep(0.05)
keys.set(VK["F8"])
check("first key taken", wait_end(cap) == ("done", "F8"))
check("service told the key before the page can read it", ends == [("sample_key", "done", "F8")])

# The key that started the capture is still down: taken only once released and pressed again.
keys = Keys(down=[VK["Enter"]])
cap, ends = capture(keys)
cap.start("sample_key")
time.sleep(0.1)
check("held key ignored", cap.status() == ("waiting", None))
keys.set()
time.sleep(0.05)
keys.set(VK["Enter"])
check("held key taken after release", wait_end(cap) == ("done", "Enter"))

keys = Keys()
cap, ends = capture(keys)
cap.start("sample_key")
time.sleep(0.05)
keys.set(VK["Escape"])
check("escape cancels", wait_end(cap) == ("cancelled", None))
check("no key stored on cancel", ends == [("sample_key", "cancelled", None)])

keys = Keys(focused=False)
cap, _ = capture(keys)
cap.start("sample_key")
time.sleep(0.05)
keys.set(VK["Q"])
time.sleep(0.1)
check("keys of another window ignored", cap.status() == ("waiting", None))
cap.cancel()
check("cancel ends it", wait_end(cap) == ("cancelled", None))

keys = Keys()
cap, _ = capture(keys, maxSeconds=0.2)
cap.start("sample_key")
check("time limit ends it", wait_end(cap, 2.0) == ("timeout", None))
check("a new capture may start after the end", cap.start("sample_key"))
cap.cancel()
wait_end(cap)


class Broken(Keys):
    def pressed(self, code):
        raise OSError("no keyboard")


cap, _ = capture(Broken())
cap.start("sample_key")
check("an error ends it visibly", wait_end(cap) == ("failed", None))

print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
sys.exit(1 if FAILURES else 0)
