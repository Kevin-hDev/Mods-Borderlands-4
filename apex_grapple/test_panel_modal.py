"""Tests the layer every settings window sits on (Kevin, 2026-10-06: a click beside the window gave the mouse to the
game, and the game behind should be a little blurred, as behind an app's pop-up): the holder can take the focus; a
layer over the whole screen takes the clicks and blurs the game at the theme's strength; the window keeps the mockup's
share of the screen, centred; the viewport gives the holder the whole screen; a game without the blur keeps a clear
layer that still takes the clicks, reported once."""

import sys
from types import SimpleNamespace as NS

import panel_render_fixture as fixture
import unrealsdk
from apex_grapple import panel_modal, panel_theme as t, panel_widgets as w

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def corners(anchors):
    return anchors.Minimum.X, anchors.Minimum.Y, anchors.Maximum.X, anchors.Maximum.Y


fixture.install()
window = unrealsdk.construct_object("ScaleBox", None)
holder = panel_modal.held(NS(), window)
screen = holder.WidgetTree.RootWidget
check(holder.kind == "UserWidget" and holder.bIsFocusable is True,
      "The holder can take the focus a click outside the buttons gives: before, the game's viewport took it")
check(screen.kind == "CanvasPanel" and len(screen.children) == 2 and screen.children[1] is window,
      "The window is drawn over the layer")
layer = screen.children[0]
check(layer.kind == "BackgroundBlur" and layer.attributes.get("SetBlurStrength") == (float(t.BACKDROP_BLUR),),
      "The layer blurs the game behind at the theme's strength")
check(layer.visibility == "ESlateVisibility.Visible", "The layer is hit: it takes the clicks the game took")
check(corners(screen.slots[0].attributes["SetAnchors"][0]) == (0.0, 0.0, 1.0, 1.0), "The layer covers the screen")
width = (t.WINDOW_WIDTH + t.SHADOW_XL) / t.STAGE_WIDTH
height = (t.WINDOW_HEIGHT + t.SHADOW_XL) / t.STAGE_HEIGHT
expected = ((1 - width) / 2, (1 - height) / 2, (1 + width) / 2, (1 + height) / 2)
share = corners(screen.slots[1].attributes["SetAnchors"][0])
check(all(abs(got - want) < 1e-9 for got, want in zip(share, expected)),
      "The window keeps the mockup's share of the screen, centred, as before the layer")
slot = panel_modal.viewport_slot()
check(corners(slot.Anchors) == (0.0, 0.0, 1.0, 1.0) and slot.ZOrder == t.ORDER, "The holder is given the whole screen")
check(0.0 < t.BACKDROP_BLUR <= 100.0, "The strength stays within Unreal's scale")

made = fixture.Node


def without_blur(kind, owner):
    if kind == "BackgroundBlur":
        raise ValueError("class not found")
    return made(kind, owner)


unrealsdk.construct_object = without_blur
for _ in range(2):
    holder = panel_modal.held(NS(), unrealsdk.construct_object("ScaleBox", None))
layer = holder.WidgetTree.RootWidget.children[0]
check(layer.kind == "Border" and layer.brush == w.linear(t.COLOR_INK, 0.0)
      and layer.visibility == "ESlateVisibility.Visible",
      "Without the blur, a clear layer still takes the clicks")
check(sum("'backdrop_blur'" in line for line in fixture.pf.f.state["errors"]) == 1, "The missing blur is reported once")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | modal layer: focus, blur, clicks, window share, fallback")
sys.exit(1 if failures else 0)
