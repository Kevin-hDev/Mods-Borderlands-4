"""The normal mode's four levels (decisions 80 and 85, Kevin, 15 October 2026), set in advance and never tuned in
game: every value of a level is here and nowhere else.

God (decisions 153 and 155, Kevin, 20 and 21 October 2026), made to play with the companions without the game growing
too easy: Predator, but for Senior's run, dodges' speed and gestures (« plus fort que en predator mais moins rapide »;
Kevin, 22 October 2026: all three of Senior's), the enemies' health +250 %, the damage the player takes +35 % (the
companions take the game's own, decision 40 of the reinforcements), ammo +50 %, money +40 % and experience +25 %.

camps: how many times their enemies the game's camps hold (camps_grown.py). chase_m: the combat radius each enemy's
own zone is widened to (Kevin: « 250m c'est pas long, poursuite on peu pousser a 350m pour bandit/senior »); Predator
is the same mode with a longer chase, never the Horde's hunt (Kevin, after trying it: « on veut la meme chose que les
deux autres mais que les ennemies suivent plus longtemps c'est tout »), at the Horde's 600 m, the radius with which a
Psycho followed much farther from its home (decision 33, verified in game). speed: the enemies' own speed bonus times
this.
dodge_speed: their own time during a dodge times this (×2, ×3 and ×4 seen and kept at trial 21). dodge_chance: the
chance of each dodge, every condition open (dodge_rate.py), and dodge_moving: IsMovingSpeed times this, the two Kevin
kept after trials 26 and 27 (« bandit c'est bon comme ca, seniors je dirais peux reduire a 90% [...] predator reduire
a peut etre 80% »; « oui c'est bon comme ca on valide »). health and taken: the enemies' health, shield and armour, and
the damage the player takes, times these: the normal mode's own BUFF, BUFF+ and BUFF++, not the Horde's; Predator's
health doubled after trial 30 (Kevin: « la vie en predator on va passer de 80 a 100% ce sera mieux »).

Rebalanced after trial 34 (Kevin, 15 October 2026: « On va re modifier quelques stats »): health +45, +75 and +130 %,
dodges ×1.7, ×2.3 and ×2.8 faster, dodge chance 35, 45 and 55 %, Predator's damage taken +30 %. Predator dodged less
than Senior (trial 27: some 23 dodges a minute against 42), a mistake of figures (Kevin: « j'ai du me tromper de
chiffre »); its chance is now the highest, IsMovingSpeed ×100 kept.

Faster after trial 35 (decision 100, Kevin, 15 October 2026: « c'est pas assez je le sent pas du tout en jeu »): speed
×1.2, ×1.5 and ×1.7 in place of ×1.1, ×1.2 and ×1.4. Senior and Predator brought back to ×1.4 and ×1.5 (decision 121,
Kevin, 16 October 2026): faster in everything, the game would be « infernal et injouable ».

reducible: whether the window's « Enemy speed » row shows at that level, Senior, Predator and God (decision 121); its
REDUCED choice runs the level's speed, faster dodges and gestures times REDUCED (Kevin: « reduis la vitesse de 15%
uniquement pour les deux niveau senior et predator [...] Pour ceux qui pourrait trouver que c'est trop rapide »),
never below Bandit's own (decision 125, Kevin, 17 October 2026: « comme ca senior descend comme bandit et predator
reste quand meme un peu au dessus »): ×0.85 took Senior's run to ×1.19 and its gestures to ×1.02, under Bandit's ×1.2
and ×1.1.

shields: the shield given to the enemies without one (decisions 111 and 112, Kevin, 16 October 2026: « Bandit : Shield
optionnel qui ne se recharge pas. Senior : Shield obligatoire qui ne se recharge pas. Predator : Shield oblgatoire qui
se recharge au bout de 10 secondes uniquement quand il est casser et de 13% par secondes comme mon shield actuel de mon
chasseur »): OPTION, given while the player keeps the option on, or ALWAYS; shield_refill: whether it comes back.

spread and bullet_speed: the enemies' aim (aim.py; decisions 114 and 115, Kevin, 16 October 2026: « ajouter en plus
des balles recu un 12% plus serrer pour Bandit/Senior et un 20% plus serré pour predator »): their weapons' spread
times spread, and their bullets' speed times bullet_speed, aimed at 15, 20 and 30 % more hits on a hunter on the move.
Trial 51 found ×2 dealt some 5 times the damage; if the damage follows a power of the speed (some 2.3), those hits ask
×1.06, ×1.08 and ×1.12, an estimate (non vérifié): two phases of the game's own differ by 60 %, so a rise of 15 % is
not measured in one pass. Kevin judges them in play.

xp, ammo and cash: the share added to the game's multipliers of the experience of the enemies killed, of the ammo
picked up and of the money picked up (decision 119, Kevin, 16 October 2026; rewards.py), never missions, sales or
vending machines.

gestures: the enemies' own time while they play a blow, a leap or a thrown weapon, never a grenade nor a turret set
down (decisions 121 and 124, Kevin, 16 October 2026: « les autres mouvement n'ont pas besoin d'aller a la meme vitesse
que la marche et le sprint »; enemy_time.py).

melee_rest: the armed bandits' rest after a blow, centre and half width in seconds, None for the game's (decision 126,
Kevin, 17 October 2026: « Senior 3 a 5 et preda 2 a 3 s c'est bon »; melee_rest.py). The game's is 6 / 2, 8 / 2 for
the pistol (trial 66).

staggers: the game's chances of a stagger and a launch times this (decision 135, Kevin, 18 October 2026: 15, 25 and
50 % fewer; staggers.py). staggers_off: whether the window's « No staggers » row shows at that level, Predator and God
(Kevin: « un bouton qui apparait uniquement pour ce niveau et qui desactive completement les sursauts »); on, the
level's staggers are zero.
"""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Level:
    name: str
    camps: float
    chase_m: float
    speed: float
    dodge_speed: float
    dodge_chance: float
    dodge_moving: float
    health: float
    taken: float
    shields: str
    shield_refill: bool
    spread: float
    bullet_speed: float
    reducible: bool
    xp: float
    ammo: float
    cash: float
    gestures: float
    melee_rest: tuple[float, float] | None
    staggers: float
    staggers_off: bool


