# Co-op Duel

Affronte ton coéquipier dans une partie en coop de Borderlands 4, n'importe où dans le monde : des manches sans fin, un
KO de 3 secondes au sol, puis on se relève sur place. Seul l'hôte a besoin du mod.

Testé sur la version du jeu **1.10.2-4845623**, sous Windows : l'hôte sur la version Steam, l'invité sur la version Epic
Games, avec et sans mods chez l'invité. Testé à deux joueurs seulement.

## Ce que fait le mod

- L'hôte et son invité peuvent se tirer dessus et se blesser, n'importe où dans le monde.
- Celui qui tombe reste au sol 3 secondes, sans pouvoir blesser ni être blessé, puis se relève sur place avec sa vie et
  son bouclier pleins. Pas de mort, pas de retour au point de réapparition.
- Chaque chute donne la manche à l'autre joueur. Le duel n'a pas de fin : il continue jusqu'à ce que l'hôte l'arrête.
- À chaque manche, le score s'affiche quelques secondes en haut de l'écran de l'hôte, avec le pseudo des deux joueurs.
- Les ennemis du coin attaquent les deux joueurs : aucun ne reçoit d'alliés.
- Quand le duel s'arrête, vous redevenez des coéquipiers normaux. Il s'arrête tout seul si l'invité quitte la partie,
  si un troisième joueur arrive, ou au voyage rapide.

Ton invité n'a rien à installer, ni le mod ni le SDK. Le score ne s'affiche que sur l'écran de l'hôte.

## Touches et fenêtre

- **F9** ouvre la fenêtre du mod, **N** lance le duel ou l'arrête. Les deux se changent dans la page OPTIONS.
- La fenêtre, en français, en anglais et en chinois simplifié, a deux pages : DUEL, pour lancer et arrêter le duel et
  voir le score, et OPTIONS, les deux touches. Tu peux aussi l'ouvrir depuis la console : `~`, `mods`, puis
  **Co-op Duel**.
- Si le duel ne peut pas commencer (pas d'invité, un joueur en véhicule ou à terre), le mod dit pourquoi et quoi faire.

Le bouton **ACTIVÉ**, en bas à gauche de la fenêtre, allume ou éteint tout le mod.

## Installation

1. Installe le [SDK Python de Borderlands 4](https://github.com/bl-sdk/oak2-mod-manager/releases/latest), sur le PC de
   l'hôte.
2. Copie `coop_duel.sdkmod` dans `...\Borderlands 4\sdk_mods\`.
3. Lance le jeu, invite un ami dans ta partie, mettez-vous à côté, puis appuie sur N.

Pour désinstaller, supprime `coop_duel.sdkmod`. Le mod ne touche pas à ta sauvegarde.

## Tests

Lance chaque test séparément depuis ce dossier, par exemple `python test_duel.py`. Les tests remplacent le SDK du jeu
par des imitations (`sdk_stubs.py`, `game_fixture.py`, `panel_fixture.py`). Chaque test affiche une ligne `RESULTAT:`
et se termine avec un code non nul en cas d'échec.

## Limites connues

- Duel à deux joueurs seulement pour l'instant.
- Toute chute compte, même si c'est un ennemi qui a fait tomber le joueur.
- Un hôte sur la version Epic Games n'a pas été testé.
- Un autre mod qui change les équipes des joueurs peut entrer en conflit avec celui-ci.
