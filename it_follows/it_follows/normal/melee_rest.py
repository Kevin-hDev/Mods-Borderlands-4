"""The armed bandits' rest after a blow, shortened to the level's (decision 126, Kevin, 17 October 2026: « Senior 3 a 5
et preda 2 a 3 s c'est bon »; Bandit keeps the game's, the psychos are not touched), given back at the end.

The rest is the SucceededCooldown of the blow's Timer node in each kind of bandit's decision tree (melee_trees.py): a
GbxParam range, its centre and half width at +8 (gbx_param.py), at the offset the SDK gives the field. Trial 66 read
it as the decoded trees give it, 6 / 2 (8 / 2 for the pistol); trial 67 wrote Predator's 2.5 / 0.5 on the seven
trees: a bandit already in the game struck every 2.9 to 4.6 s at contact instead of 7 to 8, and every tree was given
back, without a crash (docs/RUN/enquetes/, vérifié en jeu, once). A tree is shared by every bandit of its kind.

Each pass looks at every tree the game holds, its nodes found again (brain_trees.py): one holding the game's rest
gets the level's, written only over that value and read back, announced before; one holding the level's is kept; one
holding anything else is left and said once. So a tree loaded again, or whose nodes the game made again, gets the
level's at the next pass. A tree found at the level's is held too: a give back missed once (an earlier game ended
short) is made at this one's end. A rest already as short as the level's is never lengthened. A write the game
refuses is not tried again in this game. Each outcome but a write is counted once by tree: a refusal that lasts is
said once, not at every census (audit of 17 October 2026). At the end, every tree still held gets the game's rest
back where the level's still lies. Another version of the game, whose types differ, finds
no tree: nothing is written, and it is said once.
"""

import struct
from typing import Any, Callable

import unrealsdk

from .. import brain_trees, gbx_param, process_memory
from .melee_trees import TREES

TREE_CLASS = "GbxBrainTaskData_AITree"
TIMER = "/Script/GbxAI.GbxBrainAspectSettings_Timer"
FIELD = "SucceededCooldown"
RANGE, VALUE_AT = 11, 8
QUIET = ("not_loaded", "kept", "shorter", "left")


class MeleeRest:
    """rest: the level's (centre, half width), None to leave the game's; note(event, **fields) writes a line;
    announce(call, **fields) a write before it is made."""

    def __init__(self, rest: tuple[float, float] | None, note: Callable[..., None],
                 announce: Callable[..., None]) -> None:
        self.rest, self.note, self.announce = rest, note, announce
        self.memory: Any = None
        self.at: int | None = None
        self.names: dict[str, int] = {}
        # By tree: its weak pointer, for the end.
        self.held: dict[str, Any] = {}
        self.said: set[str] = set()
        # By tree, the outcomes already counted: at most the seven trees times a handful of outcomes.
        self.counted: set[tuple[str, str]] = set()
        self.left: set[str] = set()

    def _say_once(self, what: str, **fields: Any) -> None:
        if what not in self.said:
            self.said.add(what)
            self.note("normal_melee_rest_left", what=what, **fields)

    def _open(self) -> bool:
        """The memory, the field's offset and the nodes' names, once; whether they are there."""
        if self.at is not None:
            return True
        try:
            prop = unrealsdk.find_object("ScriptStruct", TIMER)._find_prop(FIELD)
            if int(prop.ElementSize) != gbx_param.SIZE:
                self._say_once("layout", size=int(prop.ElementSize))
                return False
            self.memory = process_memory.ProcessMemory()
            wanted = {name for tree in TREES.values() for name in tree.nodes}
            self.names = brain_trees.tokens(self.memory, list(wanted))
            missing = sorted(wanted - set(self.names))
            if missing:
                # Their trees are then refused by node: said here once with the names.
                self._say_once("tokens", missing=missing)
            self.at = int(prop.Offset_Internal)
        except Exception as error:
            self._say_once("open", error=type(error).__name__)
            return False
        return True

    def _address(self, tree: Any, asset: Any) -> int | str:
        found = brain_trees.nodes(self.memory, asset, list(tree.nodes), self.names)
        return found if isinstance(found, str) else found[tree.timer] + self.at

    def _read(self, address: int) -> Any:
        raw = self.memory.read(address, gbx_param.SIZE)
        if raw is None:
            return None
        kind, value = gbx_param.decode(raw)
        return value if kind == RANGE else None

    def _put(self, address: int, wanted: tuple[float, float]) -> bool:
        if not self.memory.write(address + VALUE_AT, struct.pack("<ff", *wanted)):
            return False
        return self._read(address) == list(wanted)

    def keep(self) -> dict[str, int]:
        """One pass over the trees the game holds: how each went, empty when nothing is to say."""
        if self.rest is None or not self._open():
            return {}
        tally: dict[str, int] = {}
        for name, tree in TREES.items():
            outcome = self._keep(name, tree)
            if outcome in QUIET or outcome != "written" and (name, outcome) in self.counted:
                continue
            self.counted.add((name, outcome))
            tally[outcome] = tally.get(outcome, 0) + 1
        return tally

    def _keep(self, name: str, tree: Any) -> str:
        if name in self.left:
            return "left"
        try:
            try:
                asset = unrealsdk.find_object(TREE_CLASS, tree.path)
            except ValueError:
                # The SDK's answer for an object the game does not hold: no bandit of that kind is loaded.
                return "not_loaded"
            if asset is None:
                return "not_loaded"
            address = self._address(tree, asset)
            if isinstance(address, str):
                self._say_once(f"nodes:{name}", reason=address)
                return "refused"
            value = self._read(address)
            if value == list(self.rest):
                self.held[name] = unrealsdk.unreal.WeakPointer(asset)
                return "kept"
            if value != list(tree.rest):
                self._say_once(f"value:{name}", read=value)
                return "unexpected"
            if tree.rest[0] <= self.rest[0]:
                return "shorter"
            self.held[name] = unrealsdk.unreal.WeakPointer(asset)
            self.announce("MeleeRest", tree=name, game=list(tree.rest), wanted=list(self.rest))
            if self._put(address, self.rest):
                return "written"
            self.left.add(name)
            return "write_failed"
        except Exception as error:
            self._say_once(f"error:{name}", error=type(error).__name__)
            return "failed"

    def put_back(self) -> dict[str, int] | str:
        """Every tree still held given the game's rest where the level's lies: how each went, "none" when none was
        written."""
        if not self.held:
            return "none"
        held, self.held = self.held, {}
        tally: dict[str, int] = {}
        for name, pointer in held.items():
            tree = TREES[name]
            try:
                asset = pointer()
                address = "gone" if asset is None else self._address(tree, asset)
                if isinstance(address, str):
                    outcome = "gone" if address == "gone" else "refused"
                elif self._read(address) != list(self.rest):
                    outcome = "different"
                else:
                    outcome = "given_back" if self._put(address, tree.rest) else "write_failed"
            except Exception as error:
                outcome = f"failed:{type(error).__name__}"
            tally[outcome] = tally.get(outcome, 0) + 1
        return tally
