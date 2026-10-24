"""An Orbit entry is only asked with both views off: with one on, the frame's context is not read from the game."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.orbit_entry import OrbitEntry  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class CountedPC:
    """A player controller that counts the reads of its character, each one a trip into the game."""

    def __init__(self):
        self.reads = 0

    @property
    def OakCharacter(self):
        self.reads += 1
        return None


def client(third_person=False, orbit=False):
    settings = types.SimpleNamespace(third_person_enabled=lambda: third_person, orbit_enabled=lambda: orbit)
    return types.SimpleNamespace(owner="mod", settings=settings)


entry, pc = OrbitEntry(), CountedPC()
entry.observe(client(third_person=True), pc)
check("third person on: the context is not read", pc.reads == 0 and entry.context is None)
entry.observe(client(orbit=True), pc)
check("Orbit on: the context is not read either", pc.reads == 0 and entry.context is None)
entry.observe(client(), pc)
check("both views off: the context is read, where an entry can be asked", pc.reads == 1)

entry.pending = ("mod", (1, 2, 3))
entry.observe(client(third_person=True), pc)
check("an entry under way is checked against a fresh context whatever the settings say", pc.reads == 2)

older = types.SimpleNamespace(owner="mod", settings=types.SimpleNamespace())
entry.pending = None
entry.observe(older, pc)
check("a mod without these settings is read as before", pc.reads == 3)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
