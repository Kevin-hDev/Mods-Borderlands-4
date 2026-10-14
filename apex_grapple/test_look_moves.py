"""Tests look_moves.py: the left arm comes in, stays stretched while the hook flies, folds with the pull at the more
advanced of its way and its time, never back and never in a jump, finishes and goes out at the end; the body flies
from the catch to the end; the right weapon comes back before the ends the grapple foresees, at the end for the
others; at the settings' bounds (5 and 100 m, 10 and 300 m/s, 2 and 80 m/s, 0 and 15 s, 0.2 and 20 m)."""

import importlib.util
import math
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

# Loaded on its own, outside its package and with no fake SDK: the moves are numbers only.
_spec = importlib.util.spec_from_file_location("look_moves", HERE / "apex_grapple" / "look_moves.py")
moves = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(moves)

fails = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


S = moves.NS_PER_S
FRAME = S // 60
ENTRY_S, EXIT_S = 0.4, 0.3


def pull_run(distance, hook_speed, pull_speed, near, longest_s=0.0, stuck_s=0.0, end_early_at=None):
    """A shot flown and pulled in a straight line at `pull_speed` cm/s, the player rising in place for `stuck_s`
    first; returns every frame's (time in s, pose, gap) and the frame the right weapon came back."""
    run = moves.Moves(ENTRY_S, EXIT_S, 0, longest_s)
    now, flight_ns = 0, int(distance / hook_speed * S)
    seen = []
    while now < flight_ns:
        seen.append((now / S, run.frame(now), distance))
        now += FRAME
    run.catch(now, distance, near, pull_speed)
    caught, gap = now, distance
    while True:
        rising = (now - caught) / S < stuck_s
        velocity = (0.0, 0.0, pull_speed) if rising else (pull_speed, 0.0, 0.0)
        pose = run.frame(now, moves.Pull((gap, 0.0, 0.0), velocity))
        seen.append((now / S, pose, gap))
        over = gap <= near or (longest_s and (now - caught) / S >= longest_s)
        if over or (end_early_at is not None and (now - caught) / S >= end_early_at):
            break
        if not rising:
            gap -= pull_speed / 60
        now += FRAME
    run.end(now)
    for _ in range(120):
        now += FRAME
        seen.append((now / S, run.frame(now), gap))
    return seen


def folds(seen):
    return [pose.fold for _t, pose, _gap in seen]


def jumps(seen):
    """The largest step of the fold between two frames, against the fastest allowed."""
    values = folds(seen)
    return max(b - a for a, b in zip(values, values[1:])) * moves.RUSH_S * 60


def came_back_ahead(seen):
    """Seconds between the right weapon coming back and the last frame of the pull."""
    back = next(t for t, pose, _ in seen if not pose.right_away)
    last_pull = max(t for t, pose, _ in seen if pose.flight is not None)
    return last_pull - back


# A shot at 20 m, hook at 50 m/s, pulled at 15 m/s, let go 2 m from the anchor.
usual = pull_run(2000.0, 5000.0, 1500.0, 200.0)
check("the arm comes in at the shot, and is still coming in just before ENTRY_S",
      usual[0][1].left == (moves.ENTRY, 0.0) and usual[23][1].left[0] == moves.ENTRY)
check("the arm stays stretched while the hook flies, and the legs are the game's",
      all(pose.left == (moves.FOLD, 0.0) and pose.flight is None for t, pose, _ in usual if ENTRY_S <= t < 0.4))
check("the fold never goes back", all(b >= a for a, b in zip(folds(usual), folds(usual)[1:])))
check("the fold never jumps", jumps(usual) <= 1.0 + 1e-9)
check("the arm is folded all the way at the arrival",
      max(pose.fold for _t, pose, gap in usual if pose.flight is not None) > 0.97)
check("the body flies from the catch to the end, following the fold",
      all(pose.flight == pose.fold for _t, pose, _ in usual if pose.flight is not None)
      and any(pose.flight is not None for _t, pose, _ in usual))
check("after the end the arm goes out, then it is gone",
      [phase for phase in dict.fromkeys(pose.left[0] for _t, pose, _ in usual)]
      == [moves.ENTRY, moves.FOLD, moves.EXIT, moves.GONE])
exit_frames = [t for t, pose, _ in usual if pose.left[0] == moves.EXIT]
check("the exit lasts the animation's own EXIT_S",
      abs(exit_frames[-1] - exit_frames[0] + 1 / 60 - EXIT_S) < 2 / 60)
