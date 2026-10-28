"""The short message at the top of the host's screen: the round's outcome and the score's line at each round, then
nothing until the next one (Kevin, 17 October 2026: "rien à l'écran le reste du temps"); also why the duel's key
could not start a duel, and why a duel ended on its own. The guest sees nothing: only the host's game runs the mod,
and a guest without it draws nothing of ours (Kevin's choice).

Its look is HUD Editor's, our mod (Kevin, 17 October 2026, two screenshots of it as the model): a cyan plate on top
left holding the title in dark capitals, over a dark blue-green panel framed in cyan, the names in white and the score
in HUD Editor's orange. The colours are read on those screenshots. The letters are Barlow Condensed, the window's own
(panel_fonts.py, seen in game); HUD Editor's own, the game's Industry, lives in the game's web HUD, out of reach of
these widgets.

Built as It Follows' bar is (it_follows/bar.py, verified in game): UMG widgets made at runtime under the player's
controller, rooted in a UserWidget's WidgetTree and put over the whole screen by GameViewportSubsystem.AddWidget,
HitTestInvisible so that the game's own menus under it still take their clicks. Seen in game in trial 9 in its first,
plain look. A failure is said in the log once and never stops the duel: the score is also in the window.
"""

from itertools import islice
from typing import Any

import unrealsdk

from . import panel_fonts, panel_widgets as w, report, score

# Under our mods' windows (10000), so that a menu covers the message.
ZORDER = 5000
SHOW_S = 4.0
TOP_PX = 90.0
# HUD Editor's colours, read on Kevin's screenshots of 17 October 2026.
CYAN = "00e6ff"
ORANGE = "ff9e27"
PANEL = "0b1e26"
PANEL_ALPHA = 0.92
WHITE = "ffffff"
PLATE_TEXT = "06161d"
# In points; a 1080p screen's pixels.
TITLE_POINTS, NAME_POINTS, SCORE_POINTS, SENTENCE_POINTS = 15.0, 24.0, 34.0, 19.0
FRAME_PX = 2.0
PLATE_PADDING_PX, BODY_PADDING_PX = (2.0, 14.0), (10.0, 26.0)
NAME_GAP_PX = 22.0
PLATE_SHEAR = -14.0
SENTENCE_WIDTH_PX = 760.0
# Letter spacing, in thousandths of the font size: the plates' wide capitals.
TITLE_SPACING = 120
# How many screen subsystems are looked through for the one in play (BL4 Arena's window: 32).
MAX_INSTANCES = 32
# Kinds of failure said in the log: a handful in practice; past this, new kinds are dropped.
MAX_FAILURES = 20
# Each kind of the score's parts: its size, colour and face, and whether a gap sits on both its sides.
LOOKS = {score.NAME: (NAME_POINTS, WHITE, "SemiBold", False), score.POINTS: (SCORE_POINTS, ORANGE, "ExtraBold", True),
         score.SEPARATOR: (NAME_POINTS, CYAN, "SemiBold", True)}
# Four teams make eleven parts; the bound keeps a broken line from building widgets without end.
MAX_PARTS = 16


def _viewport() -> Any:
    return next((one for one in islice(unrealsdk.find_all("GameViewportSubsystem"), MAX_INSTANCES)
                 if not str(one.Name).startswith("Default__")), None)


def _enum(name: str, member: str) -> Any:
    return getattr(unrealsdk.find_enum(name), member)


def _margin(top: float, side: float) -> Any:
    return unrealsdk.make_struct("Margin", Left=side, Top=top, Right=side, Bottom=top)


def _slot() -> Any:
    whole = unrealsdk.make_struct("Anchors", Minimum=w.vector(0.0, 0.0), Maximum=w.vector(1.0, 1.0))
    return unrealsdk.make_struct("GameViewportWidgetSlot", ZOrder=ZORDER, bAutoRemoveOnWorldRemoved=True,
                                 Alignment=w.vector(0.0, 0.0), Anchors=whole, Offsets=_margin(0.0, 0.0))


class _Look:
    """The fonts, built once per message: the text widgets using them are what keep them alive."""

    def __init__(self, holder: Any) -> None:
        try:
            self.fonts = panel_fonts.build(holder)
        except Exception:
            self.fonts = {}

    def text(self, owner: Any, value: str, points: float, colour: str, face: str, spacing: int = 0) -> Any:
        words = unrealsdk.construct_object("TextBlock", owner)
        words.SetText(value)
        font = words.Font
        try:
            font.Size = points
        except TypeError:
            # Engines before 5.1 size fonts in whole points (BL4 Arena's window).
            font.Size = round(points)
        if "body" in self.fonts:
            font.FontObject = self.fonts["body"]
            font.TypefaceFontName = face
        if spacing:
            try:
                font.LetterSpacing = spacing
            except Exception:
                pass  # Wider capitals are a look: without them the plate still reads.
        words.SetFont(font)
        words.SetColorAndOpacity(w.slate(colour))
        return words


