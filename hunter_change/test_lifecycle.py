"""The lifecycle: nothing without a character; a new character dressed for its game once, later frames leaving it
alone; a game not ready yet tried again after a pause, then dressed; the wait given up after its bound, said once; a
failed look tried again after a pause, given up after its bound, said once; a new character dressed again; a reset
dressing the character again; an error inside never leaving the frame hook."""

import sys

import sdk_stubs

state = sdk_stubs.install()

import fake_game  # noqa: E402
from fake_game import handed, rule  # noqa: E402
from hunter_change import choices, lifecycle, wardrobe  # noqa: E402

fails: list[str] = []
HARLOWE_GAME = "8107146506D5906AD9BCCD4479661B4D"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


calls: list[str] = []
real_settle = wardrobe.settle


def counted(character: object, player_state: object) -> str:
    calls.append("settle")
    return real_settle(character, player_state)


wardrobe.settle = counted

lifecycle.on_frame(0.0)
check("nothing without a character", not calls)

choices.choose(HARLOWE_GAME, "Paladin")
character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
lifecycle.on_frame(1.0)
lifecycle.on_frame(1.1)
lifecycle.on_frame(50.0)
check("a new character dressed for its game once, later frames leaving it alone", calls == ["settle"]
      and fake_game.body_drawn(character) == "Cosmetics_Paladin_Body00_Default")

character = fake_game.load(state, "Gravitar", "0" * 32)
calls.clear()
lifecycle.on_frame(60.0)
lifecycle.on_frame(60.0 + lifecycle.WAIT_S / 2)
first = len(calls)
state["pc"].PlayerState.ActiveCharGuid = fake_game.id_words(HARLOWE_GAME)
lifecycle.on_frame(60.0 + lifecycle.WAIT_S)
lifecycle.on_frame(60.0 + 2 * lifecycle.WAIT_S)
check("a game not ready yet tried again after a pause, then dressed", first == 1 and len(calls) == 2)

character = fake_game.load(state, "Gravitar", "0" * 32)
calls.clear()
now = 100.0
while now < 100.0 + lifecycle.MAX_WAIT_S + 5 * lifecycle.WAIT_S:
    lifecycle.on_frame(now)
    now += lifecycle.WAIT_S
waited = len(calls)
lifecycle.on_frame(now + 1000.0)
check("the wait given up after its bound, said once", len(calls) == waited
      and waited <= lifecycle.MAX_WAIT_S / lifecycle.WAIT_S + 2
      and sum("gave up" in error for error in state["errors"]) == 1)

character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
# Harlowe's pickers are still Amon's from the first game: given back their own, the look has to be put on again.
fake_game.pickers_of("Gravitar")[0].DefaultPart._name = "Cosmetics_Gravitar_Body00_Default"
rule["setter_refused"] = True
calls.clear()
now = 2000.0
for _ in range(lifecycle.MAX_TRIES * 3):
    lifecycle.on_frame(now)
    now += lifecycle.RETRY_S / 2
check("a failed look tried again after a pause, given up after its bound",
      len(calls) == lifecycle.MAX_TRIES and sum("could not" in error for error in state["errors"]) == 1)
rule["setter_refused"] = False

character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
calls.clear()
lifecycle.on_frame(5000.0)
check("a new character dressed again", calls == ["settle"]
      and fake_game.body_drawn(character) == "Cosmetics_Paladin_Body00_Default")
lifecycle.reset()
lifecycle.on_frame(5001.0)
check("a reset dressing the character again", calls == ["settle", "settle"])

wardrobe.settle = lambda *_args: 1 / 0
fake_game.load(state, "Gravitar", HARLOWE_GAME)
lifecycle.tick(None, None, None, None)
check("an error inside never leaving the frame hook", any("ZeroDivisionError" in error for error in state["errors"]))
wardrobe.settle = real_settle
handed.clear()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
