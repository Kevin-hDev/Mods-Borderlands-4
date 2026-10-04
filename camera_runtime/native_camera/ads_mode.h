#pragma once
#include "generated_ads.h"

namespace apex_ads {
struct ModeSnapshot {
    uint64_t name{};
    uintptr_t object{};
    bool stable{};
};
// The SDK supplies the interned ThirdPerson FName once, not a prior frame's mode.
bool read_mode(void* manager, uint64_t third_person_name, ModeSnapshot& output);
}
