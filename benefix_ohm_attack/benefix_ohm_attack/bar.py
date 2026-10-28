"""The energy bar's side of the mod: tells the game's screen how much energy the beam has left.

The bar itself is a script in the game's screen (docs/attaque-rayon/barre/); this module only owns the local
service that script asks. The bar is an extra: whatever fails here leaves it hidden and the beam untouched.
"""

from typing import Any

from . import report

# None: the port the bar's script knows (assets/bar.constants.json). The tests ask for a free one instead.
PORT: int | None = None

_service: Any = None


def start() -> None:
    """Called when the mod is switched on."""
    global _service
    stop()
    try:
        # Imported here: a service that cannot even load (its constants, the game's Python) must not take the
        # whole mod down with it.
        from . import energy_service
        service = energy_service.EnergyService(report.note)
        if service.start(PORT):
            _service = service
            report.note(f"energy bar: the service answers on port {service.port()}")
    except Exception as error:
        report.error_once("bar:start", f"the energy bar stays hidden: {error!r}")


def tell(energy: float, maximum: float, element: str) -> None:
    """Called at each frame; does nothing while the service is not running."""
    if _service is None:
        return
    try:
        _service.publish(energy, maximum, element)
    except Exception as error:
        report.error_once("bar:tell", f"the energy bar no longer follows: {error!r}")


def hide() -> None:
    """Called at each frame while the player wants no bar (settings.show_bar): the screen is told nothing."""
    if _service is None:
        return
    try:
        _service.clear()
    except Exception as error:
        report.error_once("bar:hide", f"the energy bar could not be hidden: {error!r}")


def stop() -> None:
    """Called when the mod is switched off."""
    global _service
    service, _service = _service, None
    if service is None:
        return
    try:
        service.stop()
    except Exception as error:
        report.error_once("bar:stop", f"the energy service could not be stopped: {error!r}")
