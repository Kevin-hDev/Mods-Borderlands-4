#pragma once
#include "anchor_pose.h"
#include "generated_ads.h"

namespace climb_anchor {
// Shared authority for the hash-qualified product and its temporary experiment.
constexpr uintptr_t eye_slot_rva = 0xB004228;
constexpr uintptr_t eye_update_rva = 0x3CD3568;
constexpr uintptr_t socket_update_rva = 0x3CD35AA;
constexpr char eye_prefix[] = "498b4028488b5060498950400f284050410f294030";
constexpr char socket_prefix[] = "5657534881ecd00000004c89c64889cf";
constexpr uint64_t duration_ms = 60000;
constexpr uint64_t owner_lease_ms = 1000;
constexpr uintptr_t component_offset = 0xF0;
// The live ThirdPerson inputs have SocketName=None, despite this bone existing.
constexpr wchar_t animated_socket_name[] = L"Camera";
constexpr uintptr_t socket_exists_slot_offset = 0x4C8;
constexpr uintptr_t pawn_offset = 0x3D0;
constexpr size_t reference_count = 6;
enum Reference { manager, state, inputs, controller, actor, component };
struct Statistics {
    uint64_t calls, eligible, applied, refused, expired, active, installed, reserved;
};
struct Session {
    apex_ads::ObjectId references[reference_count]{};
    uintptr_t table{};
    uint64_t mode_name{};
    uint64_t socket_name{};
    uint64_t deadline{};
    unsigned long thread{};
};
bool capture(uintptr_t camera, Session& output);
bool eligible(const Session& session, void* current_state);
bool refresh(Session& session);
}
extern "C" {
__declspec(dllexport) int anchor_verify();
__declspec(dllexport) int anchor_start(uint64_t manager);
__declspec(dllexport) int anchor_stop();
__declspec(dllexport) int anchor_refresh();
__declspec(dllexport) int anchor_stats(climb_anchor::Statistics* output);
}