def _box(owner: Any, colour: str, padding: tuple[float, float], alpha: float = 1.0) -> Any:
    box = unrealsdk.construct_object("Border", owner)
    box.SetBrushColor(w.linear(colour, alpha))
    box.SetPadding(_margin(*padding))
    return box


def _centred(slot: Any) -> None:
    slot.SetVerticalAlignment(_enum("EVerticalAlignment", "VAlign_Center"))


def build(holder: Any, title: str, line: list[tuple[str, str]] | None, sentence: str | None) -> Any:
    """The message's widgets under holder: the plate and its title, then the framed panel with the score's line
    (score.py) or a sentence. Its root, an Overlay over the whole screen."""
    look = _Look(holder)
    layer = unrealsdk.construct_object("Overlay", holder)
    card = unrealsdk.construct_object("VerticalBox", layer)
    plate = _box(card, CYAN, PLATE_PADDING_PX)
    plate.SetContent(look.text(plate, title.upper(), TITLE_POINTS, PLATE_TEXT, "ExtraBold", TITLE_SPACING))
    plate.SetRenderShear(w.vector(PLATE_SHEAR, 0.0))
    card.AddChildToVerticalBox(plate).SetHorizontalAlignment(_enum("EHorizontalAlignment", "HAlign_Left"))
    frame = _box(card, CYAN, (FRAME_PX, FRAME_PX))
    body = _box(frame, PANEL, BODY_PADDING_PX, PANEL_ALPHA)
    frame.SetContent(body)
    if line is not None:
        row = unrealsdk.construct_object("HorizontalBox", body)
        for value, kind in islice(line, MAX_PARTS):
            size, colour, face, gap = LOOKS[kind]
            slot = row.AddChildToHorizontalBox(look.text(row, value, size, colour, face))
            _centred(slot)
            if gap:
                slot.SetPadding(_margin(0.0, NAME_GAP_PX))
        body.SetContent(row)
    else:
        words = look.text(body, sentence or "", SENTENCE_POINTS, WHITE, "SemiBold")
        words.SetAutoWrapText(True)
        # The game's TextBlock has no SetWrapTextAt (its function list, cosmetics/heirloom/releves/2026-09-25-
        # listes-animations/apex_functions.txt): trial 10's sentence failed to build on it. WrapTextAt is its
        # field (a probe of 21 September read it); written, it is not verified in game to take effect, and a
        # refused write leaves the sentence wrapping at the screen's edge.
        try:
            words.WrapTextAt = SENTENCE_WIDTH_PX
        except Exception:
            pass
        body.SetContent(words)
    card.AddChildToVerticalBox(frame)
    top = layer.AddChildToOverlay(card)
    top.SetPadding(unrealsdk.make_struct("Margin", Left=0.0, Top=TOP_PX, Right=0.0, Bottom=0.0))
    top.SetHorizontalAlignment(_enum("EHorizontalAlignment", "HAlign_Center"))
    top.SetVerticalAlignment(_enum("EVerticalAlignment", "VAlign_Top"))
    return layer


class Banner:
    """The message on the screen, held weakly, and when it is taken off."""

    def __init__(self) -> None:
        self.holder = None
        self.until = 0.0
        self.failures: set[str] = set()

    def show(self, pc: Any, title: str, now: float, line: list[tuple[str, str]] | None = None,
             sentence: str | None = None) -> str:
        """The message built and put on the screen for SHOW_S, the one before taken off: "shown", or what kept it
        off."""
        self.hide()
        step = "viewport"
        try:
            screen = _viewport()
            if screen is None or pc is None:
                return self._failed("no_viewport")
            step = "build"
            holder = unrealsdk.construct_object("UserWidget", pc)
            holder.bIsFocusable = False
            tree = unrealsdk.construct_object("WidgetTree", holder)
            holder.WidgetTree = tree
            layer = build(holder, title, line, sentence)
            tree.RootWidget = layer
            hidden_to_clicks = _enum("ESlateVisibility", "HitTestInvisible")
            layer.SetVisibility(hidden_to_clicks)
            holder.SetVisibility(hidden_to_clicks)
            step = "add"
            if not screen.AddWidget(holder, _slot()):
                return self._failed("refused")
        except Exception as error:
            return self._failed(f"{step}_failed:{type(error).__name__}")
        self.holder, self.until = unrealsdk.unreal.WeakPointer(holder), now + SHOW_S
        return "shown"

    def _failed(self, why: str) -> str:
        """Each kind of failure said once: a message fails the same way at every round, and the log must not fill."""
        if why not in self.failures and len(self.failures) < MAX_FAILURES:
            self.failures.add(why)
            report.note("message not shown", why=why)
        return why

    def tick(self, now: float) -> None:
        if self.holder is not None and now >= self.until:
            self.hide()

    def hide(self) -> None:
        holder = self.holder() if self.holder is not None else None
        self.holder = None
        if holder is None:
            return
        try:
            holder.RemoveFromParent()
        except Exception as error:
            report.note("message not taken off", error=type(error).__name__)
