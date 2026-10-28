"""Tests the settings upgrade: a file saved before the third-person auto sprint switch keeps auto sprint in third
person when it was on; a new install, a file that already has the switch, or an unreadable file changes nothing."""

import json
import pathlib
import sys
import tempfile
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_movement.settings_upgrade import apply, keeps_third_person  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def saved(group: dict) -> dict:
    return {"enabled": True, "options": {"auto_sprint_menu": group}}


check("auto sprint saved on, before the switch: kept in third person",
      keeps_third_person(saved({"auto_sprint": True})))
check("auto sprint saved off: nothing kept", not keeps_third_person(saved({"auto_sprint": False})))
check("a file that already has the switch: the player's choice stands",
      not keeps_third_person(saved({"auto_sprint": True, "auto_sprint_third_person": False})))
check("a file without the auto sprint group, or not a settings file: nothing",
      not keeps_third_person({"options": {}}) and not keeps_third_person([]) and not keeps_third_person(None)
      and not keeps_third_person({"options": {"auto_sprint_menu": 3}}))

option = types.SimpleNamespace(value=False)
with tempfile.TemporaryDirectory() as folder:
    path = pathlib.Path(folder) / "apex_movement.json"
    check("a new install, no file: the default stays", apply(path, option) is False and option.value is False)
    check("no settings file at all: the default stays", apply(None, option) is False and option.value is False)
    path.write_text("{ not json", encoding="utf-8")
    check("an unreadable file: left to the mod's own loading", apply(path, option) is False and option.value is False)
    path.write_text(json.dumps(saved({"auto_sprint": True})), encoding="utf-8")
    check("a player's file from before with auto sprint on: on in third person",
          apply(path, option) is True and option.value is True)
    option.value = False
    path.write_text(json.dumps(saved({"auto_sprint": True, "auto_sprint_third_person": False})), encoding="utf-8")
    check("a file saved after: nothing changed", apply(path, option) is False and option.value is False)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
