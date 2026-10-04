#include "ads_paths.h"
#include <windows.h>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>

#define check(value) do { if (!(value)) { \
    std::cerr << "RESULTAT: ECHEC line=" << __LINE__ << "\n"; std::exit(1); \
} } while (false)

namespace {
alignas(16) unsigned char state[0x70]{}, inputs[0xf0]{}, pc[0x440]{}, weapon[0xd68]{};
alignas(16) unsigned char view_target[0x440]{};
int scale_calls = 0, crosshair_calls = 0;
float returned_scale = 0.75f;
bool returned_crosshair = false;

float scale(void* behavior, void* manager, void* camera_state) {
    check(manager == nullptr && camera_state == state);
    float base{};
    std::memcpy(&base, static_cast<unsigned char*>(behavior) + 0x18, sizeof(base));
    check(base == 1.0f);
    ++scale_calls;
    return returned_scale;
}

bool crosshair(void* held) {
    check(held == weapon);
    ++crosshair_calls;
    return returned_crosshair;
}

apex_ads::Config config() {
    void* input_address = inputs;
    void* controller = pc;
    void* target = view_target;
    std::memcpy(state + 0x28, &input_address, sizeof(input_address));
    // Real CameraModeInputs has distinct ViewTarget and Controller references.
    // Live SDK metadata locates Controller at 0xe8, not the ZoomFOV access at 0xe0.
    std::memcpy(inputs + 0xe0, &target, sizeof(target));
    std::memcpy(inputs + 0xe8, &controller, sizeof(controller));
    return {1, 0, reinterpret_cast<uintptr_t>(state), reinterpret_cast<uintptr_t>(inputs),
            reinterpret_cast<uintptr_t>(pc), reinterpret_cast<uintptr_t>(weapon),
            sizeof(state), sizeof(inputs), sizeof(pc), sizeof(weapon)};
}
}

int main() {
    auto cfg = config();
    unsigned char original_state[sizeof(state)], original_inputs[sizeof(inputs)];
    unsigned char original_pc[sizeof(pc)], original_weapon[sizeof(weapon)];
    std::memcpy(original_state, state, sizeof(state));
    std::memcpy(original_inputs, inputs, sizeof(inputs));
    std::memcpy(original_pc, pc, sizeof(pc));
    std::memcpy(original_weapon, weapon, sizeof(weapon));
    apex_ads::Sample result{};
    check(apex_ads::read_paths(cfg, result, scale, crosshair) == 0);
    check(result.zoom_scale == 0.75f && result.weapon_present == 1);
    check(result.crosshair_requested == 0 && scale_calls == 1 && crosshair_calls == 1);
    check(!std::memcmp(original_state, state, sizeof(state)));
    check(!std::memcmp(original_inputs, inputs, sizeof(inputs)));
    check(!std::memcmp(original_pc, pc, sizeof(pc)));
    check(!std::memcmp(original_weapon, weapon, sizeof(weapon)));
    returned_crosshair = true;
    check(apex_ads::read_paths(cfg, result, scale, crosshair) == 0);
    check(result.crosshair_requested == 1);

    cfg.weapon = cfg.weapon_size = 0;
    check(apex_ads::read_paths(cfg, result, scale, crosshair) == 0);
    check(result.weapon_present == 0 && crosshair_calls == 2);
    cfg = config();
    const auto before = scale_calls;
    cfg.state_size = 0x28;
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    check(scale_calls == before && result.weapon_present == 0);
    cfg = config();
    cfg.inputs_size = 0xe8;
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    check(scale_calls == before);
    cfg = config();
    cfg.controller = reinterpret_cast<uintptr_t>(weapon);
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    check(scale_calls == before);
    cfg = config();
    void* wrong_controller = view_target;
    std::memcpy(inputs + 0xe8, &wrong_controller, sizeof(wrong_controller));
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    check(scale_calls == before);
    cfg = config();
    cfg.abi = 2;
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    cfg = config();
    cfg.reserved = 1;
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    cfg = config();
    cfg.weapon_size = 1;
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    cfg = config();
    cfg.state_size = 1'000'001;
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    cfg = config();
    cfg.state = 1;
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    cfg = config();
    void* invalid_input = weapon;
    std::memcpy(state + 0x28, &invalid_input, sizeof(invalid_input));
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    cfg = config();
    returned_scale = std::numeric_limits<float>::quiet_NaN();
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    check(result.zoom_scale == 0.0f && result.weapon_present == 0);
    returned_scale = 0.0f;
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    returned_scale = 3.0f;
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    auto* inaccessible = VirtualAlloc(nullptr, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_NOACCESS);
    check(inaccessible != nullptr);
    cfg.weapon = reinterpret_cast<uintptr_t>(inaccessible);
    check(apex_ads::read_paths(cfg, result, scale, crosshair) != 0);
    check(VirtualFree(inaccessible, 0, MEM_RELEASE));
    std::cout << "RESULTAT: OK (native reader; no camera or UI writes)\n";
}
