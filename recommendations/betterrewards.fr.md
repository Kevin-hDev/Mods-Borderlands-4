# BetterRewards

BetterRewards réunit des récompenses ajustées pour le jeu en solo en Difficile et en Chasseur de l'Arche ultime (UVH), un niveau maximum porté à 100, encore expérimental, et une fonction de retour au jeu d'origine (Return to vanilla and disable). Son créateur l'a conçu pour une progression du personnage plus longue, moins de farm répétitif, et une raison de continuer à chercher un meilleur équipement. C'est une bêta publique.

![Un distributeur qui propose un bouclier de niveau 100](images/betterrewards/vending-level-100.jpg){: width="1600" height="902"}

## Expérience et argent

| Mode en cours | XP du personnage | XP de spécialisation débloquée | Argent gagné |
|---|---|---|---|
| Difficile, sans UVH actif | ×1,25 | ×1,25 | ×1,25 |
| UVH | ×1,30 | ×1,30 | ×1,30 |

Ces multiplicateurs s'appliquent aux récompenses réelles du jeu d'origine dans chaque mode. Les bonus de Difficile et d'UVH se remplacent l'un l'autre ; ils ne se cumulent pas. Tous les rangs d'UVH pris en charge aujourd'hui ont les mêmes réglages.

- Le bonus de spécialisation ne s'applique qu'une fois la spécialisation débloquée.
- Les prix d'achat et les autres monnaies ne changent pas.
- Seul le jeu en solo en Difficile et en UVH est ajusté. Les récompenses en Facile et en Normal ne changent pas.
- Les ennemis ne reçoivent aucun multiplicateur de dégâts, de vie ou de nombre, même si les niveaux et les points de compétence en plus rendent le joueur plus fort.

## Choisis ton réglage de butin : n'en installe qu'un

| Réglage | Difficile | UVH |
|---|---|---|
| Standard | ×1,50 | ×1,75 |
| Enhanced | ×3,00 | ×3,50 |
| Insane | ×10,00 | ×12,00 |
| MaxLoot | ×10 000 | ×10 000 |

Les réglages modifient le poids des objets légendaires et nacrés dans le butin, et les chances de butin propre à chaque boss pris en compte ; ils ne garantissent pas que chaque objet soit légendaire ou nacré. MaxLoot sert aux essais ou au plaisir du butin à profusion. Chaque ZIP a un réglage fixe : pour en changer, quitte complètement le jeu et installe l'autre ZIP comme expliqué plus bas. Les quatre réglages ont aujourd'hui les mêmes multiplicateurs d'expérience et d'argent.

## Niveau 100 (expérimental)

- Après avoir fini l'histoire principale et débloqué l'UVH, entre en UVH en solo avec BetterRewards activé : ce personnage est alors inscrit pour le niveau maximum 100.
- Le personnage reste inscrit quand tu reviens à une autre difficulté en solo.
- Un personnage déjà entré en UVH avant doit y entrer à nouveau avec le mod activé pour être inscrit.
- Aucun niveau, aucune expérience ni aucun point de compétence n'est donné directement : continue à monter de niveau normalement.
- Les niveaux 71 à 100 donnent leurs points de compétence comme d'habitude, soit 30 points de compétence de personnage en plus au total.
- L'équipement et les ennemis suivent les règles de niveau habituelles du jeu ; certains ennemis peuvent dépasser le niveau 100.

![L'écran des compétences d'un personnage de niveau 100](images/betterrewards/skills-level-100.jpg){: width="1600" height="898" loading="lazy"}

## Installation

