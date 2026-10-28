"""Window files leave the package whole and once; anything unexpected is refused, reported once, and hidden."""

import contextlib
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import control_fixture as f
import mods_base
from apex_grapple import panel_assets as a

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


root = Path(tempfile.mkdtemp())
font, picture = b"\x00\x01\x00\x00" + b"f" * 100, b"\x89PNG\r\n\x1a\n" + b"p" * 50
store = {"Anton-Regular.ttf": font, "avatar.png": picture,
         "BarlowCondensed-Medium.ttf": b"<html>not a font</html>",
         "BarlowCondensed-SemiBold.ttf": b"\x00\x01\x00\x00" + b"z" * a.MAX_BYTES}


@contextlib.contextmanager
def open_in_mod_dir(path, binary=False):
    check(binary and Path(path).parent.name == "assets", "Assets are read in binary from the package's folder")
    if Path(path).name not in store:
        raise FileNotFoundError(Path(path).name)
    yield io.BytesIO(store[Path(path).name])


mods_base.open_in_mod_dir, mods_base.SETTINGS_DIR = open_in_mod_dir, root
target = root / a.FOLDER / "Anton-Regular.ttf"
check(a.path("Anton-Regular.ttf") == str(target) and target.read_bytes() == font, "The font is copied whole")
check(not list(target.parent.glob("*.tmp")), "No temporary file is left behind")
stamp = target.stat().st_mtime_ns
a._copied.clear()
check(a.path("Anton-Regular.ttf") == str(target) and target.stat().st_mtime_ns == stamp,
      "An identical copy is not rewritten at the next session")
for name, reason in (("BarlowCondensed-Medium.ttf", "a file that is not a font"),
                     ("BarlowCondensed-SemiBold.ttf", "a file over the size bound"),
                     ("BarlowCondensed-ExtraBold.ttf", "a file missing from the package")):
    check(a.path(name) is None and not (root / a.FOLDER / name).exists(), f"Refused: {reason}")
errors = len(f.state["errors"])
check(errors == 3, "Each refusal is reported")
a.path("BarlowCondensed-Medium.ttf")
check(len(f.state["errors"]) == errors, "A refused file is not retried or reported again in the session")
try:
    a.path("../settings.json")
    failures.append("Only the shipped names are accepted")
except ValueError:
    pass
loaded = []
f.state["extra_classes"]["KismetRenderingLibrary"] = NS(ClassDefaultObject=NS(
    ImportFileAsTexture2D=lambda world, file: loaded.append((world, file)) or "texture"))
check(a.texture("world") == "texture" and loaded == [("world", str(root / a.FOLDER / "avatar.png"))],
      "The avatar is imported by Unreal from the copied file")
f.state["extra_classes"]["KismetRenderingLibrary"] = NS(ClassDefaultObject=NS(ImportFileAsTexture2D=lambda *_: None))
check(a.texture("world") is None, "No texture, no avatar")
del f.state["extra_classes"]["KismetRenderingLibrary"]
check(a.texture("world") is None and any("'avatar'" in line for line in f.state["errors"]),
      "An importer missing from the game hides the avatar and says so")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | window assets: whole copies, bounds, signatures, avatar")
sys.exit(1 if failures else 0)
