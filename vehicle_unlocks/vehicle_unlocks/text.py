"""One English/French text authority for both vehicle pages."""
EN = {
    'vehicles': 'VEHICLES',
    'vehicles:description': 'Unlock vehicles with the game\'s rewards.',
    'vehicles:hint': 'Use these buttons in your own game, on foot. The 4 promotional vehicles require Save Editor or Vehicle Driving to stay enabled, including after restarting the game.',
    'vehicles:standard': 'UNLOCK THE 10 VEHICLES',
    'vehicles:promotions': 'UNLOCK THE 4 PROMOTIONAL VEHICLES',
    'vehicles:shatterland': 'UNLOCK TRIDENT + REWARDS',
    'vehicles:standard:description': 'The 6 regular models and their 4 Proto variants.',
    'vehicles:promotions:description': 'Rocket Luge, Light Gunner, Skank Wagon and Manta.',
    'vehicles:shatterland:description': 'Includes Trident and the other rewards in its promotional bundle.',
    'vehicles:reason:disabled': 'Enable this mod to unlock vehicles.',
    'vehicles:reason:no_game': 'Load a character in your own game.',
    'vehicles:reason:guest': 'Available only in your own game.',
    'vehicles:reason:vehicle': 'Get out of the vehicle and try again on foot.',
    'vehicles:reason:unreadable': 'Vehicle rewards are unavailable. Close and restart the game before trying again.',
    'vehicles:reason:busy': 'An unlock action is already running.',
    'vehicles:reason:restart': 'The previous result could not be confirmed. Close and restart the game before continuing.',
    'vehicles:result:delivered': 'Vehicle rewards delivered: {changed}. Keep Save Editor or Vehicle Driving enabled to retain these promotional vehicles.',
    'vehicles:result:changed': 'Unlocks completed: {changed}. Already received: {skipped}.',
    'vehicles:result:unchanged': 'All rewards for this button have already been received.',
    'vehicles:result:uncertain': 'Confirmed unlocks: {changed}. The rest could not be confirmed. Close and restart the game before continuing.',
}
FR = {
    'vehicles': 'VÉHICULES',
    'vehicles:description': 'Débloque les véhicules avec les récompenses du jeu.',
    'vehicles:hint': 'Utilise ces boutons dans ta propre partie, à pied. Les 4 véhicules promotionnels nécessitent Save Editor ou Vehicle Driving activé, y compris après relance du jeu.',
    'vehicles:standard': 'DÉBLOQUER LES 10 VÉHICULES',
    'vehicles:promotions': 'DÉBLOQUER LES 4 VÉHICULES PROMOTIONNELS',
    'vehicles:shatterland': 'DÉBLOQUER TRIDENT + RÉCOMPENSES',
    'vehicles:standard:description': 'Les 6 modèles classiques et leurs 4 variantes Proto.',
    'vehicles:promotions:description': 'Luge-fusée, Mitrailleur léger, Chariot glauque et Manta.',
    'vehicles:shatterland:description': 'Comprend Trident et les autres récompenses de son paquet promotionnel.',
    'vehicles:reason:disabled': 'Active ce mod pour débloquer les véhicules.',
    'vehicles:reason:no_game': 'Charge un personnage dans ta propre partie.',
    'vehicles:reason:guest': 'Disponible seulement dans ta propre partie.',
    'vehicles:reason:vehicle': 'Descends du véhicule puis réessaie à pied.',
    'vehicles:reason:unreadable': 'Les récompenses de véhicules sont indisponibles. Ferme et relance le jeu avant de réessayer.',
    'vehicles:reason:busy': 'Un déblocage est déjà en cours.',
    'vehicles:reason:restart': 'Le résultat précédent n’a pas pu être confirmé. Ferme et relance le jeu avant de continuer.',
    'vehicles:result:delivered': 'Récompenses de véhicules attribuées : {changed}. Garde Save Editor ou Vehicle Driving activé pour conserver ces véhicules promotionnels.',
    'vehicles:result:changed': 'Déblocages effectués : {changed}. Déjà reçus : {skipped}.',
    'vehicles:result:unchanged': 'Toutes les récompenses de ce bouton ont déjà été reçues.',
    'vehicles:result:uncertain': 'Déblocages confirmés : {changed}. Le reste n’a pas pu être confirmé. Ferme et relance le jeu avant de continuer.',
}


def get(key, language):
    return (FR if language == 'FR' else EN)[key]
