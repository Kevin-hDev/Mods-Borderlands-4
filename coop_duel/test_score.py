"""score.py: a point to the round's winning team, none for a draw, the rounds counted; the line, model A: one against
one as 1.0.0, two teams' names joined by "+" around the points, three teams or more each followed by its points
between separators; past two players each name cut to 14 characters; a player gone off the line, his team once
empty; a team's one name; the points bounded."""

import sys

import sdk_stubs

sdk_stubs.install()

from coop_duel import score  # noqa: E402
from coop_duel.score import NAME, POINTS, SEPARATOR, Score  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


duo = Score({1: {1: "Kevin"}, 2: {2: "Venus"}})
duo.won(1)
duo.draw()
check("a point to the winner, none for a draw, the rounds counted", duo.points == {1: 1} and duo.rounds == 2)
check("one against one: the 1.0.0 line", duo.line() == [("Kevin", NAME), ("1 - 0", POINTS), ("Venus", NAME)]
      and duo.text() == "Kevin  1 - 0  Venus")
long_pair = Score({1: {1: "Abcdefghijklmnopq"}, 2: {2: "Venus"}})
check("one against one: names never cut", long_pair.line()[0][0] == "Abcdefghijklmnopq")
pairs = Score({1: {1: "Kevin", 3: "Raph"}, 2: {2: "Venus", 4: "Lina"}})
pairs.won(2)
check("two teams: names joined around the points", pairs.text() == "Kevin + Raph  0 - 1  Venus + Lina")
three = Score({1: {1: "Kevin"}, 2: {2: "Abcdefghijklmnopq"}, 3: {3: "Raph"}})
three.won(2)
check("three teams: each followed by its points, between separators", three.line() == [
    ("Kevin", NAME), ("0", POINTS), ("·", SEPARATOR), ("Abcdefghijklmn…", NAME), ("1", POINTS), ("·", SEPARATOR),
    ("Raph", NAME), ("0", POINTS)])
check("a team's one name; none for a team of several", three.alone(3) == "Raph" and pairs.alone(1) is None)
pairs.left(2, 4)
check("a player gone off the line", pairs.text() == "Kevin + Raph  0 - 1  Venus")
three.left(3, 3)
check("his team off the line once empty, the duel's points kept; two players left, names whole again",
      three.text() == "Kevin  0 - 1  Abcdefghijklmnopq" and three.points == {2: 1})
bounded = Score({1: {1: "A"}, 2: {2: "B"}}, points={1: score.MAX_POINTS})
bounded.won(1)
check("the points bounded", bounded.points[1] == score.MAX_POINTS)

print(f"RESULTAT: {'OK' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
