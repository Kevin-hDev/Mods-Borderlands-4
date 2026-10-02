"""Tests the game's beat: the hook on the arms' animation update, which is the attack's one way in."""

import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import attack, frame  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


# The function hooked is a fact read in game (heirloom probes; 30 shots in third person on 2026-10-01): another
# one would leave the attack without a beat, so the test holds its very name.
check("the hook is on the first-person arms' animation update, after it has run",
      frame.tick.path == "/Game/PlayerCharacters/_Shared/Animation/BPAnim_Player_1st.BPAnim_Player_1st_C"
                         ":BlueprintUpdateAnimation" and frame.tick.kind == "post")
check("its name is the mod's own: it never replaces another mod's hook", frame.tick.identifier == "benefix_ohm_attack:frame")

seen: list[float] = []
real, attack.on_frame = attack.on_frame, seen.append
before = time.perf_counter()
frame.tick.run(None, None, None, None)
frame.tick.run(None, None, None, None)
after = time.perf_counter()
attack.on_frame = real
check("each update is one frame of the attack, told the time on a clock that never goes back",
      len(seen) == 2 and before <= seen[0] <= seen[1] <= after)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
