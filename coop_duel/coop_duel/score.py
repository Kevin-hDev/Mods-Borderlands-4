"""The duel's score (Kevin, 17 October 2026, docs/duel/spec-equipes.md): a point to the team that wins a round, none
for a draw, and the line that shows it on the host's screen and in the window, model A. With two teams, each team's
names joined by "+" around the points, "Kevin + Raph  2 - 1  Venus + Lina", the 1.0.0 message in one against one;
with three or more, each team followed by its points, "Kevin  1  ·  Venus  2  ·  Raph  1". Past two players each name
is cut, so that four hold on one line. Any fall counts, whoever caused it: an enemy around can knock a player down too
(default chosen while writing 1.0.0)."""

from dataclasses import dataclass, field

NAME, POINTS, SEPARATOR = "name", "points", "separator"
# A duel has no end (Kevin, 17 October 2026); the bound only keeps a count from growing without limit.
MAX_POINTS = 9999
# Past two players, a name is cut to this many characters and an ellipsis: four names must hold on one line.
SHORT_NAME = 14
CUT = "…"
JOIN, BETWEEN, GAP = " + ", "·", "  "


def _short(name: str) -> str:
    return name if len(name) <= SHORT_NAME else name[:SHORT_NAME] + CUT


@dataclass
class Score:
    """teams: by team number, its players' names by their number J; points: by team number."""
    teams: dict[int, dict[int, str]]
    points: dict[int, int] = field(default_factory=dict)
    rounds: int = 0

    def won(self, team: int) -> None:
        self.rounds += 1
        self.points[team] = min(self.points.get(team, 0) + 1, MAX_POINTS)

    def draw(self) -> None:
        self.rounds += 1

    def left(self, team: int, number: int) -> None:
        """A player gone: his name off the line, his team off it once empty; its points stay in the log."""
        names = self.teams.get(team, {})
        names.pop(number, None)
        if not names:
            self.teams.pop(team, None)

    def alone(self, team: int) -> str | None:
        """The name of the team's one player; None when it has several or none."""
        names = list(self.teams.get(team, {}).values())
        return names[0] if len(names) == 1 else None

    def line(self) -> list[tuple[str, str]]:
        """The line's parts in order, each its text and its kind."""
        many = sum(len(names) for names in self.teams.values()) > 2
        shown = [(team, JOIN.join(_short(name) if many else name for _number, name in sorted(names.items())))
                 for team, names in sorted(self.teams.items())]
        if len(shown) == 2:
            (first, left), (second, right) = shown
            points = f"{self.points.get(first, 0)} - {self.points.get(second, 0)}"
            return [(left, NAME), (points, POINTS), (right, NAME)]
        parts: list[tuple[str, str]] = []
        for index, (team, names) in enumerate(shown):
            if index:
                parts.append((BETWEEN, SEPARATOR))
            parts += [(names, NAME), (str(self.points.get(team, 0)), POINTS)]
        return parts

    def text(self) -> str:
        """The line as the window shows it."""
        return GAP.join(text for text, _kind in self.line())
