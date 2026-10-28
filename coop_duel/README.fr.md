# Co-op Duel

Affronte tes coéquipiers dans une partie en coop de Borderlands 4, de 2 à 4 joueurs, chacun pour soi ou en équipes,
n'importe où dans le monde : des manches sans fin, puis on se relève sur place. Seul l'hôte a besoin du mod.

Testé sur la version du jeu **1.10.2-4845623**, sous Windows : l'hôte sur la version Steam, l'invité sur la version Epic
Games, avec et sans mods chez l'invité. **Testé à deux joueurs seulement** : le duel à 3 ou 4 joueurs n'a pas encore été
essayé. Si quelque chose ne marche pas chez toi, signale-le dans l'onglet Bugs de sa page Nexus avec le fichier de log de l'hôte,
`...\Borderlands 4\OakGame\Binaries\Win64\Plugins\unrealsdk.log`, copié avant de relancer le jeu (il est réécrit à
chaque lancement).

## Ce que fait le mod

- Les joueurs de la partie peuvent se tirer dessus et se blesser, n'importe où dans le monde : de 2 à 4 joueurs, chacun
  pour soi ou en équipes.
- Celui qui tombe reste au sol, sans être blessé, jusqu'à la fin de la manche. Ses coéquipiers peuvent le relever.
- La manche va à la dernière équipe qui a encore un joueur debout. 3 secondes plus tard, tout le monde se relève sur
  place avec sa vie et son bouclier pleins. Pas de mort, pas de retour au point de réapparition.
- Le duel n'a pas de fin : il continue jusqu'à ce que l'hôte l'arrête.
- À chaque manche, le score s'affiche quelques secondes en haut de l'écran de l'hôte, avec le pseudo des joueurs.
- Les compagnons d'un joueur attaquent l'équipe adverse. Les ennemis du coin attaquent tout le monde ; à partir de 3
  équipes, les bandits ou les soldats de l'Ordre du coin peuvent se battre aux côtés d'une équipe.
- Quand le duel s'arrête, vous redevenez des coéquipiers normaux. Il s'arrête tout seul si un joueur arrive dans la
  partie, s'il ne reste qu'une équipe, ou au voyage rapide.

Tes invités n'ont rien à installer, ni le mod ni le SDK. Le score ne s'affiche que sur l'écran de l'hôte.

## Touches et fenêtre

- **F9** ouvre la fenêtre du mod, **N** lance le duel ou l'arrête. Les deux se changent dans la page OPTIONS.
- La fenêtre, en français, en anglais et en chinois simplifié, a trois pages : DUEL, pour lancer et arrêter le duel et
  voir le score ; ÉQUIPES, où l'hôte range chaque joueur dans l'équipe 1, 2, 3 ou 4 (chacun pour soi au départ, et le
  bouton CHACUN POUR SOI y revient) ; et OPTIONS, les deux touches. Les équipes ne changent pas pendant un duel. Tu peux
  aussi ouvrir la fenêtre depuis la console : `~`, `mods`, puis **Co-op Duel**.
- Si le duel ne peut pas commencer (pas d'autre joueur, tout le monde dans la même équipe, un joueur en véhicule ou à
  terre), le mod dit pourquoi et quoi faire.

Le bouton **ACTIVÉ**, en bas à gauche de la fenêtre, allume ou éteint tout le mod.

## Installation

1. Installe le [SDK Python de Borderlands 4](https://github.com/bl-sdk/oak2-mod-manager/releases/latest), sur le PC de
   l'hôte.
2. Copie `coop_duel.sdkmod` dans `...\Borderlands 4\sdk_mods\`.
3. Lance le jeu et invite des amis dans ta partie. Pour jouer en équipes, range-les dans la page ÉQUIPES (F9).
   Mettez-vous à côté, puis appuie sur N.

Pour désinstaller, supprime `coop_duel.sdkmod`. Le mod ne touche pas à ta sauvegarde.

## Tests

Lance chaque test séparément depuis ce dossier, par exemple `python test_duel.py`. Les tests remplacent le SDK du jeu
par des imitations (`sdk_stubs.py`, `game_fixture.py`, `panel_fixture.py`). Chaque test affiche une ligne `RESULTAT:`
et se termine avec un code non nul en cas d'échec.

## Limites connues

- Testé à deux joueurs seulement.
- Toute chute compte, même si c'est un ennemi qui a fait tomber le joueur.
- Un hôte sur la version Epic Games n'a pas été testé.
- Un autre mod qui change les équipes des joueurs peut entrer en conflit avec celui-ci.
