"""Tests the mod as the SDK sees it: what it registers, and what switching it on and off does."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
import benefix_ohm_attack  # noqa: E402
from benefix_ohm_attack import bar, damage, frame, hand, keys, report, settings  # noqa: E402

fails: list[str] = []
PRESSED = "EInputEvent.IE_Pressed"
PALM = (10.0, -20.0, 40.0)


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


mod = state["mods"][0]
check("the mod registers its frame hook, its two keys, its settings and its keys' options",
      mod.name == "Benefix Ohm Attack" and mod.hooks == [frame.tick]
      and mod.keybinds == [keys.keyboard_bind, keys.controller_bind]
      and mod.options[:len(settings.ALL) + 2] == [*settings.ALL, keys.keyboard_key, keys.controller_key])
check("a mod with no settings file to look at is left as the SDK made it: off", mod.is_enabled is False)

# Everything a session may leave behind: a hit the game refused, a hand that could not be read, an error already
# said, a key held, and a bind whose key is not its option's.
pc, character = sdk_stubs.player(state)
enemy = sdk_stubs.aim_at(state, "Char_Psycho_7")
state["hit_raises"] = RuntimeError("the game refuses")
damage.hit(character, enemy, None, 1.0, "Fire")
state["hit_raises"] = None
sockets = dict(state["sockets"])
state["sockets"].clear()
hand.spot(pc, character)
state["sockets"].update(sockets)
report.error_once("said before", "an error of the last session")
keys.keyboard_key.value = "N"
keys.keyboard_bind.key = "Stale"
keys.keyboard_bind.callback(PRESSED)
check("before: the hit is refused, the hand is unread, the key is held",
      damage.refused() and hand.spot(pc, character) != PALM and keys.held())

# Port 0: the system picks a free one, so the test never takes the port Kevin's game uses.
bar.PORT = 0
errors = len(state["errors"])
mod.on_enable()
check("switching the mod on says so, with its version",
      f"[Benefix Ohm Attack] enabled, version {benefix_ohm_attack.__version__}" in state["log"])
check("a hit refused before is tried again", not damage.refused())
check("the hand is looked for again", hand.spot(pc, character) == PALM)
report.error_once("said before", "an error of the last session")
check("an error said before is said again", len(state["errors"]) == errors + 1)
check("each bind has its option's key, and nothing is held from before",
      keys.keyboard_bind.key == "N" and not keys.held())
check("the energy bar's service is started", bar._service is not None)

mod.on_disable()
check("switching it off stops the service and says so",
      bar._service is None and state["log"][-1] == "[Benefix Ohm Attack] disabled")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
