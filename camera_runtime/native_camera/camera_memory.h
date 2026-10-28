#pragma once
#include <windows.h>
#include <cstdint>

namespace apex_camera {
inline bool memory_access(void* address, size_t length, bool writable = false) {
    MEMORY_BASIC_INFORMATION memory{};
    if (!address || !length || VirtualQuery(address, &memory, sizeof(memory)) != sizeof(memory)
        || memory.State != MEM_COMMIT || (memory.Protect & (PAGE_GUARD | PAGE_NOACCESS))) {
        return false;
    }
    auto start = reinterpret_cast<uintptr_t>(address);
    auto end = reinterpret_cast<uintptr_t>(memory.BaseAddress) + memory.RegionSize;
    if (start > end || length > end - start) {
        return false;
    }
    const DWORD allowed = writable ? (PAGE_READWRITE | PAGE_EXECUTE_READWRITE | PAGE_WRITECOPY
        | PAGE_EXECUTE_WRITECOPY) : (PAGE_READONLY | PAGE_READWRITE | PAGE_WRITECOPY
        | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY);
    return (memory.Protect & allowed) != 0;
}

inline bool executable_in_main_module(void* address) {
    MEMORY_BASIC_INFORMATION memory{};
    return VirtualQuery(address, &memory, sizeof(memory)) == sizeof(memory)
        && memory.AllocationBase == GetModuleHandleW(nullptr)
        && memory.State == MEM_COMMIT
        && !(memory.Protect & (PAGE_GUARD | PAGE_NOACCESS))
        && (memory.Protect & (PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY));
}

inline int replace_slot(void** slot, void* expected, void* replacement) {
    MEMORY_BASIC_INFORMATION memory{};
    if (VirtualQuery(slot, &memory, sizeof(memory)) != sizeof(memory)
        || (memory.Protect & (PAGE_EXECUTE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE
                              | PAGE_EXECUTE_WRITECOPY))) {
        return 4;
    }
    DWORD protection;
    if (!VirtualProtect(slot, sizeof(void*), PAGE_READWRITE, &protection)) {
        return 1;
    }
    void* previous = InterlockedCompareExchangePointer(slot, replacement, expected);
    DWORD ignored;
    if (!VirtualProtect(slot, sizeof(void*), protection, &ignored)) {
        InterlockedCompareExchangePointer(slot, expected, replacement);
        VirtualProtect(slot, sizeof(void*), protection, &ignored);
        return 2;
    }
    return previous == expected ? 0 : 3;
}
}
