#include "ads_identity.h"
#include "ads_memory.h"
#include "ads_sdk_exports.h"
#include <cstring>
#include <windows.h>

namespace {
template<class T> bool read(uintptr_t base, uint64_t offset, T& value) {
    return apex_ads::read_memory(base, offset, value);
}

bool entry(uintptr_t table, int32_t index, uintptr_t& item) {
    using namespace apex_ads;
    int32_t count{};
    uintptr_t chunks{}, chunk{};
    if (index < 0 || !read(table, OBJECT_COUNT_OFFSET, count) || count <= 0
            || static_cast<uint64_t>(count) > MAX_OBJECTS || index >= count
            || !read(table, OBJECT_CHUNKS_OFFSET, chunks)
            || !read(chunks, (static_cast<uint64_t>(index) / OBJECTS_PER_CHUNK) * 8, chunk)
            || chunk < MIN_POINTER || chunk % 8) return false;
    const auto offset = (static_cast<uint64_t>(index) % OBJECTS_PER_CHUNK) * OBJECT_ITEM_SIZE;
    if (offset > UINTPTR_MAX - chunk) return false;
    item = chunk + offset;
    return true;
}
}

namespace apex_ads {
bool resolve_id(uintptr_t table, const ObjectId& identity, uintptr_t& resolved) {
    resolved = 0;
    uintptr_t item{}, object{};
    int32_t serial{}, index{};
    uint32_t flags{};
    if (!identity.address || identity.serial <= 0 || !entry(table, identity.index, item)
            || !read(item, 0, object) || object != identity.address
            || !read(item, OBJECT_SERIAL_OFFSET, serial) || serial != identity.serial
            || !read(item, OBJECT_FLAGS_OFFSET, flags) || (flags & OBJECT_DESTROY_MASK)
            || !read(object, OBJECT_INDEX_OFFSET, index) || index != identity.index) return false;
    resolved = object;
    return true;
}

bool capture_id(uintptr_t table, uintptr_t object, ObjectId& identity) {
    identity = {};
    int32_t index{}, serial{};
    uintptr_t item{}, resolved{};
    if (!read(object, OBJECT_INDEX_OFFSET, index) || !entry(table, index, item)
            || !read(item, OBJECT_SERIAL_OFFSET, serial) || serial <= 0) return false;
    const ObjectId candidate{object, index, serial};
    if (!resolve_id(table, candidate, resolved)) return false;
    identity = candidate;
    return true;
}

uintptr_t sdk_object_table() {
    using Objects = const void* (*)();
    const auto module = GetModuleHandleW(sdk_exports::module);
    const auto symbol = module ? GetProcAddress(module, sdk_exports::gobjects) : nullptr;
    if (!symbol) return 0;
    Objects getter{};
    static_assert(sizeof(getter) == sizeof(symbol), "SDK function pointer size");
    std::memcpy(&getter, &symbol, sizeof(getter));
    uintptr_t table{};
    const auto wrapper = reinterpret_cast<uintptr_t>(getter());
    return read(wrapper, 0, table) ? table : 0;
}
}
