"""Tests the camera options' shared English texts: one plain sentence each, and sides for the shoulder's two values."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from apex_camera_runtime import option_texts  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def one_sentence(text: str) -> bool:
    # Kevin, 2026-09-23: a description says what the player gets in one plain sentence (Omni Sprint's panel test).
    return 0 < len(text) <= 60 and text.count(".") == 1 and text.endswith(".")


TEXTS = (option_texts.THIRD_PERSON, option_texts.SHOULDER, option_texts.ORBIT, option_texts.ORBIT_DISTANCE,
         option_texts.CUSTOM_FOV, option_texts.FOV)
check("every camera option has a name and one short sentence",
      all(texts["display_name"] and one_sentence(texts["description"]) for texts in TEXTS))
check("the SDK's text menu names the shoulder's side, never On or Off",
      option_texts.SHOULDER["true_text"] == "Left" and option_texts.SHOULDER["false_text"] == "Right")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
