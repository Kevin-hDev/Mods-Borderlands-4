# Questions fréquentes

## Est-ce que Mod Settings marche sur la version Epic Games ?

Il n'a jamais été essayé sur la version Epic Games, seulement sur la version Steam 1.11.0-4906557. Si tu l'essaies,
dis-nous ce que ça donne dans une issue, avec le journal du SDK.

## Et en coopération ?

Il n'a jamais été essayé en coop. Mod Settings n'envoie et ne reçoit rien par le réseau du jeu : il ne règle que les
mods de ton PC. Ce qu'un mod fait en coop dépend de ce mod.

## Est-ce que la console du SDK sert encore ?

Oui. MODS est une autre porte vers les mêmes réglages : un changement fait dans l'une se retrouve dans l'autre, et
MODS relit tout à chaque ouverture. Pour allumer ou éteindre Mod Settings lui-même, c'est la console.

## Comment éteindre Mod Settings ?

Dans la console du SDK : `~`, puis `mods`, puis Mod Settings. Sur sa page dans MODS, son interrupteur Activé ne
répond pas : éteint depuis là, il couperait la page pendant que tu t'en sers. Éteint, l'entrée MODS reste dans le
menu, car elle vient du paquet, et MODS affiche « MOD SETTINGS NE RÉPOND PAS » quand tu l'ouvres. Pour la faire disparaître, retire
aussi le paquet `mod-settings_999_P.pak`.

## Que deviennent mes réglages si je retire Mod Settings ?

Rien ne change. Les réglages de tes mods sont enregistrés par le SDK dans `...\Borderlands 4\sdk_mods\settings\`, un
fichier par mod, et ils y restent. Retire les deux fichiers de Mod Settings : le menu pause et le menu principal
reviennent comme avant.

## Pourquoi un mod n'a-t-il pas tous ses réglages dans MODS ?

MODS montre ce que chaque mod déclare au SDK, comme la console. Un mod qui a sa propre fenêtre de réglages peut n'y
déclarer qu'une partie de ses réglages, ou aucun. Voir le [dépannage](TROUBLESHOOTING.fr.md).

## Pourquoi Mod Settings n'a-t-il pas de réglages à lui ?

Mod Settings est une autre porte vers la console du SDK, rien de plus : il montre et règle ce que chaque mod déclare,
sans ajouter ses propres réglages par-dessus. Chaque fonction en plus serait une chose de plus à casser à une mise à
jour du jeu, ou à entrer en conflit avec les mods qu'il affiche. Et un créateur qui essaie son mod dans la console l'a
aussi essayé dans MODS.

## Est-ce que Mod Settings ralentit le jeu ?

Menus fermés, il ne fait rien. À chaque ouverture de MODS, et une première fois quand le jeu charge le menu pause ou
le menu principal, il relit les réglages des mods, ce qui fige le jeu un court instant : de 0,2 à 0,35 seconde la
première fois après le lancement du jeu, puis de quelques millisecondes à 50 millisecondes, avec 22 à 29 mods
installés (mesuré en jeu).

## Est-ce que Mod Settings va sur Internet ? Est-ce sûr ?

Il ne va pas sur Internet. La page et le mod Python se parlent par un petit service qui n'écoute que ton PC, et qui
refuse les demandes des pages web ouvertes dans ton navigateur. Le détail est dans
[Comment ça marche](HOW_IT_WORKS.fr.md).

## Est-ce que je peux reprendre son code ?

Oui, sous la licence Mozilla Public License 2.0 : voir la partie Licence du [README](README.fr.md).
