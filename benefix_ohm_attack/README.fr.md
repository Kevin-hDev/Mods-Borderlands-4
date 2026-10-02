# Benefix Ohm Attack

Lance un rayon d'attaque avec la main dans Borderlands 4, avec six éléments au choix et des dégâts qui évoluent en
fonction de ton niveau.

Testé en solo sur la version du jeu **1.10.2-4845623**, avec tous les chasseurs, au clavier et à la manette. Windows
seulement.

[English version](README.md)

## Ce que fait le mod

Tiens la touche que tu as choisie : ta main gauche lance un rayon d'énergie sur ce que tu vises.

- **Le rayon** part de ta main gauche, sans limite de portée, et touche l'ennemi visé cinq fois par seconde. Il
  marche à la première et à la troisième personne, arme sortie ou rangée.
- **Six éléments** : feu, électrique, corrosif, cryo, radiation, ou cinétique (sans élément, un éclair blanc).
- **Des dégâts qui suivent ton niveau**, comme ceux d'une arme. Tu règles leur force de départ.
- **Aucune munition** : l'attaque consomme sa propre énergie, de 100, montrée par une nouvelle barre sous ta barre
  d'endurance. Vide, le rayon s'arrête ; l'énergie revient toute seule après un court délai.

Ouvre la console avec `~`, tape `mods`, puis choisis **Benefix Ohm Attack** : son menu, en français et en anglais,
a deux pages.

| Page | Réglage | Valeurs |
|---|---|---|
| RAYON | Élément | Feu au départ |
| RAYON | Dégâts par seconde | De 5 à 2 000, 75 au départ : la valeur au niveau 1 |
| RAYON | Barre d'énergie | Affichée ou cachée |
| RAYON | Énergie par seconde | De 0 à 100, 20 au départ ; à 0, l'énergie ne baisse jamais |
| RAYON | Recharge par seconde | De 1 à 100, 25 au départ |
| RAYON | Délai avant recharge | De 0 à 10 secondes, 2 au départ |
| COMMANDES | Lancer le rayon | Clavier/souris et manette |

Aucune touche n'est réglée au départ : choisis la tienne dans la page COMMANDES avant de jouer.

## Deux fichiers

Le mod sort en deux fichiers sur Nexus Mods :

- **Benefix Ohm Attack**, le fichier principal : `benefix_ohm_attack.sdkmod`.
- **Benefix Ohm Attack Paks**, dans les fichiers optionnels : quatre fichiers du jeu. `000_BenefixOhmAttack_999_P`
  (`.pak`, `.ucas`, `.utoc`) apporte la main gauche levée ; `pakchunk998-windows_998_P.pak` apporte la barre
  d'énergie.

Sans le second, le rayon marche quand même, mais ta main gauche ne se lève pas et la barre d'énergie ne s'affiche
pas.

## Installation

1. Installe le [SDK Python de Borderlands 4](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Copie `benefix_ohm_attack.sdkmod` dans `...\Borderlands 4\sdk_mods\`.
3. Copie les quatre fichiers de Benefix Ohm Attack Paks dans `...\Borderlands 4\OakGame\Content\Paks\`.
4. Lance le jeu, ouvre le menu du mod et choisis ta touche dans la page COMMANDES.

Avec Vortex, installe les deux fichiers : chacun va tout seul dans son dossier.

Les quatre fichiers du jeu sont fabriqués à partir des fichiers du jeu lui-même : ils ne sont pas dans ce dépôt,
seulement dans le fichier Benefix Ohm Attack Paks sur Nexus.

## Tests

Lance chaque test séparément depuis ce dossier, par exemple `python test_attack.py`. Les tests remplacent le SDK du
jeu par des doublures (`sdk_stubs.py`, `*_fixture.py`). Chaque test écrit une ligne `RESULTAT:` et sort avec un code
non nul en cas d'échec.

## Limites connues

- Pas testé en coopération, sur Linux ni sur Steam Deck.
- La barre d'énergie passe par le fichier du jeu qui dessine la barre d'endurance. Un autre mod qui change cette
  barre peut entrer en conflit avec elle. Après une mise à jour du jeu, si ta barre d'endurance s'affiche mal,
  retire `pakchunk998-windows_998_P.pak` du dossier Paks en attendant une mise à jour du mod.
- Une mise à jour du jeu peut déplacer ou renommer les effets et les animations que le mod utilise.
