"""Measured Steam contract; only the four vehicle-only DLC rewards are selectable."""
from .config import ACTIONS
from .game_build import CURRENT, IMAGE_SIZE, STEAM_4845623, STEAM_4906557

OWNERS = ('save_editor', 'vehicle_driving')
DLC = dict(zip(('Cello', 'Mandolin', 'Harp', 'Viola'), ACTIONS['promotions']))
FILE = 'vehicle_unlocks.json'
MAX_SETTINGS_BYTES = 1024
SCHEMA = 1
STARTUP_HOOK = '/Script/Engine.AnimInstance:BlueprintUpdateAnimation'
STARTUP_HOOK_ID = 'vehicle_unlocks:catalogue_ready'
STARTUP_TIMEOUT_NS = 120_000_000_000
STARTUP_POLL_NS = 100_000_000
STARTUP_MAX_ATTEMPTS = 1200
FAILURE_CODES = {
    'DLC catalogue startup timeout': 'catalogue_timeout',
    'Startup hook unavailable': 'startup_hook',
    'Invalid promotional selection': 'selection',
    'Settings exceed bound': 'settings_bound',
    'Settings schema differs': 'settings_schema',
    'DLC layout unavailable': 'layout_missing',
    'DLC layout differs': 'layout_changed',
    'Module unavailable': 'module_missing',
    'Unexpected module': 'module_name',
    'Invalid header': 'image_header',
    'Unsupported image': 'image_version',
    'Native DLC contract differs': 'native_contract',
    'Reward type unavailable': 'reward_type',
    'DLC catalogue bound exceeded': 'catalogue_bounds',
    'Duplicate DLC definition': 'duplicate_definition',
    'Promotional definition differs': 'promotion_type',
    'Promotional definitions unavailable': 'promotions_missing',
    'DLC catalogue changed during read': 'catalogue_changed',
    'Original vehicle reward differs': 'reward_reference',
    'Named original links required': 'reward_identity',
    'Protection state changed': 'link_state',
    'Writable data region required': 'page_protection',
    'Reward reference changed before write': 'link_changed',
    'Reference write incomplete': 'write_incomplete',
    'Reference readback differs': 'write_readback',
    'Invalid read': 'read_size',
    'Invalid address': 'read_address',
    'Read refused': 'read_failed',
    'Invalid name index': 'name_index',
    'Unsupported name encoding': 'name_encoding',
}
DLC_STRUCT = '/Script/OakGame.DLCDef'
MAX_DLC = 32
MAX_FIELDS = 48
LINK_SIZE = 24
ARRAY_OFFSET = 0x20
NAME_OFFSET = 56
LINK_OFFSET = 104
FACT_OFFSET = 144
FACT_SIZE = 56
DEFINITION_SIZE = 200
MIN_ADDRESS = 65536
MAX_ADDRESS = 2**47
MAX_REGION = 2**40
MEM_COMMIT = 0x1000
WRITABLE_DATA = (0x04, 0x08)
FIELDS = (('DLCName', 56, 8), ('AutoUnlockReward', 104, 24), ('EntitlementFact', 144, 56))
EXE_NAME = 'Borderlands4.exe'
MAX_MODULE_PATH = 1024
MAX_READ = 16384
MAX_NAME_BLOCKS = 8192
MAX_NAME_LENGTH = 256
# (catalogue cache, name pool, code blocks) per build. 4906557, 2026-10-22: the same functions matched instruction by
# instruction; only call and RIP displacements changed, the two globals come from the moved instructions.
BUILDS = {
    STEAM_4845623: (0xCBC0AE0, 0xC876B00, (
        (0xF82D36, bytes.fromhex('488b35a3ddc30b')),
        (0x120BEF6, bytes.fromhex('e8266ed7ff48c7060000000048637828488b5820')),
        (0x410598E, bytes.fromhex('488b47704885c07511e870eab4fc4889c1e8b09f660048894770488d6f684c8b7f784d85ff0f84c10100004885c0')),
        (0x4105B7A, bytes.fromhex('4885c00f842a03000048837d00000f841f0300004c8bb0b80000')),
        (0x4105C93, bytes.fromhex('807c2438007451')),
        (0x4105E25, bytes.fromhex('4c89e14c89fae8b8170bfd')),
    )),
    STEAM_4906557: (0xCBC8BF0, 0xC87EB00, (
        (0xF7E346, bytes.fromhex('488b35a3a8c40b')),
        (0x1208F44, bytes.fromhex('e8e853d7ff48c7060000000048637828488b5820')),
        (0x410B7D2, bytes.fromhex('488b47704885c07511e87069b4fc4889c1e87cfe660048894770488d6f684c8b7f784d85ff0f84c10100004885c0')),
        (0x410B9BE, bytes.fromhex('4885c00f842a03000048837d00000f841f0300004c8bb0b80000')),
        (0x410BAD7, bytes.fromhex('807c2438007451')),
        (0x410BC69, bytes.fromhex('4c89e14c89fae822650afd')),
    )),
}
CACHE_RVA, NAME_POOL_RVA, BLOCKS = BUILDS[CURRENT]
