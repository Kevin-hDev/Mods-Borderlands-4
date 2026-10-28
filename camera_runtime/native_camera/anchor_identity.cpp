#include "anchor_contract.h"
#include "ads_identity.h"
#include "ads_memory.h"
#include "ads_mode.h"
#include "ads_sdk_exports.h"
#include "camera_memory.h"
#include <cstring>
namespace climb_anchor {
using apex_ads::read_memory;
bool socket_present(const Session& session) {
    uintptr_t table{}, function{};
    const auto object = session.references[component].address;
    if (!read_memory(object, 0, table)
        || !read_memory(table, socket_exists_slot_offset, function)
        || !apex_camera::executable_in_main_module(reinterpret_cast<void*>(function))) return false;
    using HasSocket = bool (*)(void*, uint64_t);
    __try {
        return reinterpret_cast<HasSocket>(function)(reinterpret_cast<void*>(object), session.socket_name);
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool capture(uintptr_t camera, Session& output) {
    output = {};
    Session candidate{};
    uintptr_t pointers[reference_count]{camera};
    candidate.table = apex_ads::sdk_object_table();
    if (!candidate.table
        || !read_memory(camera, apex_ads::MANAGER_STATE_OFFSET, pointers[state])
        || !read_memory(camera, apex_ads::MANAGER_INPUTS_OFFSET, pointers[inputs])
        || !read_memory(pointers[inputs], apex_ads::INPUTS_CONTROLLER_OFFSET, pointers[controller])
        || !read_memory(pointers[controller], pawn_offset, pointers[actor])
        || !read_memory(pointers[inputs], component_offset, pointers[component])) return false;
    for (size_t i = 0; i < reference_count; ++i)
        if (!apex_ads::capture_id(candidate.table, pointers[i], candidate.references[i])) return false;
    const auto sdk = GetModuleHandleW(apex_ads::sdk_exports::module);
    const auto address = sdk ? GetProcAddress(sdk, apex_ads::sdk_exports::fname_init) : nullptr;
    using Init = void (*)(uint64_t*, const wchar_t*, uint32_t);
    Init initialize{};
    static_assert(sizeof(initialize) == sizeof(address));
    std::memcpy(&initialize, &address, sizeof(initialize));
    if (!initialize) return false;
    initialize(&candidate.mode_name, L"ThirdPersonClimbing", 0);
    initialize(&candidate.socket_name, animated_socket_name, 0);
    if (!candidate.mode_name || !candidate.socket_name || !socket_present(candidate)) return false;
    candidate.thread = GetCurrentThreadId();
    candidate.deadline = GetTickCount64() + duration_ms;
    output = candidate;
    return true;
}
bool current(const Session& session, void* current_state) {
    if (session.thread != GetCurrentThreadId()
        || reinterpret_cast<uintptr_t>(current_state) != session.references[state].address) return false;
    uintptr_t resolved{}, value{};
    for (const auto& reference : session.references)
        if (!apex_ads::resolve_id(session.table, reference, resolved)) return false;
    const auto camera = session.references[manager].address;
    const auto input = session.references[inputs].address;
    const auto pc = session.references[controller].address;
    return read_memory(camera, apex_ads::MANAGER_STATE_OFFSET, value)
        && value == session.references[state].address
        && read_memory(camera, apex_ads::MANAGER_INPUTS_OFFSET, value) && value == input
        && read_memory(session.references[state].address, apex_ads::STATE_INPUTS_OFFSET, value) && value == input
        && read_memory(input, apex_ads::INPUTS_CONTROLLER_OFFSET, value) && value == pc
        && read_memory(input, component_offset, value) && value == session.references[component].address
        && read_memory(pc, apex_ads::CONTROLLER_MANAGER_OFFSET, value) && value == camera
        && read_memory(pc, pawn_offset, value) && value == session.references[actor].address
        && socket_present(session);
}
bool eligible(const Session& session, void* current_state) {
    apex_ads::ModeSnapshot mode{};
    return GetTickCount64() < session.deadline && current(session, current_state)
        && apex_ads::read_mode(reinterpret_cast<void*>(session.references[manager].address),
                               session.mode_name, mode);
}
bool refresh(Session& session) {
    if (!current(session, reinterpret_cast<void*>(session.references[state].address))) return false;
    session.deadline = GetTickCount64() + owner_lease_ms;
    return true;
}
}
