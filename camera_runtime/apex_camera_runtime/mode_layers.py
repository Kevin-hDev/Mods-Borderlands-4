"""Own the exact ThirdPerson layers held by the camera controller."""

from typing import Any

from .constants import (CAMERA_BLEND, CAMERA_TELEPORT, CAMERA_TRANSITION,
                        THIRD_PERSON_MODE)


def push_one(controller: Any, actor: Any, manager: Any) -> None:
    push(controller, actor, manager)
    controller._mode_pushes = 1


def push(controller: Any, actor: Any, manager: Any) -> None:
    manager.PushActorCameraMode(
        actor, THIRD_PERSON_MODE, CAMERA_TRANSITION, CAMERA_BLEND, CAMERA_TELEPORT)
    controller._mode_pushes += 1


def remove_all(controller: Any, actor: Any, manager: Any) -> None:
    while controller._mode_pushes:
        manager.PopActorCameraMode(
            actor, THIRD_PERSON_MODE, CAMERA_TRANSITION, CAMERA_BLEND, CAMERA_TELEPORT)
        controller._mode_pushes -= 1
