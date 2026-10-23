# Companions

Une équipe de 8 compagnons au plus, parmi les 6 chasseurs de l'Arche et 4 alliés du jeu, qui te suivent et se battent
à tes côtés. Ce sont les compagnons d'[It Follows](../it_follows/), dans un mod à part : pas besoin d'It Follows pour
les avoir.

Testé sur la version du jeu du 22 octobre 2026 (build **4906557**) sous Windows, en solo sur Steam.

## Ce qu'il fait

Ouvre la console avec `~`, tape `mods` et choisis **Companions**, ou appuie sur la touche du menu choisie dans OPTIONS
(aucune au départ). Sa fenêtre, en français, en anglais, en chinois simplifié et en japonais, a trois pages. Le jeu se met en pause
tant qu'elle est ouverte, sauf en coopération.

- **CHASSEURS DE L'ARCHE et ALLIÉS.** Choisis jusqu'à 8 compagnons parmi 10, le même plusieurs fois si tu veux, puis
  LANCER L'ÉQUIPE, ou appuie sur la touche de l'équipe, F8 au départ : ils te suivent et se battent avec toi. Les
  chasseurs de l'Arche se battent avec leurs armes seulement, sans leurs compétences. Sur la carte du chasseur que tu
  joues, sa tenue de base ou tes couleurs. Un compagnon mort revient près de toi après le temps choisi ; l'équipe te
  retrouve après un voyage rapide ou un changement de carte, et part quand tu l'arrêtes ou que tu reviens au menu
  principal.
- **RÉGLAGES DE L'ÉQUIPE**, les mêmes pour tous tes compagnons, gardés par l'équipe depuis son lancement : vie, ×4
  celle de ton chasseur au départ (×1 à ×20) ; bouclier, 30 % de leur vie (0 % à 100 %) ; recharge du bouclier,
  JAMAIS au départ (5 à 120 s) ; vitesse, +20 % (0 à +50 %) ; retour après la mort, 45 s (10 à 120 s).
- **OPTIONS.** Les barres de vie à gauche, la touche du menu et celle de l'équipe. Avec le fichier `Companions Paks`,
  la vie de chaque compagnon s'affiche en bas à gauche de l'écran, et ses barres en vert quand tu le vises.

Le bouton **ACTIVÉ**, en bas à gauche de la fenêtre, allume ou éteint tout le mod.

## Avec It Follows

Les deux mods portent le même code des compagnons, [characters](../characters/). Une seule équipe tourne à la fois :
tant qu'It Follows est activé, c'est lui qui mène l'équipe, et la fenêtre de Companions le dit. Désactive It Follows
dans le menu des mods pour revenir à Companions, sans relancer le jeu. Companions demande It Follows 1.0.11 ou plus :
à côté d'une version plus ancienne, même désactivée, il ne lance pas d'équipe et demande de la mettre à jour. Les deux
mods utilisent les deux mêmes fichiers `.pak` pour les barres.

## Installation

1. Installe le [SDK Python de Borderlands 4](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Copie `companions.sdkmod` dans `...\Borderlands 4\sdk_mods\`.
3. Pour les barres de vie, copie les deux fichiers `.pak` du fichier `Companions Paks`, sur Nexus, dans
   `...\Borderlands 4\OakGame\Content\Paks\`.
4. Lance le jeu, charge ta partie, ouvre la fenêtre et lance ton équipe.

Pour désinstaller, arrête ton équipe, puis supprime `companions.sdkmod`, et les deux fichiers `it-follows-…_999_P.pak`
sauf si It Follows s'en sert. Le mod ne touche pas à ta sauvegarde.

## Tests

Lance chaque test à part depuis ce dossier, par exemple `python test_session.py`. Les tests remplacent le SDK du jeu
par de faux objets (`sdk_stubs.py`, `*_fixture.py`), et chargent le code des compagnons depuis
[characters](../characters/), à côté de ce dossier. `test_mod.py` construit le mod sans aucun fichier d'It Follows là
où Python cherche. Chaque test écrit une ligne `RESULTAT:` et se termine par un code non nul en cas d'échec.

## Limites connues

- Les compagnons ont été testés en solo uniquement.
