"""Anton and Barlow Condensed as Unreal fonts, built at runtime from the copied TTF files.

A font with a runtime cache reads its faces from file names, the path Slate's own core fonts take in a packaged
game. Rebuilt at each opening: the text widgets using a font are what keep it alive, nothing else holds it.
"""

import unrealsdk as sdk

from . import panel_assets as assets, panel_theme as t, panel_widgets as w

FACES = {
    "title": (("Regular", "Anton-Regular.ttf"),),
    "body": (("Medium", "BarlowCondensed-Medium.ttf"), ("SemiBold", "BarlowCondensed-SemiBold.ttf"),
             ("ExtraBold", "BarlowCondensed-ExtraBold.ttf")),
}
# The mockup's CSS weights, mapped to the Barlow files shipped; Anton has a single weight.
WEIGHTS = {t.WEIGHT_REGULAR: "Medium", t.WEIGHT_MEDIUM: "SemiBold", t.WEIGHT_BOLD: "ExtraBold"}


def build(outer):
    """Family -> font object. A family whose files or font class are unavailable is left out: engine font."""
    fonts = {}
    for family, faces in FACES.items():
        files = tuple((name, assets.path(file)) for name, file in faces)
        if any(path is None for _, path in files):
            continue
        made = []
        w.cosmetic(f"font:{family}", lambda files=files, made=made: made.append(_font(outer, files)))
        if made:
            fonts[family] = made[0]
    return fonts


def _font(outer, files):
    font = sdk.construct_object("Font", outer)
    font.FontCacheType = w.enum("EFontCacheType", "Runtime")
    composite = font.CompositeFont
    composite.DefaultTypeface.Fonts = [
        sdk.make_struct("TypefaceEntry", Name=name, Font=sdk.make_struct(
            "FontData", FontFilename=path, Hinting=w.enum("EFontHinting", "Default"),
            LoadingPolicy=w.enum("EFontLoadingPolicy", "LazyLoad"), SubFaceIndex=0))
        for name, path in files]
    # Written back whole, so the faces land whether the SDK handed out the struct or a copy of it.
    font.CompositeFont = composite
    return font


def face(family, weight):
    return "Regular" if family == "title" else WEIGHTS[weight]
