"""The spread of the distances at which It Follows puts its enemies behind the hunter (decision 66). Kevin, 14 October
2026, after trial 14: « éviter de toujours faire pop à la même distance, ça crée surtout un énorme effet de groupe ».

Each enemy put behind him, born again (copies.py) or brought back (catch_up.py), takes the next offset of its level's
spread (levels.py), added to the distance it would have had. The offsets come in turn by a smooth weighted round robin:
over each round of the shares' total, each offset comes as often as its share, and the offsets are interleaved rather
than in runs, so that the enemies of one second already stand at several distances.
"""


class Spread:
    """The offsets of shares, ((share, metres), ...), in turn."""

    def __init__(self, shares: tuple) -> None:
        self.shares = shares
        self.total = sum(share for share, _ in shares)
        self.credit = [0] * len(shares)

    def next(self) -> float:
        """The next offset, in metres: the share most owed its turn, the first one listed among equals."""
        for index, (share, _) in enumerate(self.shares):
            self.credit[index] += share
        chosen = max(range(len(self.shares)), key=self.credit.__getitem__)
        self.credit[chosen] -= self.total
        return self.shares[chosen][1]
