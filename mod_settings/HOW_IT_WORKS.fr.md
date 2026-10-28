# Comment ça marche

Mod Settings tient en deux fichiers : un paquet d'interface, `mod-settings_999_P.pak`, qui dessine MODS dans le menu
du jeu, et un mod Python, `mod_settings.sdkmod`, qui lit et règle les mods du SDK. Cette page explique ce qui se passe
entre les deux, pour que tu saches ce que Mod Settings touche, et ce qu'il ne touche pas.

<img src="site/images/pause-menu.jpg" width="1200" height="986" alt="Le menu pause du jeu, avec l'entrée MODS sélectionnée">

## Le trajet d'un réglage

1. Le paquet remplace le menu pause et le menu principal du jeu par des copies qui ont une entrée MODS en plus.
2. Quand tu ouvres MODS, la page emprunte les pièces de l'écran Options du jeu : interrupteurs, curseurs, listes,
   touches et onglets. C'est pour ça qu'elle a l'apparence, les sons et les commandes du jeu.
3. La page demande la liste des mods au mod Python, par un service local de ton PC.
4. Le mod Python lit la liste des mods du SDK et les options que chacun déclare, comme le menu des mods de la console
   du SDK.
5. Quand tu changes un réglage, la page envoie la nouvelle valeur. Le mod Python vérifie qu'elle entre dans ce que le
   mod accepte, puis la donne au mod, exactement comme la console.
6. Le SDK enregistre le réglage dans `...\Borderlands 4\sdk_mods\settings\`, dans le fichier du mod.

<img src="site/images/mod-page.jpg" width="1600" height="839" alt="La page d'un mod dans MODS : ses onglets, ses curseurs, ses interrupteurs et le panneau de description">

Mod Settings ne garde aucun réglage à lui : chaque valeur vit dans le mod qui la déclare, et MODS n'en est qu'un
affichage, comme la console.

## Quand un changement compte

- **Le mod reçoit la valeur tout de suite.** Ce qu'il en fait, et quand, dépend du mod.
- **Un curseur qu'on fait glisser** envoie sa valeur au plus toutes les 100 millisecondes, et toujours la dernière.
- **Un changement est enregistré tout de suite**, sauf celui d'un curseur : il l'est quand tu fermes MODS, ou au
  changement suivant d'un autre réglage. Si le jeu plante avant, la dernière valeur de ce curseur est perdue.

## À chaque ouverture de MODS

MODS relit la liste des mods et leurs réglages à chaque ouverture, et une première fois quand le jeu charge le menu
pause ou le menu principal. Un réglage changé ailleurs, dans la console du SDK ou dans la fenêtre d'un mod, s'y voit
donc à la prochaine ouverture.

Cette lecture fige le jeu un court instant, jamais en dehors des menus : de 0,2 à 0,35 seconde la première fois après
le lancement du jeu, puis de quelques millisecondes à 50 millisecondes, avec 22 à 29 mods installés (mesuré en jeu).
Menus fermés, Mod Settings ne fait rien.

## Les fichiers du jeu, et ses mises à jour

- Le paquet contient des copies du menu pause et du menu principal du jeu, faites à partir de la version testée,
  1.11.0-4906557. Le jeu les charge à la place des siennes.
- Si une mise à jour du jeu change ces menus, le paquet garde ses anciennes copies : les menus peuvent alors perdre
  une nouveauté ou mal se comporter, jusqu'à une mise à jour de Mod Settings. Retirer le paquet rend au jeu ses
  propres menus, et tes réglages ne bougent pas.
- Un autre mod qui remplace aussi le menu pause ou le menu principal entre en conflit avec Mod Settings : un seul des
  deux peut l'emporter.
- Ces copies appartiennent à Gearbox Software et 2K. C'est pour ça que le paquet n'est que sur Nexus, et pas dans le
  dépôt GitHub.

## Le service local, et pourquoi les pages web sont refusées

La page et le mod Python se parlent par un petit service sur ton PC.

- **Il n'écoute que ton PC** (`127.0.0.1`, port 38791). Rien ne part sur Internet ni sur le réseau du jeu, en coop
  non plus.
- **Il refuse les pages web.** Il refuse toute demande qui vient d'une page web ouverte dans ton navigateur. Sans ce
  refus, un site que tu visites pendant que tu joues pourrait envoyer des demandes à ce service et changer les
  réglages de tes mods. Seuls l'interface du jeu et les programmes de ton propre PC peuvent s'en servir.
- **Chaque demande est petite et vérifiée** : son contenu fait 512 octets au plus, et une valeur qui sort de ce que le
  mod accepte est refusée.
- Si un autre programme utilise déjà ce port, Mod Settings ne démarre pas, et le journal du SDK le dit (voir le
  [dépannage](TROUBLESHOOTING.fr.md)).

## Pourquoi des limites

MODS a un plafond pour chaque liste : nombre de mods, d'options, de choix, longueur des textes. Sans eux, un mod qui
déclarerait des milliers d'options pourrait rendre la page énorme et figer le jeu à chaque ouverture. Au-delà d'une
limite, MODS cache ou coupe ce qui dépasse, alors que la console du SDK le montre. Les valeurs sont dans le
[guide pour les créateurs de mods](MOD_AUTHORS.fr.md), à « Les limites ».
