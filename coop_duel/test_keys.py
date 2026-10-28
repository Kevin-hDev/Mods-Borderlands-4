"""The two keys (keys.py): F9 opens the window; N starts the duel, then stops it; N does nothing while the window is
open; a start N cannot make says why on the screen, nothing changed; a saved key that is no key read as the default,
a saved key given to the SDK's keybind; a key already used by the other shortcut found; the window's closing watch on
the opening key, deaf until the key is first up. And the message's look: the title on a cyan plate, the names in white
and the score in orange on the dark panel framed in cyan."""

import sys

import sdk_stubs

state = sdk_stubs.install()

import panel_fixture  # noqa: E402

panel_fixture.install()

import game_fixture  # noqa: E402

game = game_fixture.install(state)
panel_fixture.Widget.RemoveFromParent = lambda self: setattr(self, "on_screen", False)

import coop_duel  # noqa: E402
from coop_duel import banner, control_window, duel, keys  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def lines(event: str) -> list[dict]:
    return [line for line in game_fixture.duel_lines(state) if line["event"] == event]


def shown_texts() -> list:
    """The widgets of the message on the screen, from its holder on."""
    holders = [holder for holder in game.screen.added if getattr(holder, "on_screen", False)]
    if not holders:
        return []
    made = panel_fixture.Widget.created
    return made[made.index(holders[-1]):]


def message() -> str:
    return " | ".join(widget.calls["SetText"][0] for widget in shown_texts() if widget.kind == "TextBlock")


opened: list[bool] = []
control_window.start = lambda *_args: opened.append(True)
keys.OPEN.bind.press()
check("F9 opens the window", opened == [True] and lines("key pressed")[-1]["key"] == "open_key")

host = game_fixture.Character("OakCharacter_1", "Kevin", local=True)
guest = game_fixture.Character("OakCharacter_2", "Venus")
game.seat(host)
keys.DUEL.bind.press()
check("a start N cannot make says why on the screen, nothing changed", duel.live() is None
      and message().startswith("CO-OP DUEL | No other player in your game"))

game.seat(host, guest)
keys.DUEL.bind.press()
check("N starts the duel", duel.live() is not None and message() == "DUEL | Kevin | 0 - 0 | Venus")
panel = [widget for widget in shown_texts() if widget.kind == "Border"]
words = [widget for widget in shown_texts() if widget.kind == "TextBlock"]
colour = coop_duel.panel_widgets.linear
check("the title on a cyan plate, the dark panel framed in cyan", [box.calls["SetBrushColor"][0] for box in panel] == [
    colour(banner.CYAN), colour(banner.CYAN), colour(banner.PANEL, banner.PANEL_ALPHA)])
check("the names in white, the score in orange, the title dark", [
    word.calls["SetColorAndOpacity"][0].SpecifiedColor for word in words] == [
    colour(banner.PLATE_TEXT), colour(banner.WHITE), colour(banner.ORANGE), colour(banner.WHITE)])

control_window.active = lambda: True
keys.DUEL.bind.press()
check("N does nothing while the window is open", duel.live() is not None
      and lines("duel key ignored")[-1]["why"] == "window_open")
control_window.active = lambda: False
keys.DUEL.bind.press()
check("N again stops the duel", duel.live() is None and lines("duel over")[-1]["why"] == "stopped"
      and game.teams.GetTeam(guest).name == "Team_Player")

keys.DUEL.option.value = "Escape"
check("a saved key that is no key read as the default", keys.DUEL.key() == "N")
keys.DUEL.option.value = "K"
check("a saved key given to the SDK's keybind", keys.align() and keys.DUEL.bind.key == "K"
      and not keys.align())
check("a key already used by the other shortcut found", keys.taken_by_other(keys.DUEL, "F9")
      and not keys.taken_by_other(keys.DUEL, "K") and not keys.taken_by_other(keys.OPEN, "F9"))
watch = keys.closer()
check("the window's closing watch on the opening key, deaf until it is first up", watch is not None
      and watch.key == 0x78 and watch.muted)

shown_ok = banner.Banner()
screens = banner.unrealsdk.find_all
banner.unrealsdk.find_all = lambda _name: []
shown_ok.show(object(), "DUEL", 0.0, sentence="x")
shown_ok.show(object(), "DUEL", 0.0, sentence="x")
banner.unrealsdk.find_all = screens
adding = game.screen.AddWidget
game.screen.AddWidget = lambda _holder, _slot: False
shown_ok.show(object(), "DUEL", 0.0, sentence="x")
game.screen.AddWidget = adding
failed = [line["why"] for line in lines("message not shown")]
check("each kind of message failure said once, a new kind said too", failed.count("no_viewport") == 1
      and failed.count("refused") == 1)

print(f"RESULTAT: {'OK' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
