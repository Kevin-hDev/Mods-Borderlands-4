"""Tests which update notes open (updates.py): those newer than the version seen and not newer than the one installed,
the newest first; none seen, or one that is no version, all up to the one installed; the one installed seen, none;
1.0.10 after 1.0.9; a version read by its numbers."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import release_notes, updates  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def note(version: str) -> tuple:
    return version, {"en": (f"Line of {version}.",), "fr": (f"Ligne de {version}.",)}


NOTES = tuple(note(version) for version in ("1.0.10", "1.0.9", "1.0.4", "1.0.3", "1.0.2", "1.0.1"))


def versions(found: list) -> list[str]:
    return [version for version, _texts in found]


try:
    check("read by its numbers", updates.key("1.0.10") == (1, 0, 10) and updates.key("2") == (2,)
          and updates.key("abc") is None and updates.key("") is None and updates.key(None) is None
          and updates.key("1..2") is None)
    check("the notes shipped: a tuple, the newest first", isinstance(release_notes.NOTES, tuple)
          and [updates.key(v) for v, _ in release_notes.NOTES]
          == sorted((updates.key(v) for v, _ in release_notes.NOTES), reverse=True))
    updates.seen.value = "1.0.1"
    check("newer than the one seen, the newest first", versions(updates.due("1.0.4", NOTES))
          == ["1.0.4", "1.0.3", "1.0.2"])
    check("never newer than the one installed", versions(updates.due("1.0.3", NOTES)) == ["1.0.3", "1.0.2"])
    check("each with its texts", updates.due("1.0.2", NOTES) == [note("1.0.2")])
    updates.seen.value = "1.0.4"
    check("the one installed seen: none", updates.due("1.0.4", NOTES) == [])
    updates.seen.value = "1.0.9"
    check("1.0.10 after 1.0.9", versions(updates.due("1.0.10", NOTES)) == ["1.0.10"])
    for value in ("", "abc", None, 3):
        updates.seen.value = value
        check(f"none seen or no version ({value!r}): all up to the one installed",
              versions(updates.due("1.0.4", NOTES)) == ["1.0.4", "1.0.3", "1.0.2", "1.0.1"])
    updates.seen.value = ""
    check("an installed version that is no version: none", updates.due("dev", NOTES) == [])
    check("the shipped notes by default", updates.due("1.0.1") == [entry for entry in release_notes.NOTES
                                                                     if updates.key(entry[0]) <= (1, 0, 1)])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
