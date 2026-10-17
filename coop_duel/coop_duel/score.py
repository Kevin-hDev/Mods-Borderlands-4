"""The duel's score: a round is lost by the player who falls, and won by the other one.

Kevin, 17 October 2026: the score shows as a short message at each round, "Kevin 3 - 2 Venus", the players' names as
the game shows them, on the host's screen (docs/duel/README.md, décisions). Any fall counts, whoever caused it: an
enemy around can knock a player down too, and he then loses the round (default chosen while writing the mod, to be
confirmed by Kevin).
"""

from dataclasses import dataclass

HOST, GUEST = "host", "guest"
# A duel has no end (Kevin, 17 October 2026); the bound only keeps a count from growing without limit.
MAX_POINTS = 9999


@dataclass
class Score:
    host_name: str
    guest_name: str
    host: int = 0
    guest: int = 0

    def fell(self, side: str) -> None:
        """The player on side fell: the other wins the round."""
        if side == HOST:
            self.guest = min(self.guest + 1, MAX_POINTS)
        elif side == GUEST:
            self.host = min(self.host + 1, MAX_POINTS)
        else:
            raise ValueError(f"no side {side!r}")

    @property
    def rounds(self) -> int:
        return self.host + self.guest

    def points(self) -> str:
        return f"{self.host} - {self.guest}"

    def parts(self) -> tuple[str, str, str]:
        """What the message on the screen shows: the host's name, the points, the guest's name."""
        return self.host_name, self.points(), self.guest_name
