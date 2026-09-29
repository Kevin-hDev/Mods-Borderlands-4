"""The loaded game's id: ActiveCharGuid written as the save writes char_guid, negative words included; none while the
game has not set it yet, or when it cannot be read."""

import sys
import types

import sdk_stubs

sdk_stubs.install()

from hunter_change.game_id import PATTERN, game_id  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def signed(word: int) -> int:
    return word - (1 << 32) if word >= 1 << 31 else word


def player_state(**guid: int) -> types.SimpleNamespace:
    return types.SimpleNamespace(ActiveCharGuid=types.SimpleNamespace(**guid))


# Rafa's save of 2026-09-28 (slot 6) and the game's answer in essai 28.
rafa = player_state(A=signed(0x4F3ED67C), B=signed(0x7CDBB85D), C=signed(0xD75426BD), D=signed(0x679FD6BC))
check("written as the save writes char_guid, negative words included",
      game_id(rafa) == "4F3ED67C7CDBB85DD75426BD679FD6BC")
check("none while the game has not set it yet", game_id(player_state(A=0, B=0, C=0, D=0)) is None)
check("none when it cannot be read", game_id(player_state(A=1, B=2)) is None
      and game_id(types.SimpleNamespace()) is None and game_id(None) is None)
check("one pattern for every id: the id returned matches it whole, a lower-case or short one does not",
      PATTERN.fullmatch(game_id(rafa)) is not None and PATTERN.fullmatch(game_id(rafa).lower()) is None
      and PATTERN.fullmatch(game_id(rafa)[:-1]) is None and PATTERN.fullmatch(game_id(rafa) + "0") is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
