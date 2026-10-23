"""Every word It Follows' window shows exists in Japanese (2026-10-23): its pages, its setting rows and their choices,
the COMPANIONS page and the bar in the game, in Japanese characters, no Simplified Chinese one slipped in; the
placeholders and numbers of the English kept; a button or row named in a sentence named as it shows; a date written
as Japanese writes one. The update notes are not checked: the versions before Japanese have none, and the pop-up shows
their English (outils/release_notes.py asks for changelog_ja.md from the next version on)."""

import pathlib
import re
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import sdk_stubs  # noqa: E402

sdk_stubs.install()
from it_follows import companion_choices, options, panel_companion_texts, panel_en, panel_fr  # noqa: E402
from it_follows import panel_glyphs, panel_header, panel_i18n, panel_ja, panel_words, texts  # noqa: E402
from it_follows.normal import options as normal_options  # noqa: E402

# Words that stay as they are in Japanese: the game's name in the theme's button.
SAME = {"BL4"}
JAPANESE = re.compile(r"[ぁ-ゟ゠-ヿ一-鿿]")
PLACES = re.compile(r"\{[^{}]*\}")
QUOTED = re.compile(r"「([^」]*)」")
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def japanese_only(text):
    """Whether every character is one Japanese writes: Simplified Chinese ones (敌, 击) are not in JIS X 0213."""
    try:
        text.encode("euc_jis_2004")
    except UnicodeEncodeError:
        return False
    return True


def same_text(label, other, ja):
    check(sorted(PLACES.findall(other)) == sorted(PLACES.findall(ja)), f"{label} placeholders")
    check(japanese_only(ja.replace("·", "")), f"{label}: a character Japanese does not write: {ja!r}")
    check("—" not in ja and "–" not in ja, f"{label}: no long dash")
    if other == "":
        check(ja == "", f"{label} stays empty")
    elif not re.search(r"[A-Za-z]", PLACES.sub("", other)):
        check(not re.search(r"[A-Za-z]", PLACES.sub("", ja)), f"{label}: no English word")
    else:
        check(ja in SAME or bool(JAPANESE.search(ja)), f"{label} not Japanese: {ja!r}")
    for number in re.findall(r"\d+", PLACES.sub("", other).replace("Borderlands 4", "")):
        check(number in ja, f"{label}: keeps {number}")


def same_table(label, reference, japanese):
    check(set(japanese) == set(reference), f"{label}: missing {sorted(set(reference) - set(japanese))}, "
                                           f"extra {sorted(set(japanese) - set(reference))}")
    for key in set(reference) & set(japanese):
        pairs = zip(*(value if isinstance(value, tuple) else (value,) for value in (reference[key], japanese[key])))
        for other, ja in pairs:
            same_text(f"{label}:{key}", other, ja)


check(panel_i18n.TABLES.get("JA") is panel_ja, "the window offers Japanese (outils/menu_languages.py)")
same_table("window", {**panel_fr.TEXT, **panel_en.TEXT}, panel_ja.TEXT)
same_table("pages", panel_fr.GROUPS, panel_ja.GROUPS)
same_table("companions", panel_companion_texts.EN, panel_companion_texts.JA)
# The outfit's two buttons share a card's width with its word: together no wider than the English ones, a
# Japanese character as wide as two Latin letters (Kevin, 2026-10-23: プレイヤーのカラー ran out of Vex's card).
OUTFITS = ("companions_outfit:own", "companions_outfit:player")
check(2 * sum(len(panel_companion_texts.JA[key]) for key in OUTFITS)
      <= sum(len(panel_companion_texts.EN[key]) for key in OUTFITS), "the outfit buttons outgrow the card")
same_table("companions' row", panel_companion_texts.OPTIONS_FR, panel_companion_texts.OPTIONS_JA)
rows = {option.identifier: option for option in (*options.RUN, *options.DISPLAY, *normal_options.PAGE,
                                                 companion_choices.bars)}
check(set(panel_ja.OPTIONS) == set(panel_fr.OPTIONS), "the same setting rows as French")
same_table("options", {key: (option.display_name, option.description) for key, option in rows.items()
                       if key in panel_ja.OPTIONS}, panel_ja.OPTIONS)
