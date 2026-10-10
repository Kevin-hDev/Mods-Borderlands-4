"""The automatic shoulder swaps away from a wall, comes back once it is clear, and never swings along a rough wall."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.shoulder_auto import BLOCKED, CLEAR, RETURN_S, SWAP_S, AutoShoulder, swap_due  # noqa: E402

fails = []
FRAME = 1 / 60


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def run(auto, seconds, shown, other, chosen=False, allowed=True):
    side = None
    for _ in range(round(seconds / FRAME)):
        side = auto.step(chosen, shown, other, allowed, FRAME)
    return side


check("a blocked side with a free other side is due to swap", swap_due(0.2, 1.0))
check("the swap thresholds are the rule's", not swap_due(BLOCKED, 1.0) and swap_due(0.2, CLEAR)
      and not swap_due(0.2, CLEAR - 0.01) and not swap_due(0.2, None))

auto = AutoShoulder()
check("a clear shoulder stays", run(auto, 2.0, 1.0, 1.0) is False and auto.override is None)
check("a short brush against a wall does not swap", run(auto, SWAP_S - 0.05, 0.2, 1.0) is False)
check("the delay restarts once the shoulder clears", run(auto, FRAME, 1.0, None) is False and auto.blocked_s == 0.0)
check("a wall held on the right shows the left shoulder", run(auto, SWAP_S + 0.02, 0.2, 1.0) is True)
check("the swap remembers the side shown", auto.override is True)

auto = AutoShoulder()
check("both sides cramped: no swap, nowhere better to go", run(auto, 1.0, 0.2, 0.5) is False)
check("the other side unread: no swap", run(auto, 1.0, 0.2, None) is False)
check("half the room kept is not a wall", run(auto, 1.0, 0.5, 1.0) is False)

auto = AutoShoulder()
run(auto, SWAP_S + 0.02, 0.0, 1.0)
check("the chosen side cramped again keeps the swap", run(auto, 2.0, 1.0, 0.3) is True)
check("the chosen side clear for less than the return delay keeps the swap",
      run(auto, RETURN_S - 0.1, 1.0, 1.0) is True)
check("a cramped frame restarts the return delay", run(auto, FRAME, 1.0, 0.5) is True and auto.clear_s == 0.0)
check("the chosen side clear long enough comes back", run(auto, RETURN_S + 0.05, 1.0, 1.0) is False)
check("coming back ends the swap", auto.override is None)

auto = AutoShoulder()
run(auto, SWAP_S + 0.02, 0.0, 1.0)
check("aiming holds the swapped side", run(auto, 3.0, 1.0, 1.0, allowed=False) is True)
check("aiming restarts the delays", auto.clear_s == 0.0 and auto.blocked_s == 0.0)
check("no reading holds the swapped side", run(auto, 3.0, None, None) is True)

auto = AutoShoulder()
check("with no wall the shoulder key has nothing to undo", not auto.player_switch())
run(auto, SWAP_S + 0.02, 0.0, 1.0)
check("the shoulder key during a swap is taken", auto.player_switch())
check("the shoulder key shows the chosen side again", auto.override is None and auto.shown(False) is False)
check("after the key the wall does not swap again", run(auto, 2.0, 0.0, 1.0) is False)
check("the chosen side clearing ends the wait", run(auto, FRAME, 1.0, None) is False and not auto.waiting)
check("a later wall swaps again", run(auto, SWAP_S + 0.02, 0.0, 1.0) is True)

auto = AutoShoulder()
run(auto, SWAP_S + 0.02, 0.0, 1.0, chosen=True)
check("a wall on the left shows the right shoulder", auto.override is False)
check("choosing the swapped side in the menu ends the swap",
      auto.step(False, 1.0, None, True, FRAME) is False and auto.override is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
