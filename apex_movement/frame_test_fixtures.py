"""Movement doubles for frame lifecycle regression tests."""

class Movement:
    def __init__(self, broken: bool = False) -> None:
        self.updates, self.stops, self.resets, self.broken = 0, 0, 0, broken

    def update(self, character: object, now_ns: int) -> None:
        if self.broken:
            raise ValueError("boom")
        self.updates += 1

    def stop(self, character: object) -> None:
        self.stops += 1

    def reset(self) -> None:
        self.resets += 1
