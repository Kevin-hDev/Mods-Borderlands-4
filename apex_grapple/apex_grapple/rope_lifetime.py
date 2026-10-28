"""Trial 0.11.2: measure the native effect's exposed lifetime independently of the arms.

User.Lifetime=1 was captured in NS_Grapple_Beam on 2026-09-21. Its effect on the cooked emitters
is not established. Ten seconds separates the trial from normal pulls without changing the asset.
Rope.let_go remains the authority for destroying the component, including early cancellation.
"""

from typing import Any

from . import report, rope_ends

PARAMETER = "User.Lifetime"
TRIAL_SECONDS = 10.0


def configure(component: Any, system: Any) -> None:
    """Set only the observed parameter on our component, before activation; propagate failures."""
    names = rope_ends.parameter_names(str(system.ExposedParameters)[:rope_ends.MAX_STORE])
    if PARAMETER not in names:
        raise ValueError("the grapple lifetime parameter is unavailable")
    # SetVariableFloat(FName, float) is exposed on BL4's component; Epic documents a local override.
    component.SetVariableFloat(PARAMETER, TRIAL_SECONDS)
    report.note(f"beam lifetime trial: requested {PARAMETER}={TRIAL_SECONDS:.1f}s before activation")
