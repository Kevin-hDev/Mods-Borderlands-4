#pragma once
#include "ads_reticle.h"

namespace apex_ads {
using Detour = bool (*)(uintptr_t, void*, void**, const char*, size_t);
struct DetourBindings {
    Detour install{};
    bool (*pin)(void*){};
    uintptr_t module{};
    void* getter{};
    void* producer{};
    bool verified{};
};
class Detours {
public:
    int install(State& state, Reticle& reticle, const DetourBindings& bindings);
private:
    bool attempted_{}, installed_{};
};
}
