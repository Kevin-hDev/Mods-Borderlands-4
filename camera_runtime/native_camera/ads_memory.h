#pragma once
#include "camera_memory.h"
#include "generated_ads.h"
#include <cstring>

namespace apex_ads {
template<class T> bool read_memory(uintptr_t base, uint64_t offset, T& value) {
    if (base < MIN_POINTER || base % sizeof(void*) || offset > UINTPTR_MAX - base
            || !apex_camera::memory_access(reinterpret_cast<void*>(base + offset), sizeof(T))) return false;
    __try {
        std::memcpy(&value, reinterpret_cast<void*>(base + offset), sizeof(T));
        return true;
    } __except(EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}
template<class T> bool write_memory(uintptr_t base, uint64_t offset, const T& value) {
    if (base < MIN_POINTER || base % sizeof(void*) || offset > UINTPTR_MAX - base
            || !apex_camera::memory_access(reinterpret_cast<void*>(base + offset), sizeof(T), true)) return false;
    __try {
        std::memcpy(reinterpret_cast<void*>(base + offset), &value, sizeof(T));
        return true;
    } __except(EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}
}
