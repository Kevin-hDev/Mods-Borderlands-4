"""Every word Companions' window shows exists in Japanese (2026-10-23): its texts, its setting rows and its pages'
sentences, in Japanese characters, no Simplified Chinese one slipped in; the places to fill and the numbers of the
English kept; no half-width punctuation in a Japanese sentence; a button a sentence names written as it shows, in
「」."""

import pathlib
import re
import sys
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()
from companions import menu, panel_common_en, panel_en, panel_glyphs, panel_header, panel_i18n, panel_ja  # noqa: E402
from companions import settings  # noqa: E402

JAPANESE = re.compile(r"[ぁ-ゟ゠-ヿ一-鿿]")
PLACES = re.compile(r"\{[^{}]*\}")
LATIN_PUNCTUATION = re.compile(r"[,.:;()!?\[\]\"]")
# The mods' names stay in Latin letters; a value's own words are a sign and a number.
KEPT = ("It Follows", "Companions", "unrealsdk.log")
VALUES = ("value_times", "value_percent", "value_bonus")
QUOTED = re.compile(r"「([^」]*)」")
failures = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def bare(text: str) -> str:
    text = PLACES.sub("", text)
    for kept in KEPT:
        text = text.replace(kept, "")
    return text


def japanese_only(text: str) -> bool:
    """Whether every character is one Japanese writes: Simplified Chinese ones (护, 伙) are not in JIS X 0213."""
    try:
        text.encode("euc_jis_2004")
    except UnicodeEncodeError:
        return False
    return True


own = {key: text for key, text in panel_en.TEXT.items() if key not in panel_common_en.TEXT}
ja_own = {key: text for key, text in panel_ja.TEXT.items() if key not in panel_ja.COMMON}
check(set(ja_own) == set(own), f"missing {sorted(set(own) - set(ja_own))}, extra {sorted(set(ja_own) - set(own))}")
# The outfit's two buttons share a card's width with its word: together no wider than the English ones, a
# Japanese character as wide as two Latin letters (Kevin, 2026-10-23: プレイヤーのカラー ran out of Vex's card).
OUTFITS = ("outfit:own", "outfit:player")
check(2 * sum(len(ja_own[key]) for key in OUTFITS) <= sum(len(own[key]) for key in OUTFITS),
      "the outfit buttons outgrow the card")
rows = [option.identifier for option in (*settings.TEAM, settings.bars)]
pages = [group.identifier.removesuffix("_menu") for group in menu.MENU]
check(sorted(panel_ja.OPTIONS) == sorted(rows), "a setting row without its words")
check(sorted(panel_ja.GROUPS) == sorted(pages), "a page without its sentence")

english = {**own, **{f"option:{option.identifier}": f"{option.display_name} {option.description}"
                     for option in (*settings.TEAM, settings.bars)}}
japanese = {**ja_own, **{f"option:{key}": " ".join(words) for key, words in panel_ja.OPTIONS.items()},
            **{f"group:{key}": text for key, text in panel_ja.GROUPS.items()}}
for key, text in japanese.items():
    reference = english.get(key, "")
    check(sorted(PLACES.findall(reference)) == sorted(PLACES.findall(text)) or not reference, f"{key} places")
    check(japanese_only(text.replace("·", "")), f"{key}: a character Japanese does not write: {text}")
    check("—" not in text and "–" not in text, f"{key}: no long dash")
    for number in re.findall(r"\d+", PLACES.sub("", reference)):
        check(number in text, f"{key}: keeps {number}")
    if not text or key in VALUES:
        continue
    check(bool(JAPANESE.search(text)), f"{key} is not Japanese: {text}")
    check(not re.search(r"[A-Za-z]", bare(text)), f"{key} keeps English: {text}")
    check(not LATIN_PUNCTUATION.search(bare(text)), f"{key} has half-width punctuation: {text}")
    for quoted in QUOTED.findall(text):
        check(quoted in panel_ja.TEXT.values(), f"{key} quotes a button that does not show: {quoted}")

check(panel_i18n.TABLES.get("JA") is panel_ja, "the window offers Japanese (outils/menu_languages.py)")
check(panel_i18n.text("close", "JA") == "閉じる", "window words")
row = SimpleNamespace(identifier="health_times", display_name="Health", description="English")
check(panel_i18n.option_text(row, "JA") == panel_ja.OPTIONS["health_times"], "setting rows in Japanese")
check(panel_header.language_button("JA") == "日本語", "the header button named in Japanese")
check(panel_glyphs.label("Gamepad_DPad_Up", "PS5", "JA") == "方向キー上", "controller names in Japanese")
check(panel_i18n.text("hunters", "FR") == "CHASSEURS DE L'ARCHE", "French unchanged")

# A Windows console prints in cp1252, where a Japanese failure message would crash the test before its RESULTAT.
sys.stdout.reconfigure(errors="backslashreplace")
for failure in failures:
    print(f"ECHEC | {failure}")
print("RESULTAT:", "TOUS LES TESTS PASSENT" if not failures else f"{len(failures)} ECHEC(S)")
sys.exit(1 if failures else 0)
