"""The bar at the top left of the screen that shows a run's kills, deaths and time while the player plays (decision
50), taken from trial 9's (docs/RUN/sondes/run_bar.py; docs/RUN/enquetes/2026-10-14-barre-en-jeu.md).

Built as BL4 Arena builds its window, which works in game: UMG widgets made at runtime under the player's controller,
put over the whole screen by GameViewportSubsystem.AddWidget, HitTestInvisible so that the game's own menus under it
still take their clicks. Trial 9 saw it stay while the player plays, keep up with each second and survive a fast travel;
but the game freed its widgets about once a minute, nothing holding them. Here they are rooted in the WidgetTree of a
UserWidget, which the game keeps for as long as it is on the screen: BL4 Arena's window learned it on 2026-09-21, after
the garbage collector took it 35 and 50 s after it opened (bl4_arena/panel_modal.py, held). Non vérifié for the bar:
trial 10 checks it. A bar the game took off with its world, or freed, is built again at the next second (keep).
"""

from itertools import islice
from typing import Any, Callable

import unrealsdk

# Under BL4 Arena's window (10000), so that a mod's menu covers the bar.
ZORDER = 5000
# From the screen's top and left edges, and inside the band, in pixels.
MARGIN_PX = 16.0
BAND_PADDING_PX = (6.0, 12.0)
# Trial 9 wrote 15 points; Kevin, after it: a little bigger by default, and three sizes in the menu (decision 52):
# the run gives the size chosen (options.BAR_SIZES), this one when none is given.
TEXT_POINTS = 19.0
BAND_RGBA = (0.0, 0.0, 0.0, 0.55)
TEXT_RGBA = (1.0, 1.0, 1.0, 1.0)
# How many screen subsystems are looked through for the one in play (BL4 Arena's window: 32).
MAX_INSTANCES = 32


def viewport() -> Any:
    """The screen's widget subsystem in play, None when the game has none."""
    return next((one for one in islice(unrealsdk.find_all("GameViewportSubsystem"), MAX_INSTANCES)
                 if not str(one.Name).startswith("Default__")), None)


def _enum(name: str, member: str) -> Any:
    return getattr(unrealsdk.find_enum(name), member)


def _colour(rgba: tuple[float, float, float, float]) -> Any:
    red, green, blue, alpha = rgba
    return unrealsdk.make_struct("LinearColor", R=red, G=green, B=blue, A=alpha)


def _margin(top: float, side: float) -> Any:
    return unrealsdk.make_struct("Margin", Left=side, Top=top, Right=side, Bottom=top)


def _vector(x: float, y: float) -> Any:
    return unrealsdk.make_struct("Vector2D", X=x, Y=y)


def _slot() -> Any:
    """The whole screen, as BL4 Arena's window takes it; the bar sits in its top left corner."""
    whole = unrealsdk.make_struct("Anchors", Minimum=_vector(0.0, 0.0), Maximum=_vector(1.0, 1.0))
    return unrealsdk.make_struct("GameViewportWidgetSlot", ZOrder=ZORDER, bAutoRemoveOnWorldRemoved=True,
                                 Alignment=_vector(0.0, 0.0), Anchors=whole, Offsets=_margin(0.0, 0.0))


def _live(pointer: Any) -> Any:
    return pointer() if pointer is not None else None