check("the right weapon is away from the shot and back just before the arrival",
      usual[0][1].right_away and 0.0 < came_back_ahead(usual) <= moves.RETURN_S + 2 / 60)

stuck = pull_run(2000.0, 5000.0, 1500.0, 200.0, stuck_s=1.0)
check("a way that stays at nothing for a second: time takes over, the arm still folds",
      max(pose.fold for t, pose, _ in stuck if pose.flight is not None and t < 0.4 + 1.0) > 0.5)

slow = pull_run(10000.0, 5000.0, 200.0, 200.0, longest_s=15.0)
check("a long slow pull (100 m at 2 m/s) folds at its own pace, not in one second",
      next(pose.fold for t, pose, _ in slow if t >= 2.0 + 1.0) < 0.2)
check("a long slow pull ends at the longest pull, the weapon back just before",
      0.0 < came_back_ahead(slow) <= moves.RETURN_S + 2 / 60)

fast = pull_run(500.0, 30000.0, 8000.0, 20.0)
check("a short fast shot (5 m, 300 m/s, 80 m/s): the hook bites while the arm comes in, and the arm catches up "
      "without a jump", jumps(fast) <= 1.0 + 1e-9 and fast[-1][1].left == (moves.GONE, 1.0))

first_fold = next(pose.fold for _t, pose, _ in fast if pose.left[0] == moves.FOLD)
check("the arm takes up the fold where its entry left it, at F, not where the pull already is",
      first_fold <= 1.0 / (60 * moves.RUSH_S) + 1e-9)

steered = moves.Moves(ENTRY_S, EXIT_S, 0)
steered.frame(0)
steered.catch(S, 2000.0, 200.0, 1500.0)
closer = steered.frame(S + 30 * FRAME, moves.Pull((800.0, 0.0, 0.0), (1500.0, 0.0, 0.0)))
farther = steered.frame(S + 31 * FRAME, moves.Pull((1900.0, 0.0, 0.0), (-1500.0, 0.0, 0.0)))
check("steered away from the anchor: the arm waits, it never unfolds (choice 4)",
      closer.fold > 0.0 and farther.fold >= closer.fold)

far_arrival = pull_run(10000.0, 1000.0, 1500.0, 2000.0)
check("a slow hook (100 m at 10 m/s): the arm waits stretched the whole ten seconds of flight",
      all(pose.left == (moves.FOLD, 0.0) for t, pose, _ in far_arrival if ENTRY_S <= t < 9.9))
check("an arrival 20 m before the anchor folds all the way there",
      max(pose.fold for _t, pose, _ in far_arrival if pose.flight is not None) > 0.97)

let_go = pull_run(3000.0, 5000.0, 1500.0, 200.0, end_early_at=0.5)
check("let go halfway: the weapon comes back at the end, the arm finishes its fold then goes out",
      came_back_ahead(let_go) <= 1 / 60 and let_go[-1][1].left == (moves.GONE, 1.0)
      and jumps(let_go) <= 1.0 + 1e-9)

called_off = moves.Moves(ENTRY_S, EXIT_S, 0)
called_off.frame(0)
called_off.end(int(0.2 * S))
trail = [called_off.frame(n * FRAME) for n in range(1, 120)]
check("called off while the hook flies: the body never flies, the arm comes in, folds and goes out",
      all(pose.flight is None for pose in trail) and trail[-1].left == (moves.GONE, 1.0)
      and not trail[0].right_away)

passing = moves.Moves(ENTRY_S, EXIT_S, 0)
passing.frame(0)
passing.catch(S, 1000.0, 20.0, 1500.0)
pose = passing.frame(S + FRAME, moves.Pull((100.0, 300.0, 0.0), (1500.0, 0.0, 0.0)))
check("an anchor about to be passed, 300 cm aside: the weapon comes back before it", not pose.right_away)
away = passing.frame(S + 2 * FRAME, moves.Pull((800.0, 300.0, 0.0), (1500.0, 0.0, 0.0)))
check("once back, the weapon stays back", not away.right_away)

held = moves.Moves(ENTRY_S, EXIT_S, 0, 0.0)
held.frame(0)
held.catch(S, 1000.0, 20.0, 1500.0)
check("no longest pull (0) and the anchor out of reach: the weapon stays away",
      held.frame(S + 60 * FRAME, moves.Pull((900.0, 0.0, 0.0), (-10.0, 0.0, 0.0))).right_away)

print(f"RESULTAT: {'TOUS LES TESTS PASSENT' if not fails else f'{len(fails)} ECHEC(S)'}")
raise SystemExit(1 if fails else 0)
