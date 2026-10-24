"""Which animation update is the played body's, without asking the game at each one.

The camera mods clock themselves on the animation update, which runs for every animated character in the world, up to
about 1,500 calls a second in a Horde (It Follows trial 40). Finding the played body asks the game for the controller,
the character, its mesh and that mesh's body, and Third Person & FOV and Omni Sprint asked it at every enemy's update
(docs/performance/enquetes/2026-10-24-cout-third-person-fov.md). The body confirmed last is remembered instead:
- every update from the object holding it, its mesh, is still checked against the game, as before: its own update,
  and a new body's on the same character, found at once;
- any other update goes by without a question while the played body updated less than RECENT_NS ago.
Once the played body has been quiet that long, a new character or the title screen, every update asks again.
Here, in the shared package, so that both mods use one copy of it (2026-10-24).
"""

from typing import Any

# Longer than a frame down to 20 images a second, so in play no other character's update asks. Its price, the one
# difference with asking at every update: after a change of character, or on leaving the game, the camera's next
# update can come up to 50 ms later (2026-10-24).
RECENT_NS = 50_000_000


def address(item: Any) -> int:
    return int(item._get_address()) if item is not None else 0


class PlayedBody:
    def __init__(self) -> None:
        self.forget()

    def forget(self) -> None:
        self.body = self.holder = self.seen_ns = 0

    def remember(self, body: int, holder: int, now_ns: int) -> None:
        """body and holder: the addresses of the body just confirmed against the game and of its outer."""
        self.body, self.holder, self.seen_ns = body, holder, now_ns

    def must_ask(self, obj: Any, now_ns: int) -> bool:
        if not self.body or now_ns - self.seen_ns >= RECENT_NS:
            return True
        return address(getattr(obj, "Outer", None)) == self.holder
