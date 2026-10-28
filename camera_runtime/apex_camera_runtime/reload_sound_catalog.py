"""The reload sounds the game left out, made for Loveless with pistols (2026-10-25).

In the game's files Loveless's four third-person pistol reloads carry no sound, where the other hunters' carry the
magazine out and in, and a throw for the Tediore pistols (read in the files,
docs/investigations/third_person_fov/son/2026-10-24-son-rechargement.md). In third person the game plays only these
body sounds: Loveless reloaded a pistol in silence (Kevin, 2026-10-25).

Each row is one sound made for a pistol reload, at the instant Vex's same pistol reload plays it (Vex's four have the
same lengths as hers), set as the game sets its own: a magazine sound by its tag and its Wwise event, from the right
hand, as her rifle's are; the Tediore throw by its tag alone, attached to the right hand, as her rifle's throws are.
Named by its tag alone, a magazine sound stayed silent (trial 13); with its Wwise event it was heard, at the right
moment (trial 14). Nothing is borrowed from her rifle reloads: the game loads them only once a rifle is held
(trial 11). The throws are not heard yet: Kevin has no Tediore pistol.
"""

from typing import NamedTuple

FOLDER = "/Game/DLC/Harmonica/PlayerCharacters/CorpoHacker/Animation/3rd/Pistol/_Shared"
SOUND_CLASS = "AnimNotify_GbxAudioEvent"
HAND = "RightHand"
THROW = "Audio.Player.Shared.GrenadeThrow"
# The game's type marker for an animation event is read on the first event the game built in this reload, its
# footstep: in memory with the three others whenever she holds a pistol (trials 10, 13, 14).
MODEL = "AS_PS_Reload_Throw"


class Made(NamedTuple):
    pistol: str
    tag: str
    # None for the throw: its tag alone, as the game's own throws.
    wwise: str | None
    at: float


# Each pistol reload's length in the files: one of another length is another animation, whose instants are unknown.
LENGTHS = {
    "AS_PS_Reload": 2.8333333,
    "AS_PS_Reload_Throw": 1.5666667,
    "AS_PS_Reload_Throw_Borg": 2.4666667,
    "AS_PS_Reload_Throw_Forge": 2.9666667,
}

SOUNDS = (
    Made("AS_PS_Reload", "Audio.Weapon.Foley.Reload.MagOut",
         "Wep_Shared_Simple_Reloads.Wep_Shared_Simple_Reloads_Out", 0.53371465),
    Made("AS_PS_Reload", "Audio.Weapon.Foley.Reload.MagIn",
         "Wep_Shared_Simple_Reloads.Wep_Shared_Simple_Reloads_In", 1.5006474),
    Made("AS_PS_Reload_Throw", THROW, None, 0.5303685),
    Made("AS_PS_Reload_Throw_Borg", THROW, None, 1.235782),
    Made("AS_PS_Reload_Throw_Forge", THROW, None, 1.9045866),
)


def path(name: str) -> str:
    return f"{FOLDER}/{name}.{name}"


def pistols() -> dict[str, tuple[Made, ...]]:
    grouped: dict[str, list[Made]] = {}
    for row in SOUNDS:
        grouped.setdefault(row.pistol, []).append(row)
    return {name: tuple(rows) for name, rows in grouped.items()}