OPTION, ALWAYS = "option", "always"
LEVELS = {
    "Bandit": Level("Bandit", 1.5, 350.0, 1.2, 1.7, 0.35, 1.0, 1.45, 1.1, OPTION, False, 0.88, 1.06, False,
                    0.10, 0.10, 0.15, 1.1, None, 0.85, False),
    "Senior": Level("Senior", 2.0, 350.0, 1.4, 2.3, 0.45, 1.0, 1.75, 1.2, ALWAYS, False, 0.88, 1.08, True,
                    0.15, 0.20, 0.15, 1.2, (4.0, 1.0), 0.75, False),
    "Predator": Level("Predator", 2.0, 600.0, 1.5, 2.8, 0.55, 100.0, 2.3, 1.3, ALWAYS, True, 0.8, 1.12, True,
                      0.20, 0.25, 0.15, 1.3, (2.5, 0.5), 0.5, True),
    "God": Level("God", 2.0, 600.0, 1.4, 2.3, 0.55, 100.0, 3.5, 1.35, ALWAYS, True, 0.8, 1.12, True,
                 0.25, 0.50, 0.40, 1.2, (2.5, 0.5), 0.5, True),
}
# The faster dodges switched off keep the game's own speed, never reduced (play.py speeds up no dodge then; Kevin: « on
# ne re reduis pas de 15% »).
REDUCED = 0.85
FLOOR = "Bandit"
# Every level's shield: SHIELD_SHARE of the health the enemy had (Kevin: « Shield = 40% de la vie », the share of the
# game's GunToterBadass, trial 46). Predator's and God's, broken, come back SHIELD_REFILL_AFTER_S later at
# SHIELD_REFILL_RATE of themselves a second, the hunter's own (trial 46: 13 % a second).
SHIELD_SHARE = 0.4
SHIELD_REFILL_AFTER_S = 10.0
SHIELD_REFILL_RATE = 0.13
# The mildest at first: the mode is there to play the game, and the player raises it at will (Claude's choice).
DEFAULT = "Bandit"
# Every level (decision 85): the rest after a dodge and the warmup before the first of a fight divided by this, as in
# trials 25 to 27.
DODGE_REST_DIVIDE = 20.0


def level(name: object) -> Level:
    """The level of that name, the default one for a value the settings file holds that is no level."""
    return LEVELS.get(str(name), LEVELS[DEFAULT])


def reduced(chosen: Level) -> Level:
    """The level with the « Enemy speed » row on REDUCED: its speed, faster dodges and gestures times REDUCED, none
    below FLOOR's; a level without the row as it is."""
    if not chosen.reducible:
        return chosen
    floor = LEVELS[FLOOR]
    return replace(chosen, speed=max(chosen.speed * REDUCED, floor.speed),
                   dodge_speed=max(chosen.dodge_speed * REDUCED, floor.dodge_speed),
                   gestures=max(chosen.gestures * REDUCED, floor.gestures))
