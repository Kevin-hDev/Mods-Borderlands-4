"""Camera commands: identifiers, defaults, validation and bind alignment."""

from typing import Any, Callable, NamedTuple

from mods_base import EInputEvent, keybind

from .key_option import (ControllerKeybindOption, KeyboardKeybindOption,
                         normalize_controller_key, normalize_keyboard_key)

KEYBOARD, CONTROLLER = "keyboard", "controller"
# The SDK's text menu lists both entries of an action: under one name, a player could not tell the keyboard's from the
# controller's (review, 2026-09-26).
DEVICE_NAMES = {KEYBOARD: "Keyboard", CONTROLLER: "Controller"}


class Action(NamedTuple):
    name: str
    keyboard_id: str
    controller_id: str
    keyboard_default: str | None
    display_name: str
    description: str


ACTIONS = (
    Action("third_person", "third_person_key", "third_person_controller", "P",
           "Toggle Third Person", "Turn the third-person camera on or off."),
    Action("shoulder", "shoulder_key", "shoulder_controller", "Six",
           "Switch Camera Shoulder", "Move the third-person camera to the other shoulder."),
    Action("orbit", "orbit_key", "orbit_controller", "Seven",
           "Toggle Orbit Camera", "Switch between shoulder and Orbit Camera views."),
    Action("zoom_in", "zoom_in_key", "zoom_in_controller", None,
           "Orbit Camera Zoom In", "Move the Orbit Camera closer, one step per press."),
    Action("zoom_out", "zoom_out_key", "zoom_out_controller", None,
           "Orbit Camera Zoom Out", "Move the Orbit Camera farther away, one step per press."),
)


class _CameraOption:
    normalizer: Callable[[Any], str | None]

    def attach(self, commands: "CameraCommands") -> None:
        object.__setattr__(self, "_camera_commands", commands)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "value":
            try:
                value = self.normalizer(value)
            except ValueError:
                value = None
            commands = getattr(self, "_camera_commands", None)
            if commands is not None and not commands.applying:
                try:
                    commands.validate({self.identifier: value})
                except ValueError:
                    return
        super().__setattr__(name, value)


class CameraKeyboardOption(_CameraOption, KeyboardKeybindOption):
    normalizer = staticmethod(normalize_keyboard_key)


class CameraControllerOption(_CameraOption, ControllerKeybindOption):
    normalizer = staticmethod(normalize_controller_key)


class CameraCommands:
    """One owner-specific set built from the shared, immutable camera command table."""

    def __init__(self, **callbacks: Callable[[], None]) -> None:
        if set(callbacks) != {action.name for action in ACTIONS}:
            raise ValueError("invalid camera callbacks")
        self.applying = True
        self.binds, self.options = self._build(callbacks)
        self._options = {option.identifier: option for option in self.options}
        for option in self.options:
            option.attach(self)
        self.applying = False
        self.align()

    @staticmethod
    def _build(callbacks: dict[str, Callable[[], None]]) -> tuple[tuple, tuple]:
        binds, options = [], []
        for action in ACTIONS:
            for device, identifier, default, option_type in (
                    (KEYBOARD, action.keyboard_id, action.keyboard_default, CameraKeyboardOption),
                    (CONTROLLER, action.controller_id, None, CameraControllerOption)):
                # A toggle changes once per physical press; repeats and releases would immediately undo it.
                bind = keybind(identifier, default,
                               lambda callback=callbacks[action.name]: callback(),
                               display_name=f"{DEVICE_NAMES[device]}: {action.display_name}",
                               description=action.description,
                               is_hidden=True, event_filter=EInputEvent.IE_Pressed)
                binds.append(bind)
                options.append(option_type.sole_entry(bind))
        return tuple(binds), tuple(options)

    def option(self, identifier: str) -> Any:
        return self._options[identifier]

    @staticmethod
    def slots() -> tuple[tuple[str, str, str], ...]:
        return tuple(slot for action in ACTIONS for slot in (
            (action.name, KEYBOARD, action.keyboard_id),
            (action.name, CONTROLLER, action.controller_id),
        ))

    def identifier(self, action: str, device: str) -> str:
        try:
            return next(identifier for name, kind, identifier in self.slots()
                        if name == action and kind == device)
        except StopIteration as error:
            raise ValueError("invalid camera command") from error

    def defaults(self) -> dict[str, str | None]:
        return {action.keyboard_id: action.keyboard_default for action in ACTIONS} | {
            action.controller_id: None for action in ACTIONS
        }

    @staticmethod
    def _normalizer(identifier: str) -> Callable[[Any], str | None]:
        return normalize_controller_key if identifier.endswith("_controller") else normalize_keyboard_key

    def validate(self, changes: Any) -> dict[str, str | None]:
        if type(changes) is not dict or not 0 < len(changes) <= len(self.options):
            raise ValueError("invalid camera command changes")
        if any(type(identifier) is not str or identifier not in self._options for identifier in changes):
            raise ValueError("unknown camera command")
        normalized = {identifier: self._normalizer(identifier)(value)
                      for identifier, value in changes.items()}
        final = {identifier: option.value for identifier, option in self._options.items()}
        final.update(normalized)
        for identifiers in (
                tuple(action.keyboard_id for action in ACTIONS),
                tuple(action.controller_id for action in ACTIONS)):
            values = [final[identifier] for identifier in identifiers if final[identifier] is not None]
            if len(values) != len(set(values)):
                raise ValueError("duplicate camera command")
        return normalized

    def set_values(self, changes: Any) -> dict[str, str | None]:
        normalized = self.validate(changes)
        self.applying = True
        try:
            for identifier, value in normalized.items():
                self._options[identifier].value = value
        finally:
            self.applying = False
        return normalized

    def apply(self, changes: Any) -> dict[str, str | None]:
        normalized = self.set_values(changes)
        self.align()
        return normalized

    def align(self) -> None:
        for bind, option in zip(self.binds, self.options):
            bind.key = option.value
