"""The mod: built under its public name with its version, the frame hook, the window's preferences and its two keys,
F9 and N at first, each keybind given its key; on at its first launch; its window opened from the SDK's mod menu; switched off, the hook stopped; switched on again, the hook back."""

import sys

import sdk_stubs

state = sdk_stubs.install()

import coop_duel  # noqa: E402
from coop_duel import heartbeat, keys, panel_preferences  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


mod = coop_duel.mod
check("built under its public name with its version, the frame hook, the window's preferences and its two keys",
      mod.kwargs["name"] == "Co-op Duel" and coop_duel.__version__ == "1.0.0"
      and mod.kwargs["hooks"] == [heartbeat.tick]
      and mod.kwargs["options"] == [*panel_preferences.ALL, keys.OPEN.option, keys.DUEL.option]
      and mod.kwargs["keybinds"] == [keys.OPEN.bind, keys.DUEL.bind])
check("F9 and N at first, each keybind given its key", (keys.OPEN.key(), keys.DUEL.key()) == ("F9", "N")
      and (keys.OPEN.bind.key, keys.DUEL.bind.key) == ("F9", "N"))
check("on at its first launch", mod.is_enabled and heartbeat.tick.enabled)
check("its window opened from the SDK's mod menu", getattr(mod, "_coop_duel_panel_display_installed", False))
mod.disable()
check("switched off, the hook stopped", not heartbeat.tick.enabled and any("disabled" in line for line in state["logs"]))
mod.enable()
check("switched on again, the hook back", heartbeat.tick.enabled)

print(f"RESULTAT: {'OK' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
