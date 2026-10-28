# Dépannage

Cherche ce que tu vois. Chaque entrée dit pourquoi ça arrive et quoi faire.

Les lignes de Mod Settings dans le journal du SDK commencent par `[ModSettings]`. Le journal est
`...\Borderlands 4\OakGame\Binaries\Win64\Plugins\unrealsdk.log`, et il est réécrit à chaque lancement du jeu :
copie-le avant de relancer. Si rien ici ne t'aide, signale-le dans l'[onglet Bugs de la page Nexus](https://www.nexusmods.com/borderlands4/mods/388?tab=bugs) avec ce fichier.

## Pour les joueurs

### Il n'y a pas d'entrée MODS dans le menu

**Pourquoi :** l'entrée MODS vient du paquet `mod-settings_999_P.pak`. Il n'est pas dans
`...\Borderlands 4\OakGame\Content\Paks\`, ou un autre mod remplace aussi le menu pause ou le menu principal : un
seul des deux peut l'emporter.

**Quoi faire :** mets le paquet à sa place ; il est dans le fichier Nexus « Mod Settings Paks ». Si un autre mod
change ces menus, retire-le pour essayer.

### MODS affiche « MOD SETTINGS NE RÉPOND PAS »

**Pourquoi :** la page est là, mais le mod Python ne répond pas. Le SDK Python n'est pas installé,
`mod_settings.sdkmod` n'est pas dans `...\Borderlands 4\sdk_mods\`, Mod Settings est éteint dans la console du SDK, ou
il n'a pas pu démarrer.

**Quoi faire :** installe le SDK et `mod_settings.sdkmod` (voir le [README](README.fr.md)). Ouvre la console du SDK
(`~`, puis `mods`) et vérifie que Mod Settings est allumé. Sinon, cherche `[ModSettings]` dans le journal :

- aucune ligne : le SDK n'a pas chargé Mod Settings, ou il est éteint ;
- `START_FAILED port_in_use_or_refused` : un autre programme utilise le port 38791, ou Mod Settings vient d'être
  éteint et ne l'a pas encore libéré. Attends quelques secondes, puis éteins et rallume Mod Settings dans la console ;
- `START_TIMEOUT` : éteins et rallume Mod Settings dans la console ;
- une autre ligne `START_FAILED` : éteins et rallume Mod Settings dans la console. Si elle revient, signale-la avec
  le journal.

### MODS affiche « LA LISTE DES MODS N'EST PAS PRÊTE »

**Pourquoi :** le mod Python répond, mais il n'a pas encore fini de lire la liste des mods. Si le message revient à
chaque ouverture et que le journal contient `MODEL_TOO_BIG`, la liste de tes mods est trop grande pour MODS.

**Quoi faire :** ferme MODS et rouvre-le. Si le message revient, signale-le avec le journal.

### MODS affiche « LA CAPTURE DE TOUCHE DEMANDE MOD SETTINGS »

**Pourquoi :** changer une touche passe par le mod Python. Il ne répond pas, ou il n'a pas encore envoyé la liste des
mods.

**Quoi faire :** attends un instant, puis réessaie. Si le message revient, voir « MOD SETTINGS NE RÉPOND PAS », plus
haut.

### MODS affiche « CHANGEMENT REFUSÉ » suivi d'un nombre

**Pourquoi :** le changement n'a pas été appliqué, et la ligne montre de nouveau la valeur du mod. Le nombre dit
pourquoi :

- 0 : Mod Settings n'a pas répondu à temps, ou il est éteint (voir « MOD SETTINGS NE RÉPOND PAS », plus haut) ;
- 409 : la page avait encore l'ancienne liste des réglages, par exemple parce qu'un réglage a changé pendant que MODS
  s'ouvrait ;
- 403 : ce réglage ne peut pas être changé ;
- 400 : la valeur sort de ce que le mod accepte ;
- 503 : le jeu a trop de changements en attente.

**Quoi faire :** refais le changement. S'il est encore refusé, ferme MODS et rouvre-le.

### Un mod n'est pas dans la liste

**Pourquoi :** MODS montre les mods du SDK Python, les mêmes que la console du SDK. Un mod installé autrement, par
exemple un paquet `.pak` seul, n'y est pas. Au-delà de 64 mods, les suivants ne sont pas affichés.

**Quoi faire :** regarde si le mod est dans la console du SDK (`~`, puis `mods`). S'il y est et pas dans MODS,
signale-le avec le journal.

### Un mod affiche « Aucun réglage », ou moins de réglages que dans sa fenêtre

**Pourquoi :** MODS montre ce que le mod déclare au SDK, comme la console. Un mod qui a sa propre fenêtre de réglages
peut n'y déclarer qu'une partie de ses réglages, ou aucun.

**Quoi faire :** règle ce mod dans sa propre fenêtre, ouverte comme son créateur l'indique. Si son créateur veut le
voir en entier dans MODS, le [guide pour les créateurs de mods](MOD_AUTHORS.fr.md) lui explique comment.

### Un curseur est revenu à son ancienne valeur après un plantage

**Pourquoi :** un curseur est enregistré quand tu fermes MODS, ou au changement suivant d'un autre réglage. Un
plantage avant perd sa dernière valeur.

**Quoi faire :** règle-le de nouveau, puis ferme MODS.

### Au menu principal, Échap ouvre « Quitter le jeu »

**Pourquoi :** au menu principal, MODS est dessiné dans la page du menu. Pour le jeu, Échap veut alors dire
« quitter », et il ouvre cette fenêtre dans son propre code, qu'un mod ne peut pas retenir. Dans le menu pause, Échap
marche normalement.

**Quoi faire :** clique Annuler, ou utilise RETOUR et FERMER.

### Le menu pause ou le menu principal se comporte mal après une mise à jour du jeu

**Pourquoi :** le paquet contient des copies de ces menus, faites sur la version testée du jeu. Une mise à jour qui
les change les rend anciennes (voir [Comment ça marche](HOW_IT_WORKS.fr.md)).

**Quoi faire :** retire `mod-settings_999_P.pak` en attendant une mise à jour de Mod Settings. Tes réglages ne
bougent pas.

### MODS est en anglais alors que le jeu est dans une autre langue

**Pourquoi :** les textes de MODS existent en anglais, en français et en chinois simplifié. Pour les autres langues,
ils restent en anglais. Les noms et les descriptions des réglages sont ceux que chaque mod donne, souvent en anglais.

**Quoi faire :** aucun réglage ne change cela. Si tu veux MODS dans ta langue, demande-le dans l'[onglet Posts de la page Nexus](https://www.nexusmods.com/borderlands4/mods/388?tab=posts).

## Pour les créateurs de mods

Le [guide pour les créateurs de mods](MOD_AUTHORS.fr.md) explique comment MODS affiche tes options. Ici, seulement
les symptômes, et la partie du guide qui y répond.

### Une option de ton mod n'apparaît pas

**Pourquoi :** son type n'est pas lu par MODS, ses valeurs ne sont pas valides, elle dépasse une limite, ou elle est
cachée.

**Quoi faire :** cherche la ligne `[ModSettings] MODEL_BUILT` dans le journal. Ses compteurs `unsupported`,
`truncated` et `failed_mods` disent ce qui a été écarté, en totaux pour tous les mods ensemble. Le guide l'explique à « Vérifier ton mod », avec « Les types
d'options » et « Les limites ».

### Toutes tes options sont dans l'onglet Général, ou leur ordre change

**Pourquoi :** sans `build_mod(options=[...])`, le SDK ramasse les options de ton module dans un ordre qui peut
changer, et il ignore tes `GroupedOption` et tes `NestedOption`.

**Quoi faire :** passe tes options à `build_mod(options=[...])`. Voir « Ranger tes options » dans le guide.

### Ta fonction `on_change` lit l'ancienne valeur

**Pourquoi :** le SDK l'appelle avant de changer la valeur.

**Quoi faire :** lis la nouvelle valeur dans son argument `value`. Voir « Quand un changement arrive dans ton mod »
dans le guide.

### Le jeu saccade quand on fait glisser un curseur de ton mod

**Pourquoi :** un curseur envoie sa valeur jusqu'à dix fois par seconde, et ta fonction `on_change` est appelée à
chaque fois.

**Quoi faire :** garde-la légère : pas d'écriture de fichier ni de recherche coûteuse.

### MODS met du temps à s'ouvrir avec ton mod

**Pourquoi :** à chaque ouverture, MODS appelle la fonction qui liste les options de chaque mod
(`iter_display_options`), sur le fil du jeu. Si la tienne fait un travail lourd, le jeu se fige le temps qu'elle
tourne, et MODS peut montrer la liste d'avant jusqu'à l'ouverture suivante.

**Quoi faire :** garde cette fonction légère : qu'elle rende tes options, sans rien calculer ni charger.
