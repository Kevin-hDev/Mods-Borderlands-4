"""The window's three sizes (Kevin, 2026-10-06): more room, never larger letters; LARGE is his red frame; FULL covers
any screen's shape; the game's screen size is read safely; the layer and the hazard band follow the size."""

import math
import sys
from types import SimpleNamespace as NS

import panel_render_fixture as fixture
import unrealsdk
from apex_grapple import panel_header, panel_modal, panel_theme as t, panel_window_size as size

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def player(screen):
    """A controller whose viewport is this screen, as the game gives it."""
    return NS(GetViewportSize=lambda *args: screen)


def scale(screen):
    """The ScaleBox's scale: the drawing fitted into its share of the screen, proportions kept (ScaleToFit)."""
    share_width, share_height = size.share()
    return min(share_width * screen[0] / (size.WIDTH + size.SHADOW),
               share_height * screen[1] / (size.HEIGHT + size.SHADOW))


fixture.install()
check(t.SIZES == ("LARGE", "FULL", "NORMAL"), "The button goes LARGE, FULL SCREEN, NORMAL")
check(size.current() == "LARGE" and (size.WIDTH, size.HEIGHT) == (1690, 965),
      "Before any window is drawn, the state is LARGE's, the default")

size.use("NORMAL")
check((size.WIDTH, size.HEIGHT, size.SHADOW) == (t.WINDOW_WIDTH, t.WINDOW_HEIGHT, t.SHADOW_XL) == (1400, 830, 14),
      "NORMAL is the window as it was")
check(size.share() == ((1400 + 14) / 1920, (830 + 14) / 1080), "NORMAL keeps the share of the screen it had")

size.use("LARGE")
width, height = size.share()
check(abs(width - 0.8882) < 0.002 and abs(height - 0.9069) < 0.002,
      "LARGE is Kevin's red frame: 88.8 % of the width, 90.7 % of the height (measured on his screenshot)")
check(size.SHADOW == t.SHADOW_XL and size.current() == "LARGE", "LARGE keeps the window's shadow")

for screen in ((1920, 1080), (2560, 1440), (1187, 668), (3440, 1440), (1920, 1200)):
    size.use("NORMAL")
    letters = scale(screen)
    for name in ("LARGE", "FULL"):
        size.use(name, player(screen))
        check(math.isclose(scale(screen), letters, rel_tol=0.002),
              f"{name} on a {screen[0]} x {screen[1]} screen: letters and buttons keep NORMAL's size")

for screen in ((2560, 1440), (3440, 1440), (1920, 1200), (1187, 668)):
    size.use("FULL", player(screen))
    width, height = size.share()
    fills = (size.WIDTH + size.SHADOW) * scale(screen), (size.HEIGHT + size.SHADOW) * scale(screen)
    check(size.SHADOW == 0 and width == height == 1.0 and abs(fills[0] - screen[0]) < 2 and abs(fills[1] - screen[1]) < 2,
          f"FULL covers a {screen[0]} x {screen[1]} screen edge to edge, without a shadow band")
size.use("FULL", player((3440, 1440)))
check(size.STAGE_WIDTH == 2580, "A 21:9 screen draws FULL 2580 wide on the 1080 reference")
size.use("FULL", player((1920, 1200)))
check((size.WIDTH, size.HEIGHT) == (1920, 1200), "A 16:10 screen draws FULL taller, not with larger letters")
for screen in (None, (100, 1), (1, 100)):
    size.use("FULL", None if screen is None else player(screen))
    check((size.WIDTH, size.HEIGHT, size.STAGE_WIDTH, size.STAGE_HEIGHT) == (1920, 1080, 1920, 1080),
          f"FULL without a believable screen ({screen}) keeps the 16:9 drawing")
size.use("FULL", player((3440, 1440)))
reads = []
size.use("LARGE", NS(GetViewportSize=lambda *args: reads.append(args)))
check((size.STAGE_WIDTH, size.STAGE_HEIGHT, size.WIDTH) == (1920, 1080, 1690) and not reads,
      "Only FULL follows the screen's shape, and only FULL reads it")
size.use("no such size")
check(size.current() == "LARGE" and size.WIDTH == 1690, "An unknown saved name draws LARGE")

check(size.pixels((2560, 1440)) == (2560.0, 1440.0), "The probe's shape: two numbers")
check(size.pixels((None, 2560, 1440)) == (2560.0, 1440.0), "Output values after a return value: the two last")
check(size.pixels(NS(SizeX=1920, SizeY=1080)) == (1920.0, 1080.0), "A struct with SizeX and SizeY")
check(size.pixels(NS(X=1280, Y=720)) == (1280.0, 720.0), "A vector")
for bad in (None, "2560x1440", (0, 0), (True, False), (2560,), (float("nan"), 1080), (float("inf"), 1080),
            (-1, 1080), (2560, 10**9)):
    check(size.pixels(bad) is None, f"Not a screen size: {bad!r}")

calls = []
pc = NS(GetViewportSize=lambda *args: calls.append(args) or (2560, 1440))
check(size.read_screen(pc) == (2560.0, 1440.0) and calls == [(0, 0)],
      "The screen is read as the probe did, its two output values given")
errors = fixture.pf.f.state["errors"]
before = len(errors)
for _ in range(2):
    check(size.read_screen(NS()) is None, "A controller without the function gives no size: FULL keeps 16:9")
check(len(errors) == before + 1 and "'viewport_size'" in errors[-1], "The missing reading is reported once")

stripes = {}
for name in ("NORMAL", "LARGE"):
    size.use(name)
    stripes[name] = len(panel_header.hazard(unrealsdk.construct_object("Overlay", None)).children[0].children)
check(stripes["LARGE"] > stripes["NORMAL"],
      "The hazard band keeps its stripes' width: a wider window has more stripes, not wider ones")

for name, screen in (("LARGE", None), ("FULL", (2560, 1440))):
    size.use(name, None if screen is None else player(screen))
    holder = panel_modal.held(NS(), unrealsdk.construct_object("ScaleBox", None))
    anchors = holder.WidgetTree.RootWidget.slots[1].attributes["SetAnchors"][0]
    width, height = size.share()
    got = anchors.Minimum.X, anchors.Minimum.Y, anchors.Maximum.X, anchors.Maximum.Y
    want = ((1 - width) / 2, (1 - height) / 2, (1 + width) / 2, (1 + height) / 2)
    check(all(abs(a - b) < 1e-9 for a, b in zip(got, want)), f"{name}: the layer gives the window its share, centred")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | window sizes: same letters, red frame, full screen, screen read")
sys.exit(1 if failures else 0)
