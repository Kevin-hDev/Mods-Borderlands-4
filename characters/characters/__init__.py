"""The characters of the game our mods have born and drive (decision 69 of docs/renforts): their spawning camps, the
game's objects read, their walk, health, shield, target and combat zone, the journal and the game's thread; and the
companions who follow the hunter (companions/).

One source, mods/perso/characters/source; outils/deploy_sdkmods.py ships a copy of it inside each mod that carries
it (SHARED_PACKAGES), as <mod>/characters: It Follows and Companions. No mod needs another to run, and nothing here
names one: what differs from a mod to the other (levels, settings, options, texts, its window) stays in that mod,
which hands it in (companions/tuning.py, report.named).
"""
