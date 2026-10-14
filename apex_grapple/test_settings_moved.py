"""Tests settings_moved.py on Kevin's real settings file of 1.0.9 (fixtures/settings_1_0_9.json, copied on 2026-10-14):
"Show the rope", off under the shot's line, stays off at its new place on the look's line; a file saved at the new
place is left as it is; an unreadable file leaves the values and is said once, without its content."""

import json
import pathlib
import shutil
import sys
import tempfile
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import menu, settings, settings_moved  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


folder = pathlib.Path(tempfile.mkdtemp())
mod = types.SimpleNamespace(settings_file=folder / "apex_grapple.json")
try:
    shutil.copyfile(HERE / "fixtures" / "settings_1_0_9.json", mod.settings_file)
    check("Kevin's 1.0.9 file holds the rope off under the shot's line",
          json.loads(mod.settings_file.read_text(encoding="utf-8"))["options"]["shot_menu"]["show_rope"] is False)
    check("the menu names the move of the rope's switch to the look's line",
          menu.MOVED == ((settings.show_rope, "shot_menu", "look_menu"),))
    settings.show_rope.value = True
    taken = settings_moved.adopt(mod, menu.MOVED)
    check("the rope stays off, taken from its former line, and the log says so",
          taken == ["show_rope"] and settings.show_rope.value is False
          and any("show_rope" in line for line in state["misc"]))

    written = json.loads(mod.settings_file.read_text(encoding="utf-8"))
    written["options"]["look_menu"] = {"show_rope": True}
    mod.settings_file.write_text(json.dumps(written), encoding="utf-8")
    settings.show_rope.value = True
    check("a file already saved at the new place is left to mods_base",
          settings_moved.adopt(mod, menu.MOVED) == [] and settings.show_rope.value is True)

    mod.settings_file.write_text("{ not json", encoding="utf-8")
    before = len(state["warnings"])
    check("an unreadable file takes nothing", settings_moved.adopt(mod, menu.MOVED) == []
          and settings.show_rope.value is True)
    check("and says so, without its content", len(state["warnings"]) == before + 1
          and "not json" not in state["warnings"][-1])

    mod.settings_file.write_text(json.dumps({"options": ["shot_menu"]}), encoding="utf-8")
    check("a file whose options are not a table takes nothing", settings_moved.adopt(mod, menu.MOVED) == [])
    mod.settings_file.unlink()
    check("no file, nothing to take", settings_moved.adopt(mod, menu.MOVED) == [])
finally:
    shutil.rmtree(folder)
    settings.show_rope.value = settings.show_rope.default_value

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
