# It Follows

Deux modes pour durcir Borderlands 4 : une refonte des ennemis de ta partie normale, plus nombreux, plus rapides et
plus résistants, et un mode Horde où une horde sans fin te suit partout.

Testé en solo sur la version du jeu **1.10.2-4845623**, version Steam, sous Windows.

## Ce qu'il fait

Appuie sur **F5** pendant le jeu, ou ouvre la console avec `~`, tape `mods` et choisis **It Follows** : sa fenêtre, en
anglais et en français, a quatre pages. Le jeu se met en pause tant qu'elle est ouverte. Tu lances un mode à la fois.

- **MODE HORDE [BETA].** Appuie sur START : tous les ennemis autour de toi viennent vers toi et te suivent partout. Ceux
  que tu croises en chemin rejoignent la horde, et ceux que tu tues reviennent derrière toi, de plus en plus nombreux.
  Les ennemis sont ceux des zones que tu traverses. Cinq niveaux, un bonus de vitesse des ennemis, BUFF et BUFF+, une
  durée ou aucune, et le plus d'ennemis qui te chassent en même temps, de 30 à 120. Une barre en haut à gauche de
  l'écran affiche tes tués, tes morts, la taille de la horde et le temps, qui s'arrête quand le jeu est en pause.
- **MODE NORMAL.** Joue ta partie comme d'habitude : les ennemis que tu croises sont plus nombreux, plus rapides et plus
  résistants, esquivent plus souvent et plus vite, et te poursuivent plus loin. Trois niveaux, Bandit, Senior et
  Predator. Les boss reçoivent la vie et la vitesse du niveau. Il est pensé d'abord pour commencer ou recommencer le jeu
  depuis le début, un peu comme trois niveaux de NG+, et reste utilisable en cours de partie. Il reste allumé d'une
  partie à l'autre jusqu'à ce que tu appuies sur STOP, et STOP rend les ennemis tels que le jeu les a faits.
- **Hardcore**, une option du mode normal : les ennemis se renforcent de 1 % tous les 100 ennemis tués, tout au long
  du jeu. Tu peux mettre la progression en pause, et elle est gardée quand l'option est désactivée.
- **HISTORIQUE.** Tes 20 derniers runs de la Horde.
- **OPTIONS.** La barre en jeu et sa taille.

Le bouton **ACTIVÉ**, en bas à gauche de la fenêtre, allume ou éteint tout le mod.

## Installation

1. Installe le [SDK Python de Borderlands 4](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Copie `it_follows.sdkmod` dans `...\Borderlands 4\sdk_mods\`.
3. Lance le jeu, charge ta partie et appuie sur F5.

Pour désinstaller, arrête le mode en cours avec STOP, puis supprime `it_follows.sdkmod`. Le mod ne touche pas à ta
sauvegarde.

## Tests

Lance chaque test à part depuis ce dossier, par exemple `python test_wave.py`. Les tests remplacent le SDK du jeu par
de faux objets (`sdk_stubs.py`, `*_fixture.py`). Chaque test écrit une ligne `RESULTAT:` et se termine par un code non
nul en cas d'échec.

## Limites connues

- Le mode Horde demande beaucoup à ton PC. Si le jeu ralentit, baisse « Ennemis maximum », choisis un niveau plus bas
  ou baisse les graphismes du jeu.
- « Gérer les ennemis éloignés » est toujours activé pour l'instant : ce réglage sera revu dans une prochaine version.
- Le mode Horde ne se lance pas en coopération ni en véhicule. Le mod n'a été essayé ni en coopération, ni sur la
  version Epic Games.
- Un autre mod qui change les ennemis, leur nombre ou leur vie peut entrer en conflit avec celui-ci.
