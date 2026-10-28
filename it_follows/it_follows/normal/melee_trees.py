"""The armed bandits' decision trees whose blow timer the normal mode shortens (decision 126): each tree's path,
its nodes in order, the index of its blow's Timer and the rest after success the game gives it (centre, half
width).

Copied once from the enemy research's contract (apex_probe/apex_pursuit_wide_contract.json, séance 35, vérifié en
jeu), the blow's Timer by Key.SomeStructs of the decoded trees (source unique); every rest read in game at trial 66
as written here. The sniper's tree is left out: the game refused its reading at séance 35 and at
trial 66."""


class Tree:
    def __init__(self, path: str, nodes: tuple[str, ...], timer: int, rest: tuple[float, float]) -> None:
        self.path, self.nodes, self.timer, self.rest = path, nodes, timer, rest


TREES = {
    "AITree_GunToterSMG": Tree(
        "/Game/AI/ArmyBandit/GunToter/SMG/_Design/Character/AITree_GunToterSMG.AITree_GunToterSMG",
        ("Root", "ThrowGrenadeFromPosition", "Timer", "Ticket", "CoverAttack", "Is In Range", "CloseMelee", "Timer",
        "MeleeAttackCanApproach", "Is In Range", "Timer", "NormalActions", "Stance", "Tagged_Enraged",
        "WeaponAttack_v2", "Stance", "Timer", "Condition", "Condition", "Condition", "DialogEvent"),
        7, (6.0, 2.0)),
    "AITree_GunToterAssault": Tree(
        "/Game/AI/ArmyBandit/GunToter/Assault/_Design/Character/AITree_GunToterAssault.AITree_GunToterAssault",
        ("Root", "CoverAttack", "ThrowGrenadeFromPosition", "Timer", "Ticket", "CloseMelee", "Timer", "Stance",
        "Tagged_Enraged", "Is In Range", "WeaponAttack_v2", "Condition", "Timer", "Condition"),
        6, (6.0, 2.0)),
    "AITree_GunToterBadass": Tree(
        "/Game/AI/ArmyBandit/GunToter/Badass/_Design/Character/AITree_GunToterBadass.AITree_GunToterBadass",
        ("Root", "MeleeAttack", "ThrowGrenade", "Timer", "Ticket", "Is In Range", "Timer", "Priority", "Tagged_Enraged",
        "WeaponAttack_v2", "CoverAttack", "Timer", "DialogEvent", "DialogEvent", "DialogEvent", "ThrowTurret", "Timer",
        "MaxChildActors", "DialogEvent", "Ticket", "Trick", "Timer", "Ticket", "MaxChildActors", "Event", "Priority_0",
        "Condition", "Condition", "Event"),
        6, (6.0, 2.0)),
    "AITree_GunToterHeavy": Tree(
        "/Game/AI/ArmyBandit/GunToter/Heavy/_Design/Character/AITree_GunToterHeavy.AITree_GunToterHeavy",
        ("Root", "MeleeAttack", "ThrowGrenade", "Timer", "Ticket", "Is In Range", "Timer", "Priority", "Stance",
        "Tagged_Enraged", "WeaponAttack_v2"),
        6, (6.0, 2.0)),
    "AITree_GunToterShotgun": Tree(
        "/Game/AI/ArmyBandit/GunToter/Shotgun/_Design/Character/AITree_GunToterShotgun.AITree_GunToterShotgun",
        ("Root", "CloseMelee", "ThrowGrenadeFromPosition", "Timer", "Timer", "IsInRange", "AdvanceToCombatDistance",
        "NavGps", "FlankABit", "Timer", "UseWeapon", "Ticket", "IsInRange", "IsInRange", "Timer", "EnragedThrowMirv",
        "HasSkill", "Timer", "Ticket", "IsInRange", "GrenadeThrow", "HasSkill", "Ticket", "IsInTerritory", "Ticket",
        "RandomOrbit", "FlankNoShoot", "Timer", "IsInRange", "Ticket", "Advancing", "AdvanceToCombatDistance_NoShoot",
        "IsInTerritory", "NavGps", "IsInRange", "Timer", "WeaponAttack_v2", "DialogEvent", "Stance", "Stance", "Stance",
        "Stance", "Stance", "Timer", "IsInRange"),
        4, (6.0, 2.0)),
    "AITree_GunToterSmall": Tree(
        "/Game/AI/ArmyBandit/GunToter/Small/_Design/Character/AITree_GunToterSmall.AITree_GunToterSmall",
        ("Root", "CloseMeleeAttack", "Is In Range", "Timer", "Priority", "Orbit", "UseWeapon", "Timer", "Stance",
        "Stance", "Tagged_Enraged", "WeaponAttack_v2", "Stance", "Condition", "RangedAttack", "IsInRange", "Ticket",
        "Timer"),
        3, (6.0, 2.0)),
    "AITree_GunToterPistol": Tree(
        "/Game/AI/ArmyBandit/GunToter/Pistol/_Design/Character/AITree_GunToterPistol.AITree_GunToterPistol",
        ("Root", "MeleeAttack", "ThrowGrenadeFromPosition", "Timer", "Ticket", "Is In Range", "Timer", "CoverAttack",
        "NormalActions", "Is In Range", "Stance", "Tagged_Enraged", "WeaponAttack_v2", "Stance", "Condition",
        "Condition", "Timer"),
        6, (8.0, 2.0)),
}
