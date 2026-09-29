"""The window's files copied out of the mod: written through file_replace into the settings folder, whole, no temporary
file left; the same content on disk not written again at the next session; other content written again; a failed
write giving no file and said once."""

import sys
from pathlib import Path

import sdk_stubs

state = sdk_stubs.install()

from hunter_change import file_replace, panel_assets, report  # noqa: E402

fails: list[str] = []
written: list[str] = []
real_replace = file_replace.replace


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def replace(target: Path, data: bytes) -> None:
    written.append(target.name)
    real_replace(target, data)


def new_session() -> None:
    panel_assets._copied.clear()


file_replace.replace = replace
name = panel_assets.AVATAR
shipped = (Path(panel_assets.__file__).with_name("assets") / name).read_bytes()

copied = Path(panel_assets.path(name))
check("written through file_replace into the settings folder, whole, no temporary file left",
      written == [name] and copied == state["settings_dir"] / panel_assets.FOLDER / name
      and copied.read_bytes() == shipped
      and not copied.with_name(copied.name + file_replace.TEMPORARY_SUFFIX).exists())

new_session()
check("the same content on disk not written again", panel_assets.path(name) == str(copied) and written == [name])

copied.write_bytes(b"older copy")
new_session()
panel_assets.path(name)
check("other content on disk written again", written == [name, name] and copied.read_bytes() == shipped)

font = panel_assets.FONTS[0]
blocked = copied.with_name(font)
blocked.with_name(blocked.name + file_replace.TEMPORARY_SUFFIX).mkdir()
report.reset()
state["errors"].clear()
check("a failed write giving no file and said once", panel_assets.path(font) is None and panel_assets.path(font) is None
      and len(state["errors"]) == 1 and font in state["errors"][0] and not blocked.exists())

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
