"""The mod: built under its public name with its version and the frame hook; on at its first launch; its window opened
from the SDK's mod menu; turned on, the character in play handled again; turned off, the hook stopped and the own
look given back, the choices kept; turned off during a hunter change asked in a game, the request dropped and nothing
written."""

import sys
from types import SimpleNamespace

import sdk_stubs

state = sdk_stubs.install()

import fake_game  # noqa: E402
import hunter_change  # noqa: E402
import save_fixture  # noqa: E402
from hunter_change import choices, leave, lifecycle, panel_preferences, save_places, switch, wardrobe  # noqa: E402

fails: list[str] = []
HARLOWE_GAME = "8107146506D5906AD9BCCD4479661B4D"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


mod = hunter_change.mod
check("built under its public name with its version and the frame hook",
      mod.kwargs["name"] == "Hunter Change" and hunter_change.__version__ == "1.0.5"
      and mod.kwargs["hooks"] == [lifecycle.tick])
check("on at its first launch", mod.is_enabled and lifecycle.tick.enabled)
check("its window opened from the SDK's mod menu, its preferences kept with the mod",
      getattr(mod, "_hunter_change_panel_display_installed", False)
      and mod.kwargs["options"] == list(panel_preferences.ALL))

character = fake_game.load(state, "Gravitar", HARLOWE_GAME)
lifecycle.on_frame(1.0)
wardrobe.wear("CorpoHacker")
mod.disable()
check("turned off, the hook stopped and the own look given back, the choice kept", not lifecycle.tick.enabled
      and fake_game.body_drawn(character) == "Cosmetics_Gravitar_Body00_Default"
      and choices.chosen(HARLOWE_GAME) == choices.Choice("CorpoHacker"))
mod.enable()
lifecycle.on_frame(2.0)
check("turned on, the character in play handled again",
      fake_game.body_drawn(character) == "Cosmetics_CorpoHacker_Body00_Default")


class Timer:
    """The Windows timer as leave uses it, never the real one."""
    target = None

    def start(self, target) -> None:
        self.target = target

    def stop(self) -> None:
        self.target = None


# A change asked in the game, waiting at the title screen for its save to stay still; the saves are the fixture's.
documents, client = save_fixture.saves_folder()
save_places.documents_candidates = lambda: [documents]
save_fixture.put(client, 4, save_fixture.game_text(HARLOWE_GAME, "Gravitar", "Harlowe", None))
changes: list = []
switch.change = lambda *args, **kwargs: changes.append(args) or switch.Outcome(switch.DONE)
timer = Timer()
leave.new_timer, leave.now = (lambda: timer), (lambda: 0.0)
leave.live_modes = lambda: [SimpleNamespace(ReturnToMainMenuHost=lambda: None)]
asked = leave.ask(HARLOWE_GAME, "Gravitar", "Paladin")
timer.target()
state["pc"] = SimpleNamespace(OakCharacter=None,
                              PlayerState=SimpleNamespace(ActiveCharGuid=fake_game.id_words(HARLOWE_GAME)))
leave.ready(None, None, None, None)
timer.target()
waiting = leave.busy()
mod.disable()
check("turned off during a hunter change asked in a game: the request dropped, nothing written",
      asked and waiting and not leave.busy() and not changes and not leave.ready.enabled and timer.target is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
