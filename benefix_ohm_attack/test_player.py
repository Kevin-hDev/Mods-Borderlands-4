"""Tests the player's reading: his body on foot and his level."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import player, report  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("no player gives no character", player.current() == (None, None))
pc, character = sdk_stubs.player(state, level=37)
check("a player on foot is found", player.current() == (pc, character))
check("the level is the Character track's, not another's", player.level(pc) == 37)
pc.PlayerState.ExperienceState = [types.SimpleNamespace(ExperienceId="{Name: 'Specialization'}", ExperienceLevel=3)]
check("no Character track counts as level 1, said once", player.level(pc) == 1 and player.level(pc) == 1
      and len(state["errors"]) == 1)

report.reset()


class Broken:
    @property
    def ExperienceState(self):
        raise RuntimeError("no state")


pc.PlayerState = Broken()
errors = len(state["errors"])
check("a level the game will not give counts as level 1, said once, and stops nothing",
      player.level(pc) == 1 and player.level(pc) == 1 and len(state["errors"]) == errors + 1)
report.reset()
tracks = [types.SimpleNamespace(ExperienceId="{Name: 'Other'}", ExperienceLevel=2) for _ in range(40)]
tracks.append(types.SimpleNamespace(ExperienceId="{Name: 'Character'}", ExperienceLevel=50))
pc.PlayerState = types.SimpleNamespace(ExperienceState=tracks)
check("no more tracks are read than the game ever held: one too far down the list is not looked for",
      player.MAX_TRACKS == 12 and player.level(pc) == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