check(set(panel_fr.CHOICES) <= set(panel_ja.CHOICES), f"French choices missing: "
                                                      f"{sorted(set(panel_fr.CHOICES) - set(panel_ja.CHOICES))}")
for option in rows.values():
    for choice in getattr(option, "choices", ()):
        name = panel_ja.CHOICES.get(f"{option.identifier}:{choice}") or panel_ja.CHOICES.get(choice)
        check(name is not None or choice.isdigit(), f"choice {option.identifier}:{choice} named in Japanese")
        if name is not None:
            # A level's choice is its target (25) but shows Level 1: the English name is the one compared.
            english = panel_en.CHOICES.get(f"{option.identifier}:{choice}") or panel_en.CHOICES.get(choice, choice)
            same_text(f"choice {option.identifier}:{choice}", english, name)

# A sentence naming a button, a page's tab, a row or the run's settings card names it as the window shows it.
BUTTONS = ("start", "stop", "start_choose", "start_back", "companions_launch", "companions_stop",
           "run", "normal", "history", "options", "companions")
shown = {panel_ja.TEXT[key] for key in BUTTONS} | {name for name, _ in panel_ja.OPTIONS.values()} \
    | {panel_ja.TEXT["run_settings"]}
# The window words every mod shares quote the shared buttons (「閉じる」): their own test checks them.
own = {key: text for key, text in panel_ja.TEXT.items() if key not in panel_ja.COMMON}
for key, text in {**own, **{f"option {key}": text for key, (_, text) in panel_ja.OPTIONS.items()}}.items():
    for quoted in QUOTED.findall(text):
        check(quoted in shown, f"{key}: 「{quoted}」 is no button, row or title of the window")
check(f"「{panel_ja.OPTIONS['max_enemies'][0]}」" in panel_ja.TEXT["caution"], "caution: names the Max enemies row")
levels = [panel_ja.CHOICES.get(name) for name in ("Bandit", "Senior", "Predator", "God")]
check(all(levels) and all(level in panel_ja.TEXT["welcome_levels"] for level in levels), "welcome_levels: the four")
check("2" in panel_ja.CHOICES["level:40"], "a level keeps its number")


def moment(day, hour, minute):
    return int(time.mktime((2026, 10, day, hour, minute, 0, 0, 0, -1)))


now = moment(14, 18, 0)
check(panel_words.when(moment(14, 9, 7), "JA", now) == "今日 09:07", "today in Japanese")
check(panel_words.when(moment(13, 23, 5), "JA", now) == "昨日 23:05", "yesterday in Japanese")
check(panel_words.when(moment(2, 20, 15), "JA", now) == "10月2日 20:15", "a date as Japanese writes it")
check(len(panel_ja.TEXT["months"].split()) == 12, "twelve months")

check(texts.JAPANESE in texts.LANGUAGES, "the bar offers Japanese")
line = texts._BAR[texts.JAPANESE]
check(sorted(PLACES.findall(line)) == sorted(PLACES.findall(texts._BAR[texts.ENGLISH])), "the bar's placeholders")
check(not re.search(r"[A-Za-z]", PLACES.sub("", line)) and japanese_only(line), "the bar: Japanese words only")
check("37" in texts.bar(texts.JAPANESE, 12, 1, 37, 3, 277.9), "the bar in Japanese shows its figures")

check(panel_i18n.text("close", "JA") == "閉じる", "window words")
option = SimpleNamespace(identifier="level", display_name="Level", description="English")
check(panel_i18n.option_text(option, "JA") == panel_ja.OPTIONS["level"], "setting rows in Japanese")
check(panel_header.language_button("JA") == "日本語", "the header button named in Japanese")
check(panel_glyphs.label("Gamepad_DPad_Up", "PS5", "JA") == "方向キー上", "controller names in Japanese")
check(panel_i18n.text("start", "FR") == "START" and panel_i18n.text("start", "EN") == "START", "others unchanged")

# A Windows console prints in cp1252, where a Japanese failure message would crash the test before its RESULTAT.
sys.stdout.reconfigure(errors="backslashreplace")
for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | every word of It Follows' window exists in Japanese")
raise SystemExit(1 if failures else 0)
