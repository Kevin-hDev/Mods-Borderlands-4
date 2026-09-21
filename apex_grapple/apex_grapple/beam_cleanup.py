"""Release the owned beam; only a failed deactivation and removal block its successor."""

from typing import Any

from unrealsdk import unreal

from . import report

DESTROY_NAMES = ("K2_DestroyComponent", "DestroyComponent")
_pending: Any = None


def release(component: Any) -> bool:
    global _pending
    if _pending is not None and _pending() is not None and _pending() != component:
        report.error_once("beam:ownership", "a previous grapple beam still needs cleanup")
        return False
    _pending = unreal.WeakPointer(component)
    return retry()


def retry() -> bool:
    global _pending
    component = _pending() if _pending is not None else None
    if component is None:
        _pending = None
        return True
    deactivated = False
    try:
        component.Deactivate()
    except Exception:
        report.error_once("beam:deactivate", "the grapple beam could not be deactivated; trying its removal")
    else:
        deactivated = True
    for name in DESTROY_NAMES:
        try:
            remove = getattr(component, name, None)
            if remove is None:
                continue
            if name == "K2_DestroyComponent":
                # Epic's reflected signature takes Object; only the owning actor may remove it.
                owner = component.GetOwner()
                remove(owner if owner is not None else component)
            else:
                remove()
            destroying = getattr(component, "IsBeingDestroyed", None)
            if _pending() is None or (destroying is not None and destroying()):
                _pending = None
                return True
        except Exception:
            continue
    if deactivated:
        # Niagara can finish asynchronously: awaiting destruction here suppressed later ropes.
        # Preserve the accepted release even when removal is unavailable, as before 0.11.7.
        _pending = None
        return True
    report.error_once("beam:cleanup", "the grapple beam is awaiting cleanup; another beam will not be created")
    return False
