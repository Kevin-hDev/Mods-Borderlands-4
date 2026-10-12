"""The camera profile window's and PROFILES page's words (decisions of 2026-10-12, mockup
docs/mokup/menu_mods/profils/), copied into the other camera mods with them (sync_menu_sources.py). The words they share
with the COMMANDS page, the devices and CHANGE, PRESS A KEY and NONE, and the page's name on its tab or sidebar button
stay panel_i18n's.

A refusal names its cause, says that nothing is saved when nothing is, and what to do next.
"""

EN = {
    "profile_new": "NEW PROFILE",
    "profile_edit": "EDIT PROFILE",
    "profile_desc": "Tune while watching the game. CANCEL or SAVE brings the menu back; Escape closes it.",
    "profile_name": "PROFILE NAME",
    "profile_key": "PROFILE KEY",
    # The distances' short names, so they fit beside the window's narrower sliders (mockup profils/6_coin.png).
    "profile_close": "Distance: close",
    "profile_far": "Distance: far",
    # A new profile's name, numbered by the profiles (profiles.py, free_name).
    "profile_word": "Profile",
    "profile_cancel": "CANCEL",
    "profile_save": "SAVE",
    "name_invalid": "Name refused: 1 to 24 letters, digits, spaces, hyphens, apostrophes or underscores.",
    "name_taken": "Another profile already has this name: choose another one.",
    "key_taken": "Another profile already uses this key: choose another one.",
    "key_command": "This key is already a camera command's (COMMANDS page): choose another one.",
    # The COMMANDS page's answer, the other way round (panel_camera_commands.py).
    "command_held": "The profile “{name}” already has this key: choose another one, or change the profile's key in "
                    "PROFILES.",
    "key_invalid": "This key cannot switch a profile: choose another one.",
    "profiles_full": "You already have 10 profiles, the most there can be: this one is not saved.",
    "profile_unknown": "This profile no longer exists: close the window with CANCEL.",
    "save_failed": "The profiles' file could not be written: nothing is saved, your settings stay in this window.",
    "profile_refused": "This profile could not be saved: your settings stay in this window.",
    # The PROFILES page (mockup profils/3_page.png).
    "profiles_desc": "One profile on at a time. Its key switches it on; a second press brings back your CAMERA VIEW "
                     "and SHOULDER VIEW settings.",
    "profile_on": "ON",
    "profile_off": "OFF",
    "profile_modify": "EDIT",
    "profile_delete": "DELETE",
    "profile_values": "FOV {fov} · close {close} · far {far} · spacing {spacing} · height {height}. "
                      "Controller: {controller}.",
    "profile_no_key": "none",
    "toggle_failed": "The profiles' file could not be written: nothing changed.",
    "delete_failed": "The profiles' file could not be written: the profile is not deleted.",
    # DELETE's pop-up (profils/4_supprimer.png).
    "profile_delete_title": "DELETE THE PROFILE",
    "profile_delete_key": "The profile “{name}” and its key will be deleted.",
    "profile_delete_keys": "The profile “{name}” and its keys will be deleted.",
    "profile_delete_plain": "The profile “{name}” will be deleted.",
    "profile_delete_on": "It is on: the camera goes back to your CAMERA VIEW and SHOULDER VIEW settings.",
    "profile_delete_rest": "Your other profiles and your CAMERA VIEW and SHOULDER VIEW settings do not change.",
    # Over the settings a profile switched on holds (profils/5_allume.png).
    "profile_held_camera": "FOV and distances set by the profile “{name}”.",
    "profile_held": "Set by the profile “{name}”.",
    "profile_off_page": "Switch it off in PROFILES.",
    "profile_off_key": "Switch it off in PROFILES or with its key.",
}
FR = {
    "profile_new": "NOUVEAU PROFIL",
    "profile_edit": "MODIFIER LE PROFIL",
    "profile_desc": "Règle en regardant le jeu. ANNULER ou ENREGISTRER rouvre le menu ; Échap le ferme.",
    "profile_name": "NOM DU PROFIL",
    "profile_key": "TOUCHE DU PROFIL",
    "profile_close": "Distance : proche",
    "profile_far": "Distance : loin",
    "profile_word": "Profil",
    "profile_cancel": "ANNULER",
    "profile_save": "ENREGISTRER",
    "name_invalid": "Nom refusé : de 1 à 24 lettres, chiffres, espaces, traits d'union, apostrophes ou tirets bas.",
    "name_taken": "Un autre profil porte déjà ce nom : choisis-en un autre.",
    "key_taken": "Un autre profil a déjà cette touche : choisis-en une autre.",
    "key_command": "Cette touche sert déjà à une commande de caméra (page COMMANDES) : choisis-en une autre.",
    "command_held": "Le profil « {name} » a déjà cette touche : choisis-en une autre, ou change celle du profil dans "
                    "PROFILS.",
    "key_invalid": "Cette touche ne peut pas allumer un profil : choisis-en une autre.",
    "profiles_full": "Tu as déjà 10 profils, le maximum : celui-ci n'est pas enregistré.",
    "profile_unknown": "Ce profil n'existe plus : ferme la fenêtre avec ANNULER.",
    "save_failed": "Le fichier des profils n'a pas pu être écrit : rien n'est enregistré, tes réglages restent dans "
                   "cette fenêtre.",
    "profile_refused": "Ce profil n'a pas pu être enregistré : tes réglages restent dans cette fenêtre.",
    "profiles_desc": "Un seul profil allumé à la fois. Sa touche l'allume ; un second appui revient à tes réglages de "
                     "VUE CAMÉRA et VUE ÉPAULES.",
    "profile_on": "ALLUMÉ",
    "profile_off": "ÉTEINT",
    "profile_modify": "MODIFIER",
    "profile_delete": "SUPPRIMER",
    "profile_values": "FOV {fov} · proche {close} · loin {far} · écart {spacing} · hauteur {height}. "
                      "Manette : {controller}.",
    "profile_no_key": "aucune",
    "toggle_failed": "Le fichier des profils n'a pas pu être écrit : rien n'a changé.",
    "delete_failed": "Le fichier des profils n'a pas pu être écrit : le profil n'est pas supprimé.",
    "profile_delete_title": "SUPPRIMER LE PROFIL",
    "profile_delete_key": "Le profil « {name} » et sa touche seront supprimés.",
    "profile_delete_keys": "Le profil « {name} » et ses touches seront supprimés.",
    "profile_delete_plain": "Le profil « {name} » sera supprimé.",
    "profile_delete_on": "Il est allumé : la caméra reprend tes réglages de VUE CAMÉRA et VUE ÉPAULES.",
    "profile_delete_rest": "Tes autres profils et tes réglages de VUE CAMÉRA et VUE ÉPAULES ne changent pas.",
    "profile_held_camera": "FOV et distances réglés par le profil « {name} ».",
    "profile_held": "Réglé par le profil « {name} ».",
    "profile_off_page": "Éteins-le dans PROFILS.",
    "profile_off_key": "Éteins-le dans PROFILS ou avec sa touche.",
}
# The store's refusals the window names (profile_store.py); any other reads as profile_refused.
REFUSALS = ("name_invalid", "name_taken", "key_taken", "key_invalid", "profiles_full", "profile_unknown")


def text(key, language):
    return (FR if language == "FR" else EN)[key]