class Bar:
    """The bar's holder on the screen and its words, held weakly. announce(call, log=True, **fields) writes each call
    to the game down before it is made: the last line before a crash names it."""

    def __init__(self, announce: Callable[..., None], points: float = TEXT_POINTS) -> None:
        self.announce, self.points = announce, points
        self.holder = self.words = self.screen = None

    def show(self, pc: Any, text: str) -> str:
        """Builds a bar under pc showing text and puts it on the screen: "shown", or what kept it off."""
        step = "viewport"
        try:
            screen = viewport()
            if screen is None:
                return "no_viewport"
            step = "build"
            self.announce("construct_object", widgets="UserWidget,WidgetTree,Overlay,Border,TextBlock")
            holder = unrealsdk.construct_object("UserWidget", pc)
            holder.bIsFocusable = False
            tree = unrealsdk.construct_object("WidgetTree", holder)
            holder.WidgetTree = tree
            layer = unrealsdk.construct_object("Overlay", holder)
            tree.RootWidget = layer
            band = unrealsdk.construct_object("Border", layer)
            words = unrealsdk.construct_object("TextBlock", band)
            self._style(holder, layer, band, words, text, self.points)
            step = "add"
            self.announce("AddWidget", zorder=ZORDER)
            # Read as BL4 Arena's window reads it: a strict "is True" would take an answer of another shape for a
            # refusal, and a bar on the screen would be built again at every second.
            if not screen.AddWidget(holder, _slot()):
                return "refused"
        except Exception as error:
            return f"{step}_failed:{type(error).__name__}"
        weak = unrealsdk.unreal.WeakPointer
        self.holder, self.words, self.screen = weak(holder), weak(words), weak(screen)
        return "shown"

    @staticmethod
    def _style(holder: Any, layer: Any, band: Any, words: Any, text: str, points: float) -> None:
        words.SetText(text)
        font = words.Font
        try:
            font.Size = points
        except TypeError:
            # Engines before 5.1 size fonts in whole points (BL4 Arena's window).
            font.Size = round(points)
        words.SetFont(font)
        words.SetColorAndOpacity(unrealsdk.make_struct("SlateColor", SpecifiedColor=_colour(TEXT_RGBA)))
        band.SetBrushColor(_colour(BAND_RGBA))
        band.SetPadding(_margin(*BAND_PADDING_PX))
        band.SetContent(words)
        # An overlay slot told neither to fill sits at its content's size, here in the top left corner.
        corner = layer.AddChildToOverlay(band)
        corner.SetPadding(unrealsdk.make_struct("Margin", Left=MARGIN_PX, Top=MARGIN_PX, Right=0.0, Bottom=0.0))
        corner.SetHorizontalAlignment(_enum("EHorizontalAlignment", "HAlign_Left"))
        corner.SetVerticalAlignment(_enum("EVerticalAlignment", "VAlign_Top"))
        hidden_to_clicks = _enum("ESlateVisibility", "HitTestInvisible")
        layer.SetVisibility(hidden_to_clicks)
        holder.SetVisibility(hidden_to_clicks)

    def where(self) -> str:
        """"on" the screen; "off" once the game took it off; "gone" once its holder is freed, or before any show;
        "unknown" when the screen does not say, which is never taken for "off": the bar would be put on twice."""
        holder, screen = _live(self.holder), _live(self.screen)
        if holder is None:
            return "gone"
        if screen is None:
            return "unknown"
        try:
            value = screen.IsWidgetAdded(holder)
        except Exception:
            return "unknown"
        if type(value) is not bool:
            return "unknown"
        return "on" if value else "off"

    def write(self, text: str) -> bool:
        words = _live(self.words)
        if words is None:
            return False
        try:
            words.SetText(text)
        except Exception:
            return False
        return True

    def keep(self, pc: Any, text: str) -> str:
        """Once a second: the words written again, or the bar built again when the game took it off or freed it.
        "written", "shown", or what kept it off ("write_failed" when its words refused)."""
        if self.where() in ("off", "gone"):
            return self.show(pc, text)
        return "written" if self.write(text) else "write_failed"

    def remove(self) -> str:
        """Takes the bar off the screen: "removed", "gone" when the game freed it already, or why it failed."""
        holder = _live(self.holder)
        self.holder = self.words = None
        if holder is None:
            return "gone"
        try:
            self.announce("RemoveFromParent")
            holder.RemoveFromParent()
        except Exception as error:
            return f"failed:{type(error).__name__}"
        return "removed"
