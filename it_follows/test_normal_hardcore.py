"""Tests the Hardcore's count (normal/hardcore.py): nothing at first, off, a factor of 1; on, 99 kills then one more
reach the first step, written at once; paused or off, no kill counted and the percent kept, applied while paused and
not while off, the same once on again; a write only when the kills changed; a write that fails said, the kills kept
and written at the next one; the count bounded; the file read tolerantly, each wrong value counting 0 and said; a
later version's record never counted on nor written over."""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import it_follows  # noqa: E402
from it_follows import report  # noqa: E402
from it_follows.normal import hardcore, options  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes() -> list[dict]:
    lines = [json.loads(text.split(" ", 2)[2]) for text in state["info"] if text.startswith(report.PREFIX + " {")]
    state["info"].clear()
    return lines


def switches(on: bool, progress: bool) -> None:
    options.hardcore.value, options.progress.value = on, progress


try:
    check("a step every 100 kills, Kevin's", hardcore.KILLS_PER_STEP == 100)
    mod = it_follows.mod
    # What the file was given at each write: the SDK's own writer has no file in the tests.
    writes: list[dict] = []
    mod.save_settings = lambda: writes.append(dict(hardcore.option.value))
    check("read at the mod's start: no kill, off", [line for line in notes() if line["event"] == "hardcore_read"]
          == [{"event": "hardcore_read", "run": 0, "kills": 0, "percent": 0, "state": "off"}])
    check("off at first, its progress on at first", options.hardcore.value is False and options.progress.value is True
          and hardcore.state() == "off" and hardcore.factor() == 1.0)
    check("off: no kill counted", hardcore.count(50) is None and hardcore.kills() == 0)
    switches(True, True)
    check("on: nothing changes at once", hardcore.state() == "on" and hardcore.factor() == 1.0)
    check("99 kills: no step, nothing written", hardcore.count(99) is None and hardcore.kills() == 99
          and writes == [] and notes() == [])
    check("one more: the first step, written at once", hardcore.count(1) == 1 and hardcore.factor() == 1.01
          and writes == [{"version": 1, "kills": 100}]
          and notes() == [{"event": "hardcore_saved", "run": 0, "why": "step", "kills": 100, "percent": 1}])
    check("no kill, nothing counted", hardcore.count(0) is None and hardcore.count(-3) is None
          and hardcore.kills() == 100)
    check("a write when nothing changed writes nothing", hardcore.save("end") is True and len(writes) == 1)
    hardcore.count(137)
    check("237 kills: 2 %", hardcore.percent() == 2 and hardcore.factor() == 1.02)
    switches(True, False)
    check("paused: the percent applied, no kill counted", hardcore.state() == "paused" and hardcore.factor() == 1.02
          and hardcore.count(500) is None and hardcore.kills() == 237)
    switches(False, False)
    check("off: nothing applied, the percent kept", hardcore.factor() == 1.0 and hardcore.percent() == 2
          and hardcore.count(500) is None)
    switches(True, True)
    check("on again: the same percent", hardcore.factor() == 1.02 and hardcore.kills() == 237)

    def refused() -> None:
        raise OSError("disk full")

    counting, mod.save_settings = mod.save_settings, refused
    notes()
    check("a write that fails is said, the kills kept", hardcore.count(63) == 3 and hardcore.kills() == 300
          and notes() == [{"event": "hardcore_not_saved", "run": 0, "why": "step", "error": "OSError"}])
    mod.save_settings = counting
    check("and written at the next write", hardcore.save("end") is True and writes[-1] == {"version": 1, "kills": 300})
    hardcore.count(hardcore.MOST_KILLS)
    check("the count bounded", hardcore.kills() == hardcore.MOST_KILLS and hardcore.percent() == 10000)

    for value, wrong in (({"version": 1, "kills": 1234}, None), ({}, None), ("lots", "not_a_record"),
                         ({"version": 2, "kills": 5}, "newer_version"),
                         ({"version": "1", "kills": 5}, "unknown_version"),
                         ({"version": 0, "kills": 5}, "unknown_version"), ({"version": 1, "kills": -4}, "bad_kills"),
                         ({"version": 1, "kills": 7.5}, "bad_kills"), ({"version": 1, "kills": True}, "bad_kills"),
                         ({"version": 1, "kills": hardcore.MOST_KILLS + 1}, "bad_kills"),
                         ({"version": 1}, "bad_kills")):
        hardcore.option.value = value
        notes()
        hardcore.load()
        said = notes()[0]
        expected = 1234 if wrong is None and value else 0
        check(f"read {value!r}: {expected} kills, {wrong or 'nothing wrong'}", hardcore.kills() == expected
              and said.get("wrong") == wrong and said["kills"] == expected)
    written = len(writes)
    check("a value read is not written again", hardcore.save("end") is True and len(writes) == written)
    newer = {"version": 2, "games": {"a": 340}}
    hardcore.option.value = dict(newer)
    hardcore.load()
    switches(True, True)
    check("a later version's record: no kill counted, nothing written over it, the factor 1",
          hardcore.count(500) is None and hardcore.save("status") is True and hardcore.save("end") is True
          and hardcore.option.value == newer and len(writes) == written and hardcore.factor() == 1.0)
    hardcore.option.value = {"version": 1, "kills": 5}
    hardcore.load()
    check("this version's record again: counted again", hardcore.count(95) == 1 and writes[-1]["kills"] == 100)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
