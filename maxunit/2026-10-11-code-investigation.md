# Epic compatibility: source-level findings and proposed changes

Follow-up to the [initial report](https://github.com/Kevin-hDev/Mods-Borderlands-4/blob/2707dbd345642c66951299390652c38304742e9d/maxunit/README.md), for **BL4ThirdPersonPOC 0.3.8.17**.
Prepared on 11 October 2026 after three parallel investigations and a coordinating
review. **No mod source, game memory, installed package, or settings were changed.**

This is an implementation advisory, not a tested patch. File/line references below
refer to the Python files in your original package, not a newer GitHub revision.
We did not establish replacement Epic addresses for your native patches in this pass.

## 1. Main result: three different kinds of failure

1. **Build guards:** several components explicitly accept the measured Steam
   executable and reject the measured Epic executable before inspecting their sites.
2. **Code guards:** prompt, item-card and reticle checks actually reach fixed
   addresses and reject the bytes/hash found there. Changing a build allowlist
   alone will not fix these.
3. **Dependencies:** some components are unavailable because an upstream component
   failed. These must not be counted as independent proven bad addresses.

The visible third-person camera and SDK-driven zoom can work while these paths
are unavailable. Keep their existing separation; do not treat camera visibility
as evidence that native targeting or recoil initialized.

### Executable identity measured from disk

Both PE headers and whole-file SHA256 were read again during this investigation.

| Installed executable | TimeDateStamp | SizeOfImage | Machine |
|---|---|---|---|
| Steam | `0x6AA81051` | `0x31B8C000` | `0x8664` |
| Epic | `0x6AA810B3` | `0x2E928000` | `0x8664` |

- Steam SHA256: `9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.
- Epic SHA256: `764a4bb5403a2619a0be627de5a738e23ea021e8672f7f0e7a536697d4a06719`.

The Epic tuple is exactly the decimal tuple in the FFYL log. The Steam tuple is
exactly `EXPECTED` in `native_recoil.py:24` and the tuple checked by several other
modules. This resolves the identity question for these two files only: it does
not validate Epic structures, patches, or all future builds from either store.

## 2. Recommended common change: per-build, per-feature contracts

Move build-dependent values to one reviewed profile source, then pass the relevant
contract to each component. A profile must cover more than an executable tuple:

- Function/site RVAs, original bytes, hash windows, continuation targets.
- Structure offsets, sizes, field masks, vtable slots and type anchors.
- The register/stack assumptions of generated native stubs, including offsets
  embedded inside their machine-code bytes.
- A separate availability result for each feature and dependency.

**Recognized executable is not the same as supported feature.** Record Epic as
identified, but leave each feature unavailable until its entire contract is
reviewed. Do not clone the Steam profile and change its timestamp. An unknown
profile must refuse activation before site reads, allocations or writes.

Use reflected SDK fields where they actually exist and cross-check native pointers
against their SDK counterparts. Non-reflected stack/runtime layouts still need
independent validation. Retain weak-reference, serial, local-player and snapshot
consistency checks on every relevant lifetime transition.

Your existing floor-pickup AOB fallback is a useful example of *resolution*: it
finds `0xB48D3E` on this Epic build. It is not proof that another site's ABI or
trampoline is safe. Require a unique candidate, instruction-level comparison and
validated structure assumptions before turning a candidate into an approved site.

Do not apply a global Steam-to-Epic address delta. Relative branches/RIP-relative
operands may change even when a function's purpose is unchanged; compare decoded
instructions, then record exact build-specific bytes and targets.

## 3. Prompt, item cards, NPCs and Placeable targeting

### What fails, and what remains untested

| Component | First refusal reached | Next checks that still matter |
|---|---|---|
| Item-card Gate-2 | Prefix at `0x03E5604C`; `item_card_runtime.py:376–393`, log 145 | Continuation, register/stack contract, final selector at `0x03E56206` |
| Prompt | Prefix at `0x03E542B5`; `interaction_runtime.py:313–333`, log 146 | Safety window, normal/alternate origins, ray and yaw fields in the stub |
| NPC | Prompt not ready; `interaction_runtime.py:121–130`, log 148 | Then its own Steam timestamp guard at lines 138–150, candidate site and continuation |
| Placeable | Steam tuple; `placeable_targeting.py:76–89`, log 147 | Bounds site, rejection continuation, owned prompt patch, provider/getter/vtable |

NPC's later timestamp refusal was reproduced with a simulated ready prompt. It
was **not reached in the game log**. Likewise, Placeable's log does not prove its
patch bytes are wrong: the build guard stopped it before those reads.

Installation order is in `game_hooks.py:2754–2757`: item cards, prompt, Placeable,
NPC. Item-card setup and prompt setup have separate failure paths. In gameplay,
however, the prompt stub also changes yaw used by native item-card selection
(`native_memory.py:417–465`), so test them together after individual qualification.

### Proposed dependency handling

This example uses methods already called by `game_hooks.py`. It is a suggested
replacement for its prompt/dependent install block, **not an Epic compatibility
fix by itself**. Item-card setup remains separate. This suppresses installation
attempts, not cleanup of any previously retained owner.

```python
# Proposed block inside game_hooks, where these names already exist.
owner_module._install_interaction_prompt_targeting()
prompt = owner_module._interaction_prompt_state
if isinstance(prompt, dict) and prompt.get("ready"):
    placeable_targeting.install(owner_module)
    owner_module._install_npc_eligible()
else:
    owner_module.logging.warning(
        "[BL4ThirdPersonPOC] Placeable/NPC targeting unavailable: "
        "native prompt not ready"
    )
```

Retain each dependent's own validation. A ready prompt does not establish the NPC
or Placeable layout. Report `blocked_by_prompt` separately from `unsupported_build`.

### Validate a selected site before allocation

The following proposed helper uses existing wrappers exposed by `__init__.py`:
`_native_image_size`, `_native_require_executable` and `_native_read`. It is an
additional preflight for a **previously approved profile**, not a signature finder
or substitute for ABI review. Run only on a fresh/unowned site; an existing hook
must be handled through its ownership/restore path, never overwritten.

```python
def validate_selected_gate2_site(mod, module_base):
    """Read-only preflight; do not allocate or install a hook here."""
    rva = mod.ITEM_CARD_GATE2_TARGET_RVA
    prefix = mod.ITEM_CARD_GATE2_TARGET_PREFIX
    continuation = mod.ITEM_CARD_GATE2_CONTINUATION_PREFIX
    if type(module_base) is not int or not 0x10000 <= module_base < 2**63:
        raise RuntimeError("Invalid module base")
    if (type(rva) is not int or type(prefix) is not bytes
            or type(continuation) is not bytes
            or not 1 <= len(prefix) <= 64
            or not 1 <= len(continuation) <= 64
            or len(prefix) != mod.ITEM_CARD_GATE2_HOOK_LENGTH):
        raise RuntimeError("Invalid Gate-2 profile")
    image_size = mod._native_image_size(module_base)
    size = len(prefix) + len(continuation)
    if (type(image_size) is not int or not 0 < image_size <= 2**32
            or rva < 0 or rva + size > image_size
            or module_base + image_size >= 2**63):
        raise RuntimeError("Gate-2 site outside image")
    target = module_base + rva
    mod._native_require_executable(target, "Gate-2")
    if mod._native_read(target, size) != prefix + continuation:
        raise RuntimeError("Gate-2 site validation failed")
    return target
```

There are two item-card sites, not one: Gate-2 replaces 16 bytes; the final selector
replaces 19. Both continuations need validation. Placeable additionally checks a
49-byte bounds window, the reject continuation, provider getter and vtable
(`placeable_targeting.py:90–107`). NPC embeds a candidate offset and branch targets.

**Critical implementation constraint:** `_native_build_trampoline` in
`native_memory.py:212–221` copies instructions; it is not a general relocating
disassembler. Finding matching bytes does not make an arbitrary detour safe.
Re-audit whole instructions, relative branches, register meanings and stack fields
for each site, and rebuild the stub when those contracts differ.

## 4. FFYL, GroundSlam and CharacterCamera

### FFYL

The first failure occurs in `native_memory.py:929–935`, called by
`_ffyl_camera_stack_has_single_tps`, then `ffyl_strategy_selection.verify_selection`.
The code refuses the build **before** reading the stack window at manager `+0x39A8`.

After a reviewed Epic stack layout is supplied, these additional guards remain:

- `ffyl_strategy_selection.py:15–28,70–82`: exact RVAs/prefixes for
  `PushActorCameraMode`, `PushActorCameraModeDef`, `GetActorCameraMode`; native
  function pointer metadata read at `UFunction+0xD8`.
- Stack entry count/capacity bounded to 64, stable repeated snapshots and matching
  mode names (`native_memory.py:940–964`).
- Reflected `OnDowned` / `OnDownedEnded` signatures, including field offsets/types.
- `ffyl_entry_blend.py:8–51`: another build guard and three native anchors;
  compensation subsequently uses runtime fields `+0xA70/+0xA74`.
- Independent recoil ownership and validation, also called directly from the
  FFYL owner. Supporting the general camera does not automatically support FFYL.

Keep the order: validate contract and local lifetime, then create the owner and
register events. Never interpret an unreadable stack as empty or authorize a pop
after failed verification. The current log shows startup failures, not proof that
the player entered and exited an actual FFYL cycle during this recording.

### GroundSlam

`ground_slam_camera.py:585–595` expects the measured Steam tuple and rejects the
observed Epic tuple. The log's
`reason=setup_failed`, `applies=0`, `restores=0`, `cleanup_complete=True` describes
this setup failure; “restoration details” does not establish another cleanup bug.

Port the complete contracts for InitialRotation, transition, runtime apply and
GetPOV. These include code hashes/prefixes, `CameraModeState` native/SDK pointer
agreement, reflected `CameraModeDef` size/masks, runtime/control pairs, socket
behavior schema and two vtable references. See lines 596–644, 667–710, 754–775,
1206–1226. Offsets also live inside generated stubs: changing Python RVAs alone
does not update those machine-code operands.

Preserve `camera_hook_chain.original_read(mod, address, size)`: it verifies owned
detours before reconstructing the original instruction window. Replacing it with
a raw read can misidentify the mod's own existing hook as a build mismatch.
Continue using `chain.allocate`, `verify`, `restore`, `retire`; do not introduce
a second independent owner for the same camera entry.

The existing module itself reports `collision_unverified=True` when armed. Do not
upgrade that claim merely because Epic initialization eventually succeeds.

### CharacterCamera

`npc_camera_visibility.py:343–356` rejects the build before validating three code
windows (lines 357–375) or installing patches. Log 205 reports zero native patches
and completed cleanup. Its `RESTORE_DETAILS` message repeats the setup error.

Qualify the camera/filter code windows, runtime producer-list layout, unique
producer selection and its vtable update slot (`:377–438`), plus embedded stub
stack assumptions. Keep filtering scoped to the owned producer, thread and query;
do not turn an NPC visibility fix into broad world-collision removal.

A small lifecycle improvement is to publish `_ffyl_camera_ignore_provider` only
after successful preflight. It is currently published at lines 339–340, before
the build check, then removed by cleanup at 197–202. Cleanup succeeded in this log;
this is a proposed reduction of transient state, not an observed leaked hook.

## 5. Recoil, reticle and ADS zoom are separate compatibility paths

### Recoil and repeated attempts

`native_recoil.py:351` rejects the build; its error report makes
`native_lifecycle.py:1223–1225` abort activation. Later reflection, Look/WeaponLook
vtable checks, function hashes and ownership checks are not reached by this attempt.

There is already deduplication by `(pawn, camera, weapon)` at
`native_lifecycle.py:825–832`. **The failed-activation cleanup explicitly preserves
it at lines 1153–1154.** Do not “fix” a reset that does not happen there.

Other transitions reset it, including Beam stop, equipment callbacks and ordinary
camera stops. `ads_events.py:461,505` resets it before local-event checks. A new
weapon also changes the identity. The log records 25 failed activations; it does
not prove a retry on every frame or identify the trigger of every retry.

Proposed change: retain a bounded per-feature incompatibility result for the
current executable/session, separate from gameplay identity and `_native_fault`.
The latter protects uncertain restoration and must keep its existing meaning.
Move equipment-triggered rearming behind a proven relevant local event without
removing cleanup that a real ownership transition needs.

Conceptual flow only; these status names are proposed, not existing APIs:

```text
service retained owners and pending cleanup first
if cleanup is uncertain: do not arm anything
if recoil contract is rejected for this process/build: skip activation
if runtime is temporarily unavailable: wait for a relevant local transition
otherwise: run the current guarded recoil activation
```

Apply the same capability check to ordinary and FFYL activation paths. Do not
return early from the whole ownership update before its cleanup work. No timed
retry will make an incompatible executable become compatible inside the process.

### Reticle: newly identified exact refusal

The initial report left this cause open. Log **381** resolves it:

```text
[BL4ThirdPersonPOC] TPS_RETICLE_PUBLISH_DISABLED error=RuntimeError: Native anchor mismatch 0x3aedfe
```

`_reticle_publish.py:68–88` rejects the first of three anchor hashes, RVA
`0x3AEDFE`, 401 bytes. This happens before model lookup or publication. Then
`__init__.py:1525,1552` retains the fault; later event results reuse it. This is
separate from recoil, not an established consequence of recoil failure.

The publisher sets the model's visibility byte/counter (`model+0x88/+0x8C`), not
the grenade trajectory. Port all its anchors, global/type references, assignment
window and model/weapon ownership checks together. Do not force its visibility
write past a rejected anchor or infer that it causes the throw offset screenshot.

### ADS zoom handoff: additional logged refusal

Log **458**, `ads_zoom_modifiers.py:280`:

```text
[BL4ThirdPersonPOC.ADSZoom] HANDOFF_REFUSED RuntimeError: Game build differs
```

`_initialize` expects the measured Steam tuple and rejects the Epic tuple at lines
62–77, before `CODE_GUARDS` and the
native entry call are prepared. Include this feature in the profile inventory.
Completed visual zoom transitions do not prove that the native modifier handoff
succeeded. The exact visible consequence of this refusal remains untested.

## 6. Throws: an integration proposal, not a storefront fix

No dedicated trajectory/eyes-viewpoint correction was found in this package.
`camera_math.py:37` reads `GetActorEyesViewPoint` for geometry; `game_hooks.py:264`
uses that reference for NPC line-of-sight. `throwable_bypasses` in
`camera_events.py:1466` distinguishes input routes; it is not throw convergence.

The [initial report](https://github.com/Kevin-hDev/Mods-Borderlands-4/blob/2707dbd345642c66951299390652c38304742e9d/maxunit/README.md#reference-approach-from-our-camera-implementation)
contains our measured approach and source links: adjust the logical eyes viewpoint
onto the final camera ray, preserving longitudinal depth, instead of rotating the
controller or moving the camera during each throw.

For your architecture, implement a separately validated **native eyes owner**,
coordinated with your existing lifecycle. Use your final camera cache and identity
rules. Our `read_camera` depends on our DLL exports `view_stats`/`view_game_build`
and suspension flags; it is **not a drop-in dependency for your mod**. No Python
callback should be added inside an arbitrary native-thread viewpoint call.

Before changing the eyes result, confirm this cause in your build with passive
measurements of camera, original eyes, controller direction and projectile path.
Then explicitly test these interactions:

- Your prompt patch already redirects its native ray/yaw toward a selected target.
  Changing its upstream eyes reference may duplicate or alter that correction.
- NPC line-of-sight currently reads the eyes. Changing it may change occlusion
  eligibility, not merely screen alignment.
- Beam has its own origin producer and rear-blocker/collision filters. An eyes
  correction does not automatically replace that system. Preserve its existing
  restoration dependency order and test both paths together.
- ADS/FPS, vehicle, ladder, FFYL, respawn and possession must select which owner
  is permitted to supply the viewpoint; stale identities retain the original answer.

Treat native compatibility, reticle visibility and throw alignment as three
separate work items. Do not attribute all three to one rejected build check.

## 7. Suggested implementation and validation order

1. Add read-only contract identification and per-feature diagnostics. Distinguish
   unknown build, rejected code, unverified layout, missing dependency and temporary
   gameplay state. Preserve restoration faults as a separate blocking category.
2. Establish each Epic function/layout offline and cross-check reflected fields
   in a read-only game session. Store reviewed contracts centrally; keep incomplete
   features disabled. Record hashes of the binaries the results apply to.
3. Port prompt and its dependents, then both item-card sites. Test their combined
   behavior after individual preflights pass.
4. Qualify recoil, reticle and ADS zoom separately. Then qualify the FFYL/slam/
   CharacterCamera contracts and all of their direct recoil dependencies.
5. Investigate throw alignment independently, then integrate an eyes owner only
   after confirming its geometry and coexistence with prompt/Beam corrections.

For each stage, use both the qualified Steam and Epic builds. Tests must include:

| Area | Minimum checks |
|---|---|
| Refusal | Unknown build, wrong prefix/hash, missing/ambiguous signature; no patch allocation/write |
| Lifetime | Changed pawn/manager/weapon, stale weak reference, changed snapshot, disable/re-enable, map load |
| Ownership | Foreign bytes, partial install, failed restore; retain reachable allocations and report failure |
| Interactions | Overlapping loot, both shoulders, near/far; NPC in/out of range and behind obstacles; Placeable candidates |
| Camera states | FFYL entry/Second Wind/death, ground slam, wall proximity, vehicles and ladders |
| Aim | ADS entry/exit and weapon handoff, ordinary weapons/Beam, both shoulders, dynamic camera |
| Throws | Same knife/grenade, FPS/TPS, near/far, obstacle between camera and character, comparison of actual impacts |

Initialization success alone is not the acceptance criterion. Verify cleanup and
visible behavior, and keep untested cases explicitly unverified.

## 8. Checks performed for this advisory

- Inspected source paths above and the original 582-line log snapshot.
- Measured both local executable identities/hashes; no binary modification.
- Reproduced five original refusal/dependency cases with AST-isolated functions
  and fake owners/readers: Gate-2 mismatch, prompt mismatch, missing prompt for NPC,
  Epic NPC timestamp with simulated ready prompt, Epic Placeable tuple. All passed.
- Independently exercised the original FFYL stack guard with three fake PE inputs:
  Steam accepted through an empty simulated stack; Epic and an unknown tuple
  rejected before any layout read. All passed.
- Checked the two Python examples above without importing the game/SDK: syntax
  and 13 isolated dependency/site acceptance and rejection cases, all passing.
- Compared all 61 extracted package files against their archive entries: identical.

These checks validate the diagnosis and isolated example logic. They do **not**
validate a new Epic profile, native stub, installed patch or in-game correction.
The examples are advisory; no fixed mod or replacement package is being delivered.
