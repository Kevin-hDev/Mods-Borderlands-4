"""Show the reticle as soon as our shoulder aim is published.

The game decides the reticle only when the zoom level changes (OnZoomInChange), and at the start of the aim it does so
about 11 ms before our publication: the weapon then says "no reticle", our .dll cannot answer yet, and the reticle
stayed hidden until the zoom ended, about 0.22 s later (Kevin, 2026-10-11, the same on three aims;
docs/third_person_fov/camera/enquetes/2026-10-11-reticule-pendant-le-zoom.md). Asking the game once more right after
publishing lets our .dll answer, one frame later. Nothing of the game's is blocked.
"""

from .ads_feedback import exception_kind

# The weapon's UI collector in the snapshot's references (ads_context.py; the .dll's references[5]).
COLLECTOR = 5
# The level the game passed at both of its calls, start and end of the zoom, on every aim measured.
LEVEL = 0


def refresh(snapshot, feedback) -> None:
    """The reticle is comfort: a refused call keeps the aim and is noted once."""
    try:
        collector = snapshot.weak_references[COLLECTOR]()
        if collector is not None:
            collector.OnZoomInChange(LEVEL)
    except Exception as error:
        feedback.diagnostic("reticle_refresh", exception_kind(error))
