"""Check page coverage, language, transactions and the vehicle input context."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from vehicle_driving import menu, mod, panel_preferences as prefs, settings  # noqa: E402
from vehicle_driving import control_window, panel_i18n  # noqa: E402
from vehicle_driving.panel_model import Model  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


model = Model(mod)
check("both pages contain each original setting exactly once",
      model.pages == ("driving", "handling") and len(model.options) == 6
      and [option for group in menu.MENU for option in group.children] == settings.OPTIONS)
check("English and French pages use the approved menu labels",
      panel_i18n.text("driving", "EN") == "DRIVING"
      and panel_i18n.text("handling", "FR") == "TENUE DE ROUTE")
# Kevin, 2026-09-23: a description says what the player gets in one plain sentence.
descriptions = [panel_i18n.option_text(option, language)[1]
                for option in settings.OPTIONS for language in ("EN", "FR")]
check("every option has one short sentence in both languages",
      all(0 < len(text) <= 60 and text.count(".") == 1 and text.endswith(".") for text in descriptions)
      and panel_i18n.option_text(settings.grip, "FR")[1] != settings.grip.description)
check("saved language and last page persist", model.change_language("FR") and model.change_page("handling")
      and Model(mod).language == "FR" and Model(mod).page == "handling" and state["saves"] >= 2)
check("invalid slider value cannot change a setting", not model.write({"max_speed": 999})
      and settings.max_speed.value == 125)
check("valid slider change is saved", model.write({"max_speed": 150})
      and settings.max_speed.value == 150)
check("reset and undo restore the previous value", model.restore() and settings.max_speed.value == 125
      and model.undo() and settings.max_speed.value == 150)

vehicle = object()
pc = types.SimpleNamespace(Pawn=vehicle, OakCharacter=None, CurrentMouseCursor="Default")
state["pc"] = pc
weak = sdk_stubs.WeakPointer
session = control_window.Session(weak(pc), lambda: None, lambda: None, False,
                                 types.SimpleNamespace(focus=lambda: None), None, lambda: None)
check("at the wheel the window restores gameplay input", not session.frontend and session.same_context(pc))
pc.Pawn = object()
check("a changed vehicle closes the old context", not session.same_context(pc))
pc.Pawn = None
front = control_window.Session(weak(pc), lambda: None, lambda: None, False,
                               types.SimpleNamespace(focus=lambda: None), None, lambda: None)
check("the title screen remains a frontend context", front.frontend and front.same_context(pc))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
