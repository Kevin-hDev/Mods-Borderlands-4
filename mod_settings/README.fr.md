# Mod Settings

Un menu MODS ajouté au menu pause et au menu principal de Borderlands 4, au design de l'écran Options du jeu, pour
voir et régler tous les mods du SDK Python de Borderlands 4.

**Version ALPHA** : une première version, pas terminée à 100 %. Elle fonctionne en l'état, mais elle n'a pas encore
été assez testée, et elle ne marchera peut-être pas avec tous les mods.

Testé sur la version du jeu **1.11.0-4906557**, version Steam, en solo, au clavier, à la souris et à la manette, avec
22 à 29 mods installés. Jamais essayé en coopération, ni sur la version Epic Games. Si ça se passe mal chez toi, regarde
d'abord le [dépannage](TROUBLESHOOTING.fr.md) et les [questions fréquentes](FAQ.fr.md), puis ouvre une issue avec le
fichier de log, `...\Borderlands 4\OakGame\Binaries\Win64\Plugins\unrealsdk.log`, copié avant de
relancer le jeu (il est réécrit à chaque lancement).

**Contrairement au reste de ce dépôt, Mod Settings est sous [licence Mozilla Public License 2.0](LICENSE).**

## Ce qu'il fait

- Une entrée MODS dans le menu pause et dans le menu principal ouvre une page pour tous les mods du SDK détectés,
  construite avec les pièces de l'écran Options du jeu.
- Chaque mod a sa page : ses réglages en onglets et sous-onglets, avec la description du réglage choisi. Un mod
  s'allume ou s'éteint quand il le permet.
- Interrupteurs, curseurs, choix à flèches, listes, touches et boutons, comme dans le menu des mods de la console du
  SDK. Pour changer une touche, clique-la, puis appuie sur la nouvelle ; Échap annule.
- Un changement est enregistré tout de suite, sauf celui d'un curseur : il l'est à la fermeture de MODS, ou au
  changement suivant d'un autre réglage. C'est le SDK lui-même qui enregistre, dans
  `...\Borderlands 4\sdk_mods\settings\`.
- Les textes de MODS suivent la langue du jeu : anglais, français ou chinois simplifié, anglais pour les autres
  langues. Les noms et descriptions des réglages restent ceux que chaque mod donne.

## Pour les créateurs de mods

Tu n'as rien à ajouter à ton code : MODS affiche les options que ton mod déclare avec `mods_base`, comme le menu des
mods de la console. Comment chaque type d'option s'affiche, comment ranger tes options en onglets, et les limites :
voir le [guide pour les créateurs de mods](MOD_AUTHORS.fr.md), aussi en [anglais](MOD_AUTHORS.md), en
[chinois](MOD_AUTHORS.zh.md) et en [japonais](MOD_AUTHORS.ja.md).

## Comment il est fait

Ce qui se passe quand tu changes un réglage, et ce que Mod Settings touche : voir
[Comment ça marche](HOW_IT_WORKS.fr.md). Deux parties, toutes deux dans ce dossier :

- `mod_settings/`, le paquet Python, livré en `mod_settings.sdkmod`. Il lit les mods et les options du SDK et les
  sert à la page par un service local sur `127.0.0.1`, qui refuse les demandes des pages web. Chaque changement
  est appliqué sur le fil du jeu lui-même.
- `page/`, le script et la feuille de style de la page, livrés dans `mod-settings_999_P.pak` avec des copies du menu
  pause et du menu principal du jeu qui les chargent. `build_pak.py` fabrique ce paquet à partir des menus les plus
  récents du jeu ; `install_pak.py` l'installe ou le retire jeu fermé, et le vérifie à tout moment.
  `build_pak.py` a besoin de deux outils extérieurs qui lisent et écrivent les paquets du jeu ; `install_pak.py`
  a besoin de `deploy_sdkmods.py`, qui lui donne le dossier du jeu, et ne marche que sous Windows. Les trois sont
  nommés dans `game_tools.py` à leur place dans l'atelier de l'auteur : fais-les pointer vers tes propres copies. Le paquet contient des fichiers du jeu : il n'est
  pas dans ce dépôt, seulement sur Nexus.

## Installation

1. Installe le [SDK Python de Borderlands 4](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Copie `mod_settings.sdkmod` dans `...\Borderlands 4\sdk_mods\`.
3. Copie `mod-settings_999_P.pak`, du fichier Nexus « Mod Settings Paks », dans
   `...\Borderlands 4\OakGame\Content\Paks\`. Il faut les deux fichiers.
4. Lance le jeu, ouvre le menu pause ou va au menu principal, puis choisis MODS.

Pour désinstaller, supprime les deux fichiers. Le menu pause et le menu principal reviennent comme avant, et les
réglages de tes autres mods ne bougent pas.

## Tests

Lance chaque test séparément depuis ce dossier : `python test_bridge.py`, et `node test_logic.js` et `node test_layout.js`
pour la page. Les tests remplacent le SDK du jeu par des faux objets (`fixture_sdk.py`, `fixture_world.py`,
`fixture_test_mod.py`). Chacun affiche une ligne `RESULTAT:` et se termine par un code non nul en cas d'échec. Les
classes d'options et l'enregistrement sont ceux du SDK, lus dans un `mods_base.sdkmod` installé : donne à
`BL4_SDK_MODS` le chemin de ton dossier `...\Borderlands 4\sdk_mods`, sinon les tests qui en ont besoin affichent
`SKIP`.
`test_page_browser.py` fait tourner la page dans Chrome sans fenêtre, sur les fichiers d'interface du jeu ; sans
Chrome à son emplacement Windows habituel, ou sans l'outil qui lit ces fichiers dans les paquets du jeu, il
affiche `SKIP`.

## Limites connues

- Au menu principal, Échap dans MODS ouvre aussi la fenêtre « Quitter le jeu » : clique Annuler, ou utilise RETOUR et
  FERMER. Dans le menu pause, Échap marche normalement.
- Un mod qui a sa propre fenêtre de réglages n'apparaît dans MODS qu'avec ce qu'il déclare au SDK.
- Mod Settings lui-même ne s'éteint pas depuis MODS : passe par la console du SDK (`~`, puis `mods`).
- Un autre mod qui remplace le menu pause ou le menu principal du jeu peut être en conflit. Une mise à jour du jeu peut
  changer ces menus : si l'un d'eux se comporte mal après une mise à jour, retire le paquet en attendant une mise à
  jour de Mod Settings.

## Licence

Mod Settings est sous licence Mozilla Public License 2.0 : voir [LICENSE](LICENSE), ou <https://mozilla.org/MPL/2.0/>.
Si tu redistribues ses fichiers modifiés, ils restent sous MPL-2.0 et leur code source doit rester disponible. Si tu
reprends du code, garde les mentions en tête de chaque fichier : les droits d'auteur (`Copyright (c) 2026 kevin-hDev`)
et l'avis de licence. Les fichiers du jeu contenus dans le paquet appartiennent à Gearbox Software et 2K et ne sont
pas couverts par cette licence.

L'idée vient de Mod Settings pour Cyberpunk 2077, de jackhumbert.
