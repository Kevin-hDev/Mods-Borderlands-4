"""One English/French/Chinese text authority for both vehicle pages."""
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
# Vehicle names stay in English: no official Chinese name was found for them (2026-10-13).
ZH = {
    'vehicles': '载具',
    'vehicles:description': '用游戏自带的奖励解锁载具。',
    'vehicles:hint': '请在你自己的游戏中、步行时使用这些按钮。4 辆活动载具需要保持 Save Editor 或 Vehicle Driving '
                     '启用，重启游戏后也一样。',
    'vehicles:standard': '解锁 10 辆载具',
    'vehicles:promotions': '解锁 4 辆活动载具',
    'vehicles:shatterland': '解锁 Trident 及奖励',
    'vehicles:standard:description': '6 款常规型号及其 4 款 Proto 变体。',
    'vehicles:promotions:description': 'Rocket Luge、Light Gunner、Skank Wagon 和 Manta。',
    'vehicles:shatterland:description': '包含 Trident 及其活动礼包中的其他奖励。',
    'vehicles:reason:disabled': '请先启用此模组再解锁载具。',
    'vehicles:reason:no_game': '请在你自己的游戏中载入一个角色。',
    'vehicles:reason:guest': '仅在你自己的游戏中可用。',
    'vehicles:reason:vehicle': '请离开载具，步行时再试一次。',
    'vehicles:reason:unreadable': '载具奖励不可用。请关闭并重启游戏后再试。',
    'vehicles:reason:busy': '已有一项解锁正在进行。',
    'vehicles:reason:restart': '无法确认上一次的结果。请关闭并重启游戏后再继续。',
    'vehicles:result:delivered': '已发放载具奖励：{changed}。请保持 Save Editor 或 Vehicle Driving 启用，以保留这些活动载具。',
    'vehicles:result:changed': '已完成解锁：{changed}。之前已获得：{skipped}。',
    'vehicles:result:unchanged': '此按钮的所有奖励都已获得。',
    'vehicles:result:uncertain': '已确认的解锁：{changed}。其余的无法确认。请关闭并重启游戏后再继续。',
}


def get(key, language):
    table = {'FR': FR, 'ZH': ZH}.get(language, EN)
    return table.get(key, EN[key])
