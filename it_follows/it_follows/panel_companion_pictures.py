"""The companions' pictures on their cards (spec-compagnons.md, « une image »; sketch A of docs/renforts/esquisses_menu,
chosen by Kevin: a square on the card's left), Kevin's own (docs/renforts/outils/companion_pictures_build.py).

They load each time their tab opens, as the starting points' do (panel_starts.py): a texture kept in Python is no hold
on it, the game may free it once its frame shows another, and drawing it then could crash the game (It Follows'
audit, 2026-10-19). One that does not load is hidden, never an empty frame (Kevin's rule of 2026-09-21): the card then
has its settings alone.
"""

from typing import Any

from mods_base import get_pc

from . import companion_pictures_data as data, panel_assets as assets, panel_theme as t, panel_widgets as w
from . import panel_window_size as size

# The square's side in the smallest window (1400 wide): 100 pushed +30 % about 25 past the card's edge (trial 195,
# Kevin's screenshot), the speeds' three buttons the widest of its settings. It grows with the window, 187 in the
# LARGE one, sketch A's, which held (trial 195); never past BIGGEST.
SIDE = 64
GROWTH = 0.425
BIGGEST = 240


def side() -> float:
    """The square's side in the window being drawn (panel_window_size.use, set before the pages)."""
    return float(min(BIGGEST, round(SIDE + (size.WIDTH - t.WINDOW_WIDTH) * GROWTH)))


def _visible(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible" if shown else "Collapsed"))


def frame(owner: Any, widgets: dict, name: str) -> Any:
    """The companion's square, hidden until its picture loads."""
    widgets[f"mate_picture:{name}"] = image = w.new("Image", owner)
    widgets[f"mate_picture_box:{name}"] = box = w.sized(owner, image, side(), side())
    _visible(box, False)
    return box


def load(form: Any, widgets: dict, tab: str, members: tuple) -> None:
    """The tab's pictures in their squares, once each time it opens; one that does not load hidden."""
    if getattr(form, "companions_loaded", None) == tab:
        return
    pc = get_pc()
    for kind in members:
        file = data.PICTURES.get(kind.name)
        texture = assets.texture(pc, file) if pc is not None and file is not None else None
        image = widgets[f"mate_picture:{kind.name}"]
        shown = texture is not None and w.cosmetic(f"mate_picture:{kind.name}", lambda image=image, texture=texture: (
            image.SetBrushFromTexture(texture, False)))
        _visible(widgets[f"mate_picture_box:{kind.name}"], shown)
    form.companions_loaded = tab
