"""Lighting the rope: the switch, and everything that can stop a beam from ever being drawn.

Split out of `beam.py` on 2026-09-21. Putting the rope in the world and getting the engine to draw
it turned out to be two different problems, and the second one is where five corrections went.

It held four "shields" for one version — `SetAllowScalability(False)` and three others — on the
guess that the engine was ruling the rope out of every frame. **They were removed on 2026-09-21**,
because they changed settings away from the native example, which permits scalability.
The active/visible flags at +0.2, +0.4, +0.8 and +1.2 s did NOT rule out culling or empty emitters.
Trial A leaves activation unchanged so its only visual hypothesis is the coordinate convention.
"""

from typing import Any

from . import report


def switch_on(component: Any) -> bool:
    """Lights the beam. False when the game offers no way to light one at all."""
    refused: list[str] = []
    for light_it in (lambda: component.Activate(True), lambda: component.Activate()):
        try:
            light_it()
        except Exception as exc:
            refused.append(repr(exc))
            continue
        return True
    report.error_once("beam:activate", f"the grapple beam could not be lit: {'; '.join(refused)}")
    return False
