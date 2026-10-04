"""The measured reward allow-list; no missions, all-player calls or SHiFT currency."""
from dataclasses import dataclass

MAX_TARGETS = 10
MAX_PACKAGES = 64
MAX_UNIQUE = 2048
MAX_ITEMS = 8
NAME_PATTERN = r'[A-Za-z0-9_.-]{1,120}'
PREFIX = '[Vehicle Unlocks]'
REWARD_STRUCT = '/Script/GbxGame.GbxRewardsDef'
REWARD_LIBRARY = 'GbxRewards_BlueprintFunctions'
HOST_LIBRARY = 'KismetSystemLibrary'
GIVE_FUNCTION = 'GiveReward'
OPEN_FUNCTION = 'Server_OpenPackage'
GIVE_PARAMETERS = ('RewardDef:GbxDefPtrProperty<GbxRewardsDef>', 'OwnerContext:ObjectProperty<Object>')
OPEN_PARAMETERS = ('PackageIndex:IntProperty',)


@dataclass(frozen=True)
class Target:
    reward: str
    contents: tuple


def vehicle(reward, model):
    return Target(reward, (('GbxRewardData_Unlockable', f'Unlockable_Vehicles.{model}'),))


# Dedicated rewards only: mission rewards contain unrelated loot.
STANDARD = tuple(vehicle(f'Reward_Vehicle_{model}', model) for model in (
    'Borg', 'DarkSiren', 'DarkSiren_Proto', 'ExoSoldier', 'ExoSoldier_Proto',
    'Gravitar', 'Gravitar_Proto', 'Grazer', 'Paladin', 'Paladin_Proto',
))
ACTIONS = {
    'standard': STANDARD,
    # Separate vehicle-only promotions from Banjo's broader bundle (Kevin, 2026-10-04).
    'promotions': (
        vehicle('RewardPackage_CelloVehicle', 'Mountain'),
        vehicle('RewardPackage_MandolinVehicle', 'CityOrder'),
        vehicle('RewardPackage_HarpVehicle', 'ShatterlandV2'),
        vehicle('RewardPackage_ViolaVehicle', 'Stingray'),
    ),
    # Kevin explicitly requested the complete promotional bundle on 2026-10-04.
    'shatterland': (Target('RewardPackage_Banjo', (
        ('GbxRewardData_UnlockableLedger', 'Unlockable_BanjoDLC'),
        ('GbxRewardData_Unlockable', 'Unlockable_Vehicles.ShatterlandV1'),
    )),),
}
