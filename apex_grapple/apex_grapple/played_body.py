"""Which animation update is the player's, without asking the game at each one.

The frame hook runs on the animation update, called for every animated character in the world: up to about 1,500
calls a second in a Horde (It Follows trial 40). Each call asked the game for the controller and the character before
it could be told apart from an enemy's (docs/performance/enquetes/2026-10-24-cout-apex-grapple.md). The player's body
confirmed last is remembered instead:
- every update from the object holding it, its mesh, is still checked against the game, as before: its own update,
  and a new body's on the same character;
- any other update goes by without a question while the player's body updated less than RECENT_NS ago.
Once the player's body has been quiet that long (a new character, a vehicle, the title screen), every update asks
again.
"""

from typing import Any

# Longer than a frame down to 20 images a second, so in play no other character's update asks. Its price, the one
# difference with asking at every update, accepted by Kevin on 2026-10-24: after a change of character, or on leaving
# the game, the rope is put down and the window closed up to 50 ms later, during the game's own transition.
RECENT_NS = 50_000_000


def address(item: Any) -> int:
    return int(item._get_address()) if item is not None else 0


class PlayedBody:
    def __init__(self) -> None:
        self.forget()

    def forget(self) -> None:
        self.body = self.holder = self.seen_ns = 0

    def remember(self, body: int, holder: int, now_ns: int) -> None:
        """body and holder: the addresses of the body just confirmed against the game and of its outer, its mesh."""
        self.body, self.holder, self.seen_ns = body, holder, now_ns

    def must_ask(self, obj: Any, now_ns: int) -> bool:
        if not self.body or now_ns - self.seen_ns >= RECENT_NS:
            return True
        return address(getattr(obj, "Outer", None)) == self.holder
