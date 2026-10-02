# Generated: the settings window Kevin's mods share, taken from Apex Heirloom's and put under this mod's names.
# Its comments may speak of that mod. Never edited by hand: the window's generator writes this file.
"""A page's pictures, right of its title, description and sentence: on HEIRLOOM the heirloom chosen, where Kevin marked
the knife on the window (2026-09-26). Since the axe (sketch H2, 2026-09-29), one picture per heirloom: the one the
window's values choose shows, the others are collapsed. Which page shows which files, at what size, and which one is
chosen, is menu.PICTURES; the files ship in assets/ and load as the avatar does (panel_assets.py, verified in game).

A picture that does not load leaves no empty frame: without any, the head takes the card's width, as before; the
chosen one missing, none shows (Kevin's rule of 2026-09-21, working or invisible).
"""

from . import menu, panel_assets as assets, panel_theme as t, panel_widgets as w


def _loaded(rows, key, world, pictures):
    """The page's pictures that load, each as (choice, image, width, height)."""
    found = []
    for choice, (name, width, height) in pictures.items():
        texture = assets.texture(world, name)
        if texture is None:
            continue
        image = w.new("Image", rows)
        if w.cosmetic(f"picture:{key}:{choice}", lambda image=image, texture=texture:
                      image.SetBrushFromTexture(texture, False)):
            found.append((choice, image, width, height))
    return found


def head(rows, widgets, key, world):
    """Where the card of page `key` puts its title, description and sentence: `rows` itself, or the left of a line of
    `rows` whose right holds the page's pictures, one over the other. `world` loads the textures; None, as for the
    CONTROLS card, loads none."""
    known = menu.PICTURES.get(key)
    if known is None or world is None:
        return rows
    found = _loaded(rows, key, world, known[1])
    if not found:
        return rows
    line = w.new("HorizontalBox", rows)
    left = w.new("VerticalBox", line)
    w.row(line, left, fill=True, valign="Top")
    stack = w.new("Overlay", line)
    for choice, image, width, height in found:
        box = w.sized(stack, image, width, height)
        w.layer(stack, box)
        widgets[f"picture:{key}:{choice}"], widgets[f"picture_box:{key}:{choice}"] = image, box
    w.row(line, stack, padding=w.pad(0, 0, 0, t.SPACE_5), valign="Center")
    w.column(rows, line)
    return left


def show(widgets, shown):
    """Each page's picture of the choice the window's values make, the others collapsed."""
    for key, (choose, pictures) in menu.PICTURES.items():
        chosen = choose(shown)
        for choice in pictures:
            box = widgets.get(f"picture_box:{key}:{choice}")
            if box is not None:
                state = "HitTestInvisible" if choice == chosen else "Collapsed"
                box.SetVisibility(w.enum("ESlateVisibility", state))
