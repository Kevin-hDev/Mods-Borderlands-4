"""The mockup's fonts become runtime Unreal fonts from their copied files; a missing file keeps the engine font."""

import sys
import control_fixture as f
import panel_render_fixture as fixture
import unrealsdk
from apex_grapple import panel_assets, panel_fonts, panel_theme as t

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


fixture.install()
paths = {name: f"C:/game/settings/{name}" for name in panel_assets.FONTS}
panel_assets.path = lambda name: paths.get(name)
fonts = panel_fonts.build("outer")
check(set(fonts) == {"title", "body"}, "Both families are built")
title, body = fonts["title"], fonts["body"]
check(title.kind == "Font" and title.owner == "outer", "A font object owned by the window")
check(title.FontCacheType == "EFontCacheType.Runtime", "Runtime cache: faces are read from their files")
entries = title.CompositeFont.DefaultTypeface.Fonts
check([entry.Name for entry in entries] == ["Regular"], "Anton has a single face")
check(entries[0].Font.FontFilename == paths["Anton-Regular.ttf"], "The face points at the copied file")
check(entries[0].Font.LoadingPolicy == "EFontLoadingPolicy.LazyLoad", "Loaded into memory, not streamed")
check([entry.Name for entry in body.CompositeFont.DefaultTypeface.Fonts] == ["Medium", "SemiBold", "ExtraBold"],
      "Barlow carries the mockup's three weights")
check(panel_fonts.face("body", t.WEIGHT_BOLD) == "ExtraBold" and panel_fonts.face("title", None) == "Regular",
      "CSS weights map to the shipped faces")
paths.pop("BarlowCondensed-ExtraBold.ttf")
check(set(panel_fonts.build("outer")) == {"title"}, "A family missing one file falls back to the engine font")
construct = unrealsdk.construct_object


def refuse(kind, owner):
    if kind == "Font":
        raise AttributeError("no Font class")
    return construct(kind, owner)


unrealsdk.construct_object = refuse
check(panel_fonts.build("outer") == {}, "A game without runtime fonts keeps the engine font")
check(sum("'font:title'" in line for line in f.state["errors"]) == 1, "and says so once")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | runtime fonts from copied files, engine font fallback")
sys.exit(1 if failures else 0)
