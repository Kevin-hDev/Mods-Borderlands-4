"""What sends the turned body back to the crosshair: a shot, a punch, a grenade or the skill (Kevin, 2026-10-09).

Whenever the hunter acts, the body turns to the crosshair, and back to the run HOLD_NS after the last action. Trial 4
read the game's keys through the SDK's key bindings and the game's state; here the keys are read by their state each
frame, as Free Look reads its own (free_look.py), so nothing is bound and nothing can block a key. The keys come from
the game's own input list, read again every second, so they follow the player's choices.
"""

from typing import Any, Callable

# Every action named after a shot, a punch, a grenade (Gadget) or the skill in the input list (2026-09-16). Not
# Action_GadgetDoubleTap: its key is ComboKey, no key of its own.
ACTIONS = ("Action_Fire", "Action_Melee", "Action_Melee_1s", "Action_Gadget", "Action_GadgetHold", "Action_Skill",
           "Action_Skill_Infinite", "Action_Skill_Hold_p5s", "Action_Skill_Hold_1s", "Action_Skill_Hold_1p5s",
           "Action_Skill_PressRelease")
# About a second, agreed by Kevin on 2026-10-09; tuned in the final session.
HOLD_NS = 1_000_000_000
KEYS_CHECK_NS = 1_000_000_000
# Bounded: a keyboard and a controller key per action at most.
MAX_KEYS = 32


def action_keys(mappings: Any, actions: tuple[str, ...] = ACTIONS) -> tuple[str, ...]:
    """The keys the game binds to one of actions, sorted, at most MAX_KEYS."""
    found = set()
    for mapping in mappings:
        action = mapping.Action
        if action is not None and str(action.Name) in actions:
            found.add(str(mapping.Key.KeyName))
    return tuple(sorted(found))[:MAX_KEYS]


class Actions:
    def __init__(self, make_key: Callable[[str], Any], log: Callable[[str], None]) -> None:
        self.make_key, self.log = make_key, log
        self.keys: dict[str, Any] = {}
        self.listed = False
        self.next_keys_ns = 0
        self.until_ns = 0
        self.left_out: set[str] = set()

    def reset(self) -> None:
        self.until_ns, self.next_keys_ns = 0, 0

    def _follow_keys(self, pc: Any, now_ns: int) -> None:
        if now_ns < self.next_keys_ns:
            return
        self.next_keys_ns = now_ns + KEYS_CHECK_NS
        names = action_keys(pc.PlayerInput.EnhancedActionMappings)
        if not self.listed or tuple(sorted(self.keys)) != names:
            self.listed = True
            self.keys = {name: self.make_key(name) for name in names}
            self.log("action keys " + (" ".join(names) if names else "none: only shots turn the body"))

    def _read(self, name: str, read: Callable[[], Any]) -> Any:
        if name in self.left_out:
            return None
        try:
            return read()
        except Exception as exc:
            # One signal the game will not give is left out for the session; the others go on.
            self.left_out.add(name)
            self.log(f"{name} signal unreadable, left out: {type(exc).__name__}")
            return None

    def acting(self, pc: Any, anim: Any, now_ns: int) -> bool:
        """Whether the body should face the crosshair now."""
        self._read("keys", lambda: self._follow_keys(pc, now_ns))
        down = "keys" not in self.left_out and bool(
            self._read("key states", lambda: any(bool(pc.IsInputKeyDown(key)) for key in self.keys.values())))
        # The weapon's own state too, in case a key is missed; the melee counter never moved in solo play (trial 4).
        firing = bool(self._read("firing", lambda: anim.bIsFiring))
        if down or firing:
            self.until_ns = now_ns + HOLD_NS
        return now_ns < self.until_ns
