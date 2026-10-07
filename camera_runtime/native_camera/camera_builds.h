#pragma once
#include "generated_camera_builds.h"
#include <atomic>
#include <cstddef>
#include <cstring>

namespace camera_builds {
inline std::atomic<unsigned> selected{0};

inline unsigned profile_for_digest(const unsigned char* digest, size_t size) {
    if (!digest || size != 32) return 0;
    unsigned match = 0;
    for (unsigned profile = 0; profile < 2; ++profile) {
        unsigned difference = 0;
        for (size_t i = 0; i < size; ++i) {
            const auto digit = [](char value) { return value <= '9' ? value - '0' : value - 'a' + 10; };
            const unsigned wanted = (digit(hashes[profile][i * 2]) << 4) | digit(hashes[profile][i * 2 + 1]);
            difference |= digest[i] ^ wanted;
        }
        if (!difference) match = profile + 1;
    }
    return match;
}

inline bool publish(unsigned profile) {
    if (profile < 1 || profile > 2) return false;
    unsigned empty = 0;
    return selected.compare_exchange_strong(empty, profile, std::memory_order_acq_rel) || empty == profile;
}

inline uintptr_t rva(uintptr_t steam_reference) {
    const auto profile = selected.load(std::memory_order_acquire);
    if (!profile) return 0;
    for (const auto& row : addresses) {
        if (row.steam == steam_reference) return profile == 1 ? row.steam : row.epic;
    }
    return 0;
}

inline const char* prefix(const char* steam_reference) {
    const auto profile = selected.load(std::memory_order_acquire);
    if (!profile || !steam_reference) return nullptr;
    for (const auto& row : prefixes) {
        if (std::strcmp(row.steam, steam_reference) == 0) return profile == 1 ? row.steam : row.epic;
    }
    // Anchor signatures contain no relocated operands and are identical on both qualified files.
    return steam_reference;
}
}
