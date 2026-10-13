"""Every word Apex Movement's window shows exists in Chinese: no English left in the Chinese window (2026-10-13)."""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import sdk_stubs  # noqa: E402

sdk_stubs.install()
from apex_movement import panel_en, panel_fr, panel_framing_text, panel_i18n, panel_profile_text  # noqa: E402
from apex_movement import panel_zh  # noqa: E402

# Words that stay as they are in Chinese: angles, the game's name and the field of view's.
SAME = {"360°", "180°", "BL4", "FOV"}
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


check("ZH" in panel_i18n.TABLES, "the window offers Chinese")
# English and French together: French alone has the aim notices, English names every other key.
same_table("window", {**panel_en.TEXT, **panel_fr.TEXT}, panel_zh.TEXT)
same_table("options", panel_fr.OPTIONS, panel_zh.OPTIONS)
same_table("pages", panel_fr.GROUPS, panel_zh.GROUPS)
same_table("framing", panel_framing_text.FR, panel_framing_text.ZH)
same_table("profiles", panel_profile_text.FR, panel_profile_text.ZH)
check(panel_i18n.text("wall_climb", "ZH") == "爬墙", "the movement pages' tabs in Chinese")
check(panel_i18n.text("close", "ZH") == "关闭" and panel_i18n.text("camera", "ZH") == "镜头", "window words")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | every word of Apex Movement's window exists in Chinese")
raise SystemExit(1 if failures else 0)
