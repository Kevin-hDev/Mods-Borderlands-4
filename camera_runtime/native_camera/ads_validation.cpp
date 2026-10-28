#include "ads_state.h"
#include "ads_identity.h"
#include "ads_memory.h"
#include "interaction_alignment.h"
#include <initializer_list>

namespace apex_ads {
uint32_t owner_error(uintptr_t table, const AdsContext& context) {
    uintptr_t resolved{};
    for (size_t index : {size_t{0}, size_t{1}, size_t{2}, size_t{5}}) {
        if (!resolve_id(table, context.references[index], resolved)) return static_cast<uint32_t>(ERROR_IDENTITY);
    }
    uintptr_t value{};
    const bool related = read_memory(context.references[0].address, apex_interaction::pawn_offset, value)
        && value == context.references[1].address
        && read_memory(context.references[0].address, CONTROLLER_MANAGER_OFFSET, value)
        && value == context.references[2].address
        && read_memory(context.references[5].address, OBJECT_OUTER_OFFSET, value)
        && value == context.references[1].address;
    // Registry expiry and changed relations require the same refusal, but explain different causes.
    return related ? 0U : static_cast<uint32_t>(ERROR_CONTEXT);
}

bool owner_alive(uintptr_t table, const AdsContext& context) {
    return owner_error(table, context) == 0;
}

uint32_t context_error(uintptr_t table, const AdsContext& context) {
    if (context.abi != ADS_ABI || context.size != sizeof(context) || context.enabled != 1
            || context.reserved || !context.generation || context.generation == UINT64_MAX)
        return static_cast<uint32_t>(ERROR_CONTEXT);
    const auto ownership = owner_error(table, context);
    if (ownership) return ownership;
    uintptr_t pointers[8]{};
    for (size_t i = 0; i < 8; ++i) {
        if (!resolve_id(table, context.references[i], pointers[i])) return static_cast<uint32_t>(ERROR_IDENTITY);
    }
    const auto& paths = context.paths;
    if (paths.abi != ADS_ABI || paths.reserved || paths.controller != pointers[0]
            || paths.weapon != pointers[3] || paths.state != pointers[6] || paths.inputs != pointers[7]
            || paths.state_size < STATE_MIN_SIZE || paths.inputs_size < INPUTS_MIN_SIZE
            || paths.controller_size < CONTROLLER_MIN_SIZE || paths.weapon_size < WEAPON_MIN_SIZE
            || paths.state_size > MAX_TYPE_BYTES || paths.inputs_size > MAX_TYPE_BYTES
            || paths.controller_size > MAX_TYPE_BYTES || paths.weapon_size > MAX_TYPE_BYTES)
        return static_cast<uint32_t>(ERROR_CONTEXT);
    uintptr_t link{}, value{};
    if (!read_memory(pointers[1], ACTOR_CONTROLLER_LINK_OFFSET, link)
            || !read_memory(link, ACTOR_LINK_CONTROLLER_OFFSET, value) || value != pointers[0]
            || !read_memory(pointers[0], CONTROLLER_MANAGER_OFFSET, value) || value != pointers[2]
            || !read_memory(pointers[2], MANAGER_STATE_OFFSET, value) || value != pointers[6]
            || !read_memory(pointers[2], MANAGER_INPUTS_OFFSET, value) || value != pointers[7]
            || !read_memory(pointers[4], ANIMATION_WEAPON_OFFSET, value) || value != pointers[3]
            || !read_memory(pointers[5], OBJECT_OUTER_OFFSET, value) || value != pointers[1]
            || !read_memory(pointers[6], STATE_INPUTS_OFFSET, value) || value != pointers[7]
            || !read_memory(pointers[7], INPUTS_CONTROLLER_OFFSET, value) || value != pointers[0])
        return static_cast<uint32_t>(ERROR_CONTEXT);
    uint8_t category{};
    // The weapons this view can present; ads_policy.py alone decides which of them the player gets at the shoulder.
    // Heavy weapons since every weapon type has its optic row (2026-10-10): trial 1 found them refused here.
    const bool supported = read_memory(pointers[4], ANIMATION_CATEGORY_OFFSET, category)
        && (category == CATEGORY_PISTOL || category == CATEGORY_SMG || category == CATEGORY_SHOTGUN
            || category == CATEGORY_ASSAULT || category == CATEGORY_SNIPER || category == CATEGORY_HEAVY);
    return supported ? 0U : static_cast<uint32_t>(ERROR_CONTEXT);
}
}
