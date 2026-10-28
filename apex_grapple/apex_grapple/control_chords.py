"""Bounded input state for one-key bindings and unordered two-key chords."""


class Chords:
    def __init__(self, groups: tuple[tuple[str, ...], ...]) -> None:
        self.groups = tuple(frozenset(group) for group in groups)
        self.known = frozenset(key for group in groups for key in group)
        self.clear()

    def clear(self) -> None:
        self.down: set[str] = set()
        self.active: frozenset[str] = frozenset()

    def feed(self, key: str, event: str) -> tuple[bool, bool]:
        if key not in self.known:
            return False, False
        if event == "IE_Released":
            self.down.discard(key)
            released = key in self.active
            if released:
                self.active = frozenset()
            return False, released
        if event != "IE_Pressed" or key in self.down:
            return False, False
        self.down.add(key)
        for group in self.groups:
            if key in group and group <= self.down:
                self.active = group
                return True, False
        return False, False
