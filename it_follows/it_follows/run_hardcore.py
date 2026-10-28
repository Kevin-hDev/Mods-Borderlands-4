"""The Horde's Hardcore (decision 109, Kevin, 16 October 2026: « Le mode hardcore, j'aimerais l'ajouter au mode Horde
mais toujours activer donc pas d'option d'activation [...] 1% d'augmentation du niveau des ennemies tous les 100
kills »): always on, counted from 0 at each START on the run's kills (« Par run »), its percent shown in the bar.

The rule is the normal mode's (hardcore_steps.py), on top of the BUFF. At each step reached, the enemies that join from
then on are raised by the new factor, and the hunter's damage taken at once. The enemies already in the horde keep the
factor they joined with: writing the new one on each of them at every step would hold one image some 20 to 40 ms every
100 kills (non vérifié), 8 times in trial 41's twelve minutes, and the horde is renewed within minutes (816 kills for a
horde of 120).
"""

from typing import Any, Callable

from . import hardcore_steps as steps


class RunHardcore:
    """toughness (toughness.Toughness) and taken (damage_taken.DamageTaken), the run's, raised by the BUFF's factors
    health and taken_factor; note(event, **fields) writes a line."""

    def __init__(self, toughness: Any, taken: Any, health: float, taken_factor: float,
                 note: Callable[..., None]) -> None:
        self.toughness, self.taken, self.note = toughness, taken, note
        self.health, self.taken_factor = health, taken_factor
        self.percent = 0

    def keep(self, kills: int, player: Any) -> None:
        """The run's kills read this second: at a new step, the new factor given and written down."""
        reached = steps.percent(kills)
        if reached == self.percent:
            return
        self.percent = reached
        hard = steps.factor(reached)
        self.toughness.harden(self.health * hard)
        taken = self.taken.change(player, self.taken_factor * hard)
        self.note("hardcore_step", percent=reached, kills=kills, health=round(self.health * hard, 3), taken=taken)
