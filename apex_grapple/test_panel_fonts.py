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
# Apex Grapple offers Chinese (2026-10-13); the windows generated from it without Chinese are played first.
panel_fonts.LANGUAGES = ("EN", "FR")
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


def fallback(font):
    # The fixture's structs make up any field read; a fallback never written has no list of faces.
    faces = font.CompositeFont.FallbackTypeface.Typeface.Fonts
    return [(entry.Name, entry.Font.FontFilename) for entry in faces] if isinstance(faces, list) else []


check(not fallback(title) and not fallback(body), "A mod not offering Chinese builds no Chinese fallback")
panel_fonts.LANGUAGES = ("EN", "FR", "ZH")
fonts = panel_fonts.build("outer")
check(fallback(fonts["title"]) == [("Black", paths["NotoSansSC-Black.ttf"])], "Titles: Noto Sans SC Black")
check(fallback(fonts["body"]) == [("Medium", paths["NotoSansSC-Medium.ttf"]),
                                  ("ExtraBold", paths["NotoSansSC-ExtraBold.ttf"])], "Body: Medium and ExtraBold")
check(fonts["body"].CompositeFont.FallbackTypeface.ScalingFactor == 1.0, "Chinese at the Latin size")
body_faces = [entry.Name for entry in fonts["body"].CompositeFont.DefaultTypeface.Fonts]
check(body_faces == ["Medium", "SemiBold", "ExtraBold"], "Barlow stays the font: Chinese is only the fallback")
paths.pop("NotoSansSC-Medium.ttf")
fonts = panel_fonts.build("outer")
check(set(fonts) == {"title", "body"} and not fallback(fonts["body"]) and fallback(fonts["title"]),
      "A missing Chinese file costs the fallback, never the Latin font")
panel_fonts.LANGUAGES = ("EN", "FR")
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
