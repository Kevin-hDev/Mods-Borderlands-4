"""Read the game's native attachment and scripted climbing presentation, without writes."""
from .constants import SCRIPTED_CLIMB_MAX, SCRIPTED_CLIMB_NONE


def read(actor):
    movement = getattr(actor, "CharacterMovement", None)
    ladder = getattr(movement, "LadderState", None)
    animation = getattr(movement, "LadderAnimState", None)
    if ladder is None or animation is None:
        return None
    kind = animation.CurrentType
    value = getattr(kind, "value", kind)
    if (isinstance(value, bool) or not isinstance(value, int)
            or not SCRIPTED_CLIMB_NONE <= value <= SCRIPTED_CLIMB_MAX):
        raise ValueError("invalid native climbing state")
    # The attachment clears before GettingOffAtTop finishes: both must be idle to return.
    return ladder.CurrentClimbable is not None, value != SCRIPTED_CLIMB_NONE
