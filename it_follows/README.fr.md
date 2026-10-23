# It Follows

Deux modes pour durcir Borderlands 4 : une refonte des ennemis de ta partie normale, plus nombreux, plus rapides et
plus résistants, et un mode Horde où une horde sans fin te suit partout. Et une équipe de compagnons pour te battre à
tes côtés.

Testé sur la version du jeu du 22 octobre 2026 (build **4906557**) sous Windows, en solo sur Steam. Le mode normal a
aussi été testé en coopération à deux joueurs sur la version précédente du jeu, l'hôte sur Steam et l'invité sur Epic
Games.

## Ce qu'il fait

Appuie sur **F5** pendant le jeu, ou ouvre la console avec `~`, tape `mods` et choisis **It Follows** : sa fenêtre, en
anglais, en français et en chinois simplifié, a cinq pages. Le jeu se met en pause tant qu'elle est ouverte. Tu
lances un mode à la fois.

- **MODE HORDE [BETA].** Appuie sur START : tous les ennemis autour de toi viennent vers toi et te suivent partout. Ceux
  que tu croises en chemin rejoignent la horde, et ceux que tu tues reviennent derrière toi, de plus en plus nombreux.
  Les ennemis sont ceux des zones que tu traverses. Cinq niveaux, un bonus de vitesse des ennemis, BUFF et BUFF+, une
  durée ou aucune, et le plus d'ennemis qui te chassent en même temps, de 30 à 120. Un point de départ en option :
  un des sept lieux de la carte, où START t'emmène derrière un écran noir avant que le run commence. Une barre en haut à gauche de
  l'écran affiche tes tués, tes morts, la taille de la horde, le Hardcore et le temps, qui s'arrête quand le jeu est
  en pause. Le Hardcore est toujours actif dans la Horde : les ennemis se renforcent de 1 % tous les 100 ennemis tués
  pendant le run, en repartant de 0 % à chaque run.
- **MODE NORMAL.** Joue ta partie comme d'habitude : les ennemis que tu croises sont plus nombreux, plus rapides et plus
  résistants, esquivent plus souvent et plus vite, frappent plus vite, et te poursuivent plus loin. En Senior et Predator,
  les bandits armés attendent moins longtemps entre deux coups au corps à corps. Ils sursautent et tombent moins
  souvent sous tes tirs, 15 % de moins en Bandit, 25 % en Senior et 50 % en Predator, où la ligne Sans sursaut les
  supprime. Les ennemis sans bouclier en
  reçoivent un, de 40 % de leur vie, qui se recharge en Predator une fois cassé ; les ennemis armés tirent plus juste
  et leurs balles vont plus vite. Tu gagnes plus d'expérience sur les ennemis tués, et plus de munitions et d'argent
  en ramassant ; les distributeurs et les missions ne changent pas. Quatre niveaux, Bandit, Senior, Predator et God ;
  God a autant d'ennemis qu'en Predator, bien plus résistants mais un peu moins rapides, et il est pensé pour jouer
  avec tes compagnons. Les boss reçoivent la vie, la vitesse, le bouclier et la précision du niveau. En Senior,
  Predator et God, la ligne Vitesse des ennemis les rend 15 % plus lents pour ceux qui les trouvent trop rapides. Il
  est pensé d'abord pour commencer ou recommencer le jeu depuis le début, un peu comme quatre niveaux de NG+, et reste
  utilisable en cours de partie. Il
  reste allumé d'une partie à l'autre jusqu'à ce que tu appuies sur STOP, et STOP rend les ennemis tels que le jeu les
  a faits.
- **Hardcore**, une option du mode normal : les ennemis se renforcent de 1 % tous les 100 ennemis tués, tout au long
  du jeu. Seuls les tués de ton chasseur comptent, pas ceux de tes compagnons. Tu peux mettre la progression en pause, et elle est gardée quand l'option est désactivée.
- **COMPAGNONS.** Choisis jusqu'à 8 compagnons parmi 10, les 6 chasseurs de l'Arche et 4 alliés, puis lance l'équipe,
  depuis la page ou avec sa touche, F8 au départ : ils te suivent et se battent avec toi. Les chasseurs de l'Arche se
  battent avec leurs armes seulement, sans leurs compétences. La carte de chacun règle son bouclier, sa vitesse et,
  pour un chasseur, sa tenue de base ou tes couleurs. Un compagnon mort revient près de toi 45 secondes plus tard ;
  l'équipe te retrouve après un voyage rapide ou un changement de carte, et part quand tu l'arrêtes ou que tu reviens
  au menu principal. Avec le fichier `It Follows Companions Paks`, la vie de chaque compagnon s'affiche en bas à
  gauche de l'écran, et ses barres en vert quand tu le vises.
- **HISTORIQUE.** Tes 20 derniers runs de la Horde.
- **OPTIONS.** La barre en jeu et sa taille ; la machine du butin perdu jusqu'à 400 objets ; une résolution
  16:10 en plein écran ; trois profils de couleurs plus vives, avec un aperçu pour les essayer en jeu.

Le bouton **ACTIVÉ**, en bas à gauche de la fenêtre, allume ou éteint tout le mod.

## Installation

1. Installe le [SDK Python de Borderlands 4](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Copie `it_follows.sdkmod` dans `...\Borderlands 4\sdk_mods\`.
3. Pour les barres de vie des compagnons, copie les deux fichiers `.pak` du fichier `It Follows Companions Paks`, sur
   Nexus, dans `...\Borderlands 4\OakGame\Content\Paks\`.
4. Lance le jeu, charge ta partie et appuie sur F5.

Pour désinstaller, arrête le mode en cours avec STOP et ton équipe, puis supprime `it_follows.sdkmod` et les deux
fichiers `it-follows-…_999_P.pak`. Le mod ne touche pas à ta sauvegarde.

## Tests

Lance chaque test à part depuis ce dossier, par exemple `python test_wave.py`. Les tests remplacent le SDK du jeu par
de faux objets (`sdk_stubs.py`, `*_fixture.py`). Chaque test écrit une ligne `RESULTAT:` et se termine par un code non
nul en cas d'échec.

## Limites connues

- Le mode Horde demande beaucoup à ton PC. Si le jeu ralentit, baisse « Ennemis maximum », choisis un niveau plus bas
  ou baisse les graphismes du jeu.
- « Gérer les ennemis éloignés » est toujours activé pour l'instant : ce réglage sera revu dans une prochaine version.
- Le mode Horde ne se lance pas en coopération ni en véhicule ; son point de départ ne marche que depuis le monde
  ouvert.
- En coopération, chaque joueur doit avoir le mod pour que le mode normal marche pleinement.
- Un autre mod qui change les ennemis, leur nombre ou leur vie peut entrer en conflit avec celui-ci.
