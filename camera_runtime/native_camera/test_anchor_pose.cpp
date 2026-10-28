#include "anchor_pose.h"
#include <array>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <limits>

namespace {
using Buffer = std::array<unsigned char, climb_anchor::state_bytes>;
int failures = 0;
double candidate[3] = {100.0, 200.0, 300.0};
void check(bool value, const char* message) {
    if (!value) { ++failures; std::printf("FAIL: %s\n", message); }
}
void native_socket(void* behavior, void* context, void* state, float delta) {
    auto* bytes = static_cast<unsigned char*>(behavior);
    check(context == reinterpret_cast<void*>(0x10000), "forward native context");
    check(delta == 0.01f, "forward native delta");
    check(bytes[climb_anchor::flags_offset] == 1, "location only, never animation rotation");
    uint64_t socket_name{};
    std::memcpy(&socket_name, bytes + 0x1c, sizeof(socket_name));
    check(socket_name == 27, "explicit animated bone survives an empty native default");
    std::memcpy(static_cast<unsigned char*>(state) + climb_anchor::position_offset,
                candidate, sizeof(candidate));
    // A native function cannot commit unrelated output from the trial buffer.
    static_cast<unsigned char*>(state)[0x48] = 99;
}
Buffer state() {
    Buffer result{};
    result[0x48] = 17;
    const double eye[3] = {216.93, 330.20, 523.19};
    std::memcpy(result.data() + climb_anchor::position_offset, eye, sizeof(eye));
    return result;
}
}

int main() {
    auto value = state();
    check(climb_anchor::apply_socket(native_socket, reinterpret_cast<void*>(0x10000),
                                    value.data(), 0.01f, 27), "animated anchor accepted");
    double actual[3]{};
    std::memcpy(actual, value.data() + climb_anchor::position_offset, sizeof(actual));
    check(actual[0] == 100 && actual[1] == 200 && actual[2] == 300,
          "native animated anchor replaces early physical teleport");
    check(value[0x48] == 17, "native camera rotation remains unchanged");
    for (double invalid : {std::numeric_limits<double>::quiet_NaN(), 1e10, 2000.0}) {
        value = state(); const auto before = value; candidate[0] = invalid;
        check(!climb_anchor::apply_socket(native_socket, reinterpret_cast<void*>(0x10000),
                                         value.data(), 0.01f, 27), "invalid socket refused");
        check(value == before, "refusal leaves native state untouched");
    }
    check(!climb_anchor::apply_socket(nullptr, nullptr, nullptr, 0, 27), "missing reader refused");
    check(!climb_anchor::apply_socket(native_socket, nullptr, value.data(), 0.01f, 0),
          "empty explicit bone refused instead of falling back to eyes");
    std::printf("RESULTAT: %d failure(s)\n", failures);
    return failures ? 1 : 0;
}
