"""Capture one owned ADS context without retaining game objects strongly."""

from dataclasses import dataclass
from itertools import islice

from .ads_category import address, category
from .ads_feedback import exception_kind
from .ads_paths_reader import make_config
from .generated_ads import MAX_COLLECTORS, ObjectId, PathsConfig


@dataclass(frozen=True)
class Snapshot:
    category: int
    references: tuple[ObjectId, ...]
    weak_references: tuple
    paths: PathsConfig


class ContextReader:
    def __init__(self, weak_ref, identify, find_all):
        self.weak_ref, self.identify, self.find_all = weak_ref, identify, find_all
        self._collector_ref = None
        self._owner = None
        self.reason = "context_unavailable"
        self.error_kind = None

    def clear(self) -> None:
        self._collector_ref = self._owner = None
        self.reason = "context_unavailable"

    def capture(self, item):
        """Capture one weak identity; ADS and body framing share this authority."""
        ref = self.weak_ref(item)
        identity = self.identify(item)
        if (not isinstance(identity, ObjectId) or identity.address != address(item)
                or identity.index < 0 or identity.serial <= 0
                or ref() is None or address(ref()) != identity.address):
            raise ValueError("ADS identity unavailable")
        return ref, identity

    def _collector(self, actor, owner):
        item = self._collector_ref() if self._collector_ref is not None else None
        if self._owner == owner and item is not None and address(item.Outer) == address(actor):
            return item
        self._collector_ref = self._owner = None
        candidates = list(islice(self.find_all("OakUIDataCollector_Weapon"), MAX_COLLECTORS + 1))
        if len(candidates) > MAX_COLLECTORS:
            return None
        local = [candidate for candidate in candidates if address(candidate.Outer) == address(actor)]
        if len(local) != 1:
            return None
        ref, _ = self.capture(local[0])
        self._collector_ref, self._owner = ref, owner
        return local[0]

    def read(self, pc, actor, manager):
        self.reason = "context_unavailable"
        self.error_kind = None
        try:
            if address(pc.OakCharacter) != address(actor) or address(pc.PlayerCameraManager) != address(manager):
                return None
            animation = actor.Mesh.GetAnimInstance()
            if animation is None:
                self.reason = "animation_pending"
                return None
            slots = actor.ActiveWeapons.Slots
            weapon = slots[0].Weapon if len(slots) else None
            observation = category(actor, weapon)
            if not observation["matched"]:
                self.reason = "unknown_weapon"
                return None
            first = tuple(self.capture(item) for item in (pc, actor, manager))
            owner = tuple((identity.address, identity.index, identity.serial) for _, identity in first)
            collector = self._collector(actor, owner)
            if collector is None:
                self.reason = "collector_unavailable"
                return None
            remaining = tuple(self.capture(item) for item in
                              (weapon, animation, collector, manager.CameraModeState, manager.CameraModeInputs))
            captured = first + remaining
            paths = make_config(pc, manager, weapon)
            if (address(manager.CameraModeState.Inputs) != paths.inputs
                    or address(manager.CameraModeInputs.Controller) != paths.controller
                    or any(ref() is None or address(ref()) != identity.address for ref, identity in captured)):
                return None
            self.reason = ""
            return Snapshot(observation["value"], tuple(identity for _, identity in captured),
                            tuple(ref for ref, _ in captured), paths)
        except Exception as error:
            # SDK reflection and weak references can fail during level reconstruction.
            self.reason = "context_unavailable"
            self.error_kind = exception_kind(error)
            return None

    def current(self, snapshot):
        """A publication must not reuse owners which expired since capture."""
        try:
            for ref, expected in zip(snapshot.weak_references, snapshot.references):
                item = ref()
                if item is None:
                    return False
                _ref, actual = self.capture(item)
                if (actual.address, actual.index, actual.serial) != (expected.address, expected.index, expected.serial):
                    return False
            return True
        except Exception as error:
            self.error_kind = exception_kind(error)
            return False
