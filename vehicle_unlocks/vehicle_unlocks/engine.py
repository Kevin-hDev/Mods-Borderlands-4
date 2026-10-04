"""Normal reflected SDK calls; no memory writes, allocation hacks or package-wide opener."""
from itertools import islice
import re

from . import config as cfg


def label(value):
    if type(value) is not str or re.fullmatch(cfg.NAME_PATTERN, value) is None:
        raise ValueError('Invalid reward name')
    return value


def bounded(values, maximum):
    count = len(values)
    if type(count) is not int or not 0 <= count <= maximum:
        raise ValueError('Reward collection bound exceeded')
    result = tuple(islice(values, maximum + 1))
    if len(result) != count:
        raise ValueError('Reward collection changed')
    return result


def labels(values, maximum):
    return tuple(label(value) for value in bounded(values, maximum))


def parameter(prop):
    result = f'{label(prop.Name)}:{label(prop.Class.Name)}'
    child = getattr(prop, 'Struct', None) or getattr(prop, 'PropertyClass', None)
    return result + (f'<{label(child.Name)}>' if child is not None else '')


def check_function(function, expected):
    count = function.func.NumParams
    fields = tuple(islice(function.func._properties(), len(expected) + 1))
    if (type(count) is not int or count != len(expected) or len(fields) != count
            or tuple(parameter(prop) for prop in fields) != expected or not callable(function)):
        raise ValueError('Reward API changed')
    return function


def validate_definition(reference, target):
    if (not reference._get_address() or label(reference._type.Name) != 'GbxRewardsDef'
            or label(reference._name).casefold() != target.reward.casefold()):
        raise ValueError('Reward identity changed')
    reward = reference.reward
    if reward.bIsUnique is not True or label(reward.UniqueName).casefold() != target.reward.casefold():
        raise ValueError('Reward uniqueness changed')
    items = bounded(reward.rewarddata, cfg.MAX_ITEMS)
    if len(items) != len(target.contents):
        raise ValueError('Reward content changed')
    for item, (kind, name) in zip(items, target.contents):
        if label(item._type.Name) != kind:
            raise ValueError('Reward item type changed')
        key = 'UnlockableLedgerDef' if kind == 'GbxRewardData_UnlockableLedger' else 'UnlockableDef'
        if label(getattr(item, key)._name).casefold() != name.casefold():
            raise ValueError('Reward unlock changed')


class Engine:
    def __init__(self, pc, manager):
        import unrealsdk
        self.sdk, self.pc, self.manager = unrealsdk, pc, manager
        self.struct = unrealsdk.find_object('ScriptStruct', cfg.REWARD_STRUCT)
        library = unrealsdk.find_class(cfg.REWARD_LIBRARY)
        if self.struct is None or library is None:
            raise ValueError('Reward service unavailable')
        self.giver = check_function(getattr(library.ClassDefaultObject, cfg.GIVE_FUNCTION), cfg.GIVE_PARAMETERS)
        self.opener = check_function(getattr(manager, cfg.OPEN_FUNCTION), cfg.OPEN_PARAMETERS)

    def packages(self):
        return bounded(self.manager.packages, cfg.MAX_PACKAGES)

    def snapshot(self):
        unique = labels(self.manager.UniqueRewards, cfg.MAX_UNIQUE)
        pending = tuple(label(row.RewardsDef._name) for row in self.packages())
        return unique, pending

    def write_unique(self, values):
        expected = labels(values, cfg.MAX_UNIQUE)
        self.manager.UniqueRewards = list(expected)
        if labels(self.manager.UniqueRewards, cfg.MAX_UNIQUE) != expected:
            raise RuntimeError('Receipt write not verified')

    def target_package(self, target):
        matches = tuple((i, row) for i, row in enumerate(self.packages())
                        if label(row.RewardsDef._name).casefold() == target.reward.casefold())
        if len(matches) != 1:
            raise ValueError('Target package missing or ambiguous')
        index, package = matches[0]
        validate_definition(package.RewardsDef, target)
        return index

    def validate(self, target):
        self.target_package(target)

    def give(self, target):
        # The Borg trial measured native name resolution from an initially unresolved reference.
        reference = self.sdk.unreal.FGbxDefPtr(target.reward, self.struct)
        if label(reference._name).casefold() != target.reward.casefold():
            raise ValueError('Reward reference changed')
        self.giver(reference, self.pc)

    def open(self, target):
        # Re-find the index after each removal; indices from an earlier package list are stale.
        self.opener(self.target_package(target))