BetterRewards a besoin du BL4 PythonSDK de la communauté (Oak2 Mod Manager), à installer à part : [guide d'installation](https://bl-sdk.github.io/oak2-mod-db/).

Pour avoir un menu MODS graphique dans le jeu, tu peux aussi installer [Mod Settings](https://www.nexusmods.com/borderlands4/mods/388) (facultatif). Il lui faut ses deux fichiers, `mod_settings.sdkmod` et `mod-settings_999_P.pak`, installés comme l'explique sa page ; ils ne sont pas fournis avec BetterRewards. Sans Mod Settings, le menu Mods du SDK marche toujours.

1. Sauvegarde et quitte complètement le jeu, puis fais une copie de tout ton compte de sauvegardes, sauvegardes de personnage et sauvegardes partagées comprises.
2. Installe le BL4 PythonSDK en suivant son guide.
3. Télécharge un des quatre ZIP, un par réglage de butin, sur la page Nexus.
4. Extrais son dossier `bl4_hard_rewards` dans le dossier `sdk_mods` du jeu.
5. Active BetterRewards dans le menu des mods si besoin.

Pour mettre à jour ou changer de réglage, remplace les fichiers fournis dans le même dossier. Garde ton `level80_unlocks.json`, les réglages du SDK, `return_python_backups`, `return_python_state.json` et les anciennes copies `return_jobs` s'il y en a. Ne renomme pas de dossier pour faire tourner plusieurs copies. Ne remplace pas les fichiers du mod pendant que le jeu tourne.

Un mod désactivé après un retour au jeu d'origine reste désactivé jusqu'à ce que tu le réactives, et une mise à jour ne rend pas ta progression de haut niveau. Si tu as déjà confirmé Return to vanilla, laisse-le aller au bout et attends « Saved data verified; Mod DISABLED » avant de mettre à jour ou de changer de réglage.

## Le menu en jeu

Avec Mod Settings installé, ouvre **MODS → Better Rewards** dans le jeu ; sans lui, passe par le menu Mods du SDK. La page montre le réglage installé, les bonus réglés, l'état des récompenses et le bouton Return to vanilla and disable. L'état se met à jour quand tu fermes la page et que tu la rouvres.

## Avant de désinstaller ou de revenir au jeu d'origine

**Ne supprime pas simplement le mod pour charger ensuite un personnage de haut niveau.** Le retour baisse les niveaux, et réactiver le mod ne rend pas ta progression de haut niveau.

Pour désinstaller le mod et revenir au jeu d'origine :

1. Garde BetterRewards installé et activé. Sauvegarde normalement, et coupe temporairement Steam Cloud pour ce jeu.
2. Déplace l'équipement au-dessus du niveau 70 depuis la banque, Lost Loot et le Reward Center vers le sac du personnage en cours, puis sauvegarde à nouveau. Les récompenses des boss mondiaux sont dans le Reward Center, pas dans Lost Loot.
3. Charge en solo le personnage que tu veux faire revenir au jeu d'origine, et sors de tout véhicule. Ouvre MODS → Better Rewards si tu as Mod Settings, ou trouve BetterRewards dans le menu Mods du SDK.
4. Presse une fois Return to vanilla and disable pour préparer le retour, et lis l'avertissement. Attends au moins 1 seconde, puis presse le même bouton une seconde fois, dans les 10 secondes après le premier appui, pour confirmer. Des appuis rapides à la suite ne confirment pas. Pour annuler, arrête d'appuyer et laisse la demande expirer ; une demande expirée doit être préparée à nouveau.
5. Ferme le menu et attends « Converted; guard remains ON », puis sauvegarde tout de suite et reviens au menu principal. Ne continue pas à farmer.
6. Au menu principal, attends « Saved data verified; Mod DISABLED » : voir le niveau 70 ne suffit pas, le retour n'est terminé qu'une fois ce message affiché. Si besoin, ferme et rouvre la page de BetterRewards pour mettre son état à jour.
7. Quitte complètement le jeu, relance-le avec BetterRewards toujours désactivé, et vérifie ton personnage, ton équipement et tes points de compétence. Sauvegarde normalement, puis recharge pour vérifier ce qui a été sauvegardé.
8. Quitte complètement le jeu, mets toute la copie faite par le retour en lieu sûr hors du dossier du mod, et seulement ensuite retire le mod si tu le veux.

Les messages du mod s'affichent en chinois et en anglais, et son choix de menu s'écrit « 返回原版并停用 / Return to vanilla and disable ».

Si le mod trouve des données de haut niveau sur un autre personnage, ou dans des objets partagés, cachés ou non récupérés, il ne termine pas le retour et garde sa protection active. Ne le désinstalle pas et ne contourne pas ses vérifications avant d'avoir vu « Saved data verified; Mod DISABLED ». Un retour ne convertit que le personnage chargé, pas tous les personnages du compte.

Ce que le retour change :

- Un personnage au-dessus du niveau 70 redescend au niveau 70, avec 69 points de compétence de personnage au total. Ses compétences de personnage sont remises à zéro et doivent être réattribuées.
- Un personnage au niveau 70 ou en dessous garde son niveau.
- L'équipement porté ou équipé au-dessus du niveau 70 redescend au niveau 70, avec des statistiques ajustées à son nouveau niveau.
- La spécialisation, l'argent et l'avancée des missions sont gardés.

Le retour commence par une copie locale des derniers fichiers sauvegardés de tout le compte. La conversion elle-même porte sur le personnage chargé et les objets qu'il porte ou équipe. Les copies sont dans `bl4_hard_rewards/return_python_backups/job-id/original` : avant de retirer le mod, mets en lieu sûr hors du dossier du mod tout le dossier `job-id`, avec ses fichiers de suivi et ses fichiers d'origine. Si tu as utilisé une ancienne version et que tu as un dossier `return_jobs`, garde aussi ses copies.

Tout se passe sur ton ordinateur ; aucune sauvegarde n'est envoyée en ligne, et il ne faut ni PowerShell, ni navigateur, ni outil extérieur. La vérification automatique prend en charge l'organisation des sauvegardes de Steam sur Windows, avec un seul dossier de compte Steam identifiable.

## Compatibilité

- Windows x64, Steam, jeu en solo.
- Cette version est adaptée au BuildID Steam 26007962. Après une mise à jour du jeu, vérifie la compatibilité sur la page Nexus avant de charger un personnage de haut niveau.
- Évite de l'associer à d'autres mods ou trainers qui modifient les mêmes systèmes d'expérience, d'argent, de butin ou de niveau maximum.

## Signaler un bug

Signale les bugs sur la page Nexus, avec :

- ta version de BetterRewards ;
- ton réglage de butin ;
- la difficulté de ta partie et ton rang d'UVH ;
- tes autres mods installés ;
- ce que tu faisais exactement quand le problème est arrivé ;
- pour un problème de niveau maximum ou de retour, le niveau de ton personnage, et s'il est entré en UVH en solo avec BetterRewards activé pour s'inscrire au niveau 100.

Si un retour n'est pas allé au bout, garde BetterRewards installé et garde les copies complètes pendant que tu signales le problème.
