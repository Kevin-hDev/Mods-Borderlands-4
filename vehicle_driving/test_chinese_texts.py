"""Every word Vehicle Driving's window shows exists in Chinese: no English left in the Chinese window (2026-10-13).

Some come from generated or shared files: the CAMERA page's control words (Apex Grapple, panel_controls_text.py),
the VEHICLES page's (the shared vehicle_unlocks runtime) and the views' names (Apex Heirloom's panel_choices.py).
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import sdk_stubs  # noqa: E402

sdk_stubs.install()
from vehicle_driving import panel_choices, panel_controls_text, panel_en, panel_fr, panel_i18n  # noqa: E402
from vehicle_driving import panel_zh  # noqa: E402
from vehicle_driving.vehicle_unlock_runtime import runtime  # noqa: E402

# Words that stay as they are in Chinese: the game's name (the BL4 theme) and the consoles' (controller icons).
SAME = {"BL4", "PLAYSTATION", "XBOX"}
CHINESE = re.compile(r"[㐀-鿿]")
PLACES = re.compile(r"\{\w+\}")
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def same_table(label, reference, chinese):
    check(set(chinese) == set(reference), f"{label}: missing {sorted(set(reference) - set(chinese))}, "
                                          f"extra {sorted(set(chinese) - set(reference))}")
    for key in set(reference) & set(chinese):
        for other, zh in zip(*(value if isinstance(value, tuple) else (value,)
                               for value in (reference[key], chinese[key]))):
            check(sorted(PLACES.findall(other)) == sorted(PLACES.findall(zh)), f"{label}:{key} placeholders")
            check(zh in SAME or CHINESE.search(zh), f"{label}:{key} not Chinese: {zh!r}")


def without(table, keys):
    return {key: value for key, value in table.items() if key not in keys}


check("ZH" in panel_i18n.TABLES, "the window offers Chinese")
controls = set(panel_controls_text.FR)
# English and French together, so that a key only one of them holds is still asked of Chinese.
same_table("window", without({**panel_en.TEXT, **panel_fr.TEXT}, controls), without(panel_zh.TEXT, controls))
same_table("controls (Apex Grapple, generated)", panel_controls_text.FR, panel_zh.CONTROLS)
same_table("options", panel_fr.OPTIONS, panel_zh.OPTIONS)
same_table("pages", panel_fr.GROUPS, panel_zh.GROUPS)
same_table("views", panel_fr.CHOICES, panel_zh.CHOICES)
same_table("vehicles (vehicle_unlocks, shared)", runtime.text.FR, getattr(runtime.text, "ZH", {}))
# Kevin, 2026-09-23: a description says what the player gets in one plain sentence.
check(all(description.count("。") == 1 and description.endswith("。")
          for _, description in panel_zh.OPTIONS.values()), "every Chinese description is one sentence")
check(panel_zh.TEXT["close"] == "关闭" and panel_zh.TEXT["camera"] == "镜头", "window words")
check(panel_choices.label("Closest", "ZH") == "极近", "the views' names in Chinese (panel_choices.py, generated)")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | every word of Vehicle Driving's window exists in Chinese")
raise SystemExit(1 if failures else 0)
