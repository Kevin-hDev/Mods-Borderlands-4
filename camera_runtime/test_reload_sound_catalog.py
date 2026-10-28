"""The reload sounds made for Loveless's pistols: four pistol reloads, each with its length, each sound within it; the
magazine sounds by their tag and the Wwise event every hunter's pistol reload names, the throws by their tag alone;
the model reload, where the type marker is read, one of hers; the game's paths.
python test_reload_sound_catalog.py"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import reload_sound_catalog as catalog  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


grouped = catalog.pistols()
check("the four pistol reloads: the reload and the three Tediore throws",
      list(grouped) == ["AS_PS_Reload", "AS_PS_Reload_Throw", "AS_PS_Reload_Throw_Borg", "AS_PS_Reload_Throw_Forge"])
check("each pistol reload has its length in the files", set(grouped) == set(catalog.LENGTHS))
check("each sound falls within its reload",
      all(0.0 < row.at < catalog.LENGTHS[row.pistol] for row in catalog.SOUNDS))
check("the reload: magazine out at 0.534 s, then in at 1.501 s, each by its tag and its Wwise event",
      [(row.tag, row.wwise, round(row.at, 3)) for row in grouped["AS_PS_Reload"]]
      == [("Audio.Weapon.Foley.Reload.MagOut", "Wep_Shared_Simple_Reloads.Wep_Shared_Simple_Reloads_Out", 0.534),
          ("Audio.Weapon.Foley.Reload.MagIn", "Wep_Shared_Simple_Reloads.Wep_Shared_Simple_Reloads_In", 1.501)])
check("each throw: the throw sound by its tag alone, once",
      all([(row.tag, row.wwise) for row in grouped[name]] == [("Audio.Player.Shared.GrenadeThrow", None)]
          for name in ("AS_PS_Reload_Throw", "AS_PS_Reload_Throw_Borg", "AS_PS_Reload_Throw_Forge")))
check("the model reload, where the game's marker is read, is one of hers", catalog.MODEL in catalog.LENGTHS)
check("the game's path of Loveless's pistol reloads",
      catalog.path("AS_PS_Reload")
      == "/Game/DLC/Harmonica/PlayerCharacters/CorpoHacker/Animation/3rd/Pistol/_Shared/AS_PS_Reload.AS_PS_Reload")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
