"""What decides a round, without the game (Kevin, 17 October 2026, docs/duel/spec-equipes.md): the last team with a
player standing wins it; when none has one, the last ones fell at the same step of the duel and the round is a draw.
Choosing the last team standing spares the mod knowing who knocked whom down, which the game does not tell it."""

GOING, DRAW = "going", "draw"


def outcome(standing: dict[int, int]) -> int | str:
    """standing: each team still in the duel and how many of its players stand. GOING while two teams or more have
    one, the team's number when a single one has, DRAW when none has."""
    up = sorted(team for team, count in standing.items() if count > 0)
    if len(up) > 1:
        return GOING
    return up[0] if up else DRAW
