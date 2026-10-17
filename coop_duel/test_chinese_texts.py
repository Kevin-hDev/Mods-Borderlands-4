"""Every word Co-op Duel's window and its message on the screen show exists in Chinese: no English left, the duel,
its rounds, the host, the vehicle and the rest named as the Chinese game names them, the buttons a sentence names
written as the buttons show them (2026-10-17)."""

import pathlib
import re
import sys
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import sdk_stubs  # noqa: E402

sdk_stubs.install()
from coop_duel import panel_en, panel_fr, panel_i18n  # noqa: E402
from coop_duel import panel_zh  # noqa: E402

# Words that stay as they are in Chinese: the game's name and the mod's own, a product name as the other mods keep.
SAME = {"BL4", "CO-OP DUEL"}
CHINESE = re.compile(r"[㐀-鿿]")
PLACES = re.compile(r"\{\w+\}")
# Half-width punctuation has no place in a Chinese sentence; the log's file name keeps its dot.
LATIN_PUNCTUATION = re.compile(r"[,.:;()!?]")
KEPT = ("unrealsdk.log",)
# The game's own zh-Hans texts (Steam build 1.10.2, read 2026-10-17): an English text naming one names it this way.
# The mod's name is taken out of the English first, so its "Duel" asks for nothing.
NAMES = (
    (r"\bduels?\b", "决斗"), (r"\bround\b", "轮"), (r"\bhost\b", "主办者"), (r"\bguest\b", "客户端玩家"),
    (r"\bvehicle\b", "载具"), (r"\bget out\b", "退出载具"), (r"\bis down\b", "倒地"), (r"\binvite a friend\b", "邀请好友"),
    (r"\bload a game\b", "加载"), (r"^options$", "选项"), (r"\bpress a key\b", "按任意键"), (r"\b(the|this) key\b", "按键"),
)
# Read in the game's texts and set aside: 单挑 is "come fight me", 房主 and 下车 never appear, 车辆 is a car's papers,
# 载入 only "goes down in history", 点击 a mouse word for a menu also used with a controller.
NOT_THE_GAME = ("单挑", "房主", "车辆", "下车", "载入", "点击")
QUOTED = re.compile(r"「([^」]*)」")
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def same_table(label, reference, chinese):
    check(set(chinese) == set(reference), f"{label}: missing {sorted(set(reference) - set(chinese))}, "
                                          f"extra {sorted(set(chinese) - set(reference))}")
    for key in set(reference) & set(chinese):
        other, zh = reference[key], chinese[key]
        check(sorted(PLACES.findall(other)) == sorted(PLACES.findall(zh)), f"{label}:{key} placeholders")
        if other == "":
            check(zh == "", f"{label}:{key} stays empty as in French")
        else:
            check(zh in SAME or CHINESE.search(zh), f"{label}:{key} not Chinese: {zh!r}")


# English and French together: a window key added in one language only must not be forgotten.
same_table("window", {**panel_en.TEXT, **panel_fr.TEXT}, panel_zh.TEXT)
same_table("pages", panel_fr.GROUPS, panel_zh.GROUPS)
check(panel_zh.OPTIONS == panel_fr.OPTIONS == {}, "no setting row to translate")

own = {key: text for key, text in panel_zh.TEXT.items() if key not in panel_zh.COMMON}
sentences = [*own.values(), *panel_zh.GROUPS.values()]


def bare(text):
    for kept in KEPT:
        text = text.replace(kept, "")
    return text


check(not [text for text in sentences if LATIN_PUNCTUATION.search(bare(text))], "full-width punctuation only")
check(not [text for text in sentences if "—" in text or "–" in text], "no long dash")
for wrong in NOT_THE_GAME:
    check(not [text for text in sentences if wrong in text], f"never {wrong}: not the game's word")

# What the English says the same way in every language: its numbers, the log's file name, the mod's name; and each
# refusal's promise that the game is not changed, in the words of the common texts' 未做任何更改.
for key in own.keys() & panel_en.TEXT.keys():
    english = panel_en.TEXT[key]
    for token in (*re.findall(r"\d+", english), *(name for name in (*KEPT, "Co-op Duel") if name in english)):
        check(token in own[key], f"{key}: keeps {token}")
    if "Your game is not changed" in english:
        check("你的游戏未做任何更改" in own[key], f"{key}: says the game is not changed")

for key in own.keys() & panel_en.TEXT.keys():
    english = panel_en.TEXT[key].lower().replace("co-op duel", "")
    for pattern, zh in NAMES:
        if re.search(pattern, english):
            check(zh in own[key], f"{key}: names {pattern} as the game, {zh}")

# A sentence naming a button names it as the button shows it.
buttons = {panel_zh.TEXT["start"], panel_zh.TEXT["stop"]}
for key, text in own.items():
    for quoted in QUOTED.findall(text):
        check(quoted in buttons, f"{key}: 「{quoted}」 is no button of the window")
    english = panel_en.TEXT[key]
    for button in ("start", "stop"):
        if panel_en.TEXT[button] in english and key != button:
            check(f"「{panel_zh.TEXT[button]}」" in text, f"{key}: names the {button} button as it shows")
# The switch at the bottom left shows 已启用 / 已停用: a sentence about it uses the same verbs.
check(panel_zh.COMMON["enabled"].removeprefix("已") in own["start_off"], "start_off: switch it on as the switch says")
check(panel_zh.COMMON["disabled"].removeprefix("已") in own["start_off"], "start_off: off as the switch says")
check((own["duel"], own["banner_over"], own["host"]) == ("决斗", "决斗结束", "主办者"), "duel and host as the game")
check(own["banner_round"].format(round=2) == "第2轮", "round as the game numbers it")

check(panel_i18n.TABLES.get("ZH") is panel_zh, "the window offers Chinese (outils/menu_languages.py)")
group = SimpleNamespace(description="English")
check(panel_i18n.text("duel", "ZH") == "决斗" and panel_i18n.text("close", "ZH") == "关闭", "window words")
check(panel_i18n.text("banner_round", "ZH") == "第{round}轮", "the message on the screen in Chinese")
check(panel_i18n.text("start_in_vehicle", "ZH") == panel_zh.TEXT["start_in_vehicle"], "refusals in Chinese")
check(panel_i18n.group_text(group, "duel", "ZH") == "", "page sentences in Chinese")
check(panel_i18n.text("start", "FR") == "LANCER LE DUEL", "French unchanged")
check(panel_i18n.text("start", "EN") == "START DUEL", "English unchanged")

# A Windows console prints in cp1252, where a Chinese failure message would crash the test before its RESULTAT.
sys.stdout.reconfigure(errors="backslashreplace")
for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | every word of Co-op Duel's window exists in Chinese")
raise SystemExit(1 if failures else 0)
