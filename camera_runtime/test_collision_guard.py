"""A camera obstruction suspends the shoulder shift until the path is stably clear."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.collision import CollisionGuard  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class SDK:
    @staticmethod
    def make_struct(name, **values):
        return types.SimpleNamespace(kind=name, **values)


class Kismet:
    def __init__(self, answers):
        self.answers = iter(answers)
        self.calls = 0

    def LineTraceSingle(self, *_args):
        self.calls += 1
        answer = next(self.answers)
        if isinstance(answer, Exception):
            raise answer
        return answer


class Bridge:
    def stats(self):
        return types.SimpleNamespace(before=(10.0, 20.0, 30.0), after=(10.0, 55.0, 35.0))


clear = (False, [], types.SimpleNamespace())
wall = (True, [], types.SimpleNamespace(Distance=12.0))
kismet = Kismet([wall, clear, clear, clear, RuntimeError("trace unavailable")])
notes, states = [], []
guard = CollisionGuard(kismet, SDK, notes.append, clear_samples=3)
for now in (50_000_000, 100_000_000, 150_000_000, 200_000_000):
    guard.sample(now, object(), Bridge(), states.append)
check("a hit suspends the offset immediately", states[0] is True)
check("three clear samples are required before resuming", states == [True, False])
guard.sample(210_000_000, object(), Bridge(), states.append)
check("sampling is rate limited", kismet.calls == 4)
guard.sample(250_000_000, object(), Bridge(), states.append)
check("a trace error fails closed", states[-1] is True and any("collision check failed" in note for note in notes))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
