#pragma once
#include "generated_ads.h"
#include "ads_paths.h"
#include "interaction_alignment.h"
#include <cstring>

namespace apex_ads {
struct NativeFixture {
    static constexpr uint64_t third = 0x1234;
    alignas(16) unsigned char objects[8][0x4000]{};
    alignas(16) unsigned char registry[64]{}, items[8][24]{}, mode[0xb00]{}, link[0x400]{};
    uintptr_t chunks[1]{};
    template<class T> void put(size_t index, size_t offset, T value) {
        std::memcpy(objects[index] + offset, &value, sizeof(value));
    }
    template<class T> static void store(unsigned char* target, size_t offset, T value) {
        std::memcpy(target + offset, &value, sizeof(value));
    }
    uintptr_t pointer(size_t index) const { return reinterpret_cast<uintptr_t>(objects[index]); }
    uintptr_t table_address() const { return reinterpret_cast<uintptr_t>(registry); }
    void* manager() { return objects[2]; }
    void* collector() { return objects[5]; }
    static float zoom(void*, void*, void*) { return 0.5f; }
    NativeFixture() {
        chunks[0] = reinterpret_cast<uintptr_t>(items);
        store(registry, OBJECT_CHUNKS_OFFSET, reinterpret_cast<uintptr_t>(chunks));
        store(registry, OBJECT_COUNT_OFFSET, int32_t{8});
        for (int32_t i = 0; i < 8; ++i) {
            put(static_cast<size_t>(i), OBJECT_INDEX_OFFSET, i);
            store(items[i], 0, pointer(static_cast<size_t>(i)));
            store(items[i], OBJECT_SERIAL_OFFSET, int32_t{1});
        }
        put(0, CONTROLLER_MANAGER_OFFSET, pointer(2));
        put(0, apex_interaction::pawn_offset, pointer(1));
        put(1, ACTOR_CONTROLLER_LINK_OFFSET, reinterpret_cast<uintptr_t>(link));
        store(link, ACTOR_LINK_CONTROLLER_OFFSET, pointer(0));
        put(2, MANAGER_MODE_OFFSET, third);
        put(2, MANAGER_MODE_OBJECT_OFFSET, reinterpret_cast<uintptr_t>(mode));
        put(2, MANAGER_STATE_OFFSET, pointer(6));
        put(2, MANAGER_INPUTS_OFFSET, pointer(7));
        put(4, ANIMATION_WEAPON_OFFSET, pointer(3));
        put(4, ANIMATION_CATEGORY_OFFSET, uint8_t{4});
        put(5, OBJECT_OUTER_OFFSET, pointer(1));
        put(6, STATE_INPUTS_OFFSET, pointer(7));
        put(7, INPUTS_CONTROLLER_OFFSET, pointer(0));
    }
    AdsContext context(uint64_t generation) const {
        AdsContext result{};
        result.abi = static_cast<uint32_t>(ADS_ABI);
        result.size = sizeof(result);
        result.enabled = 1;
        result.generation = generation;
        for (int32_t i = 0; i < 8; ++i) result.references[i] = {pointer(i), i, 1};
        result.paths = {static_cast<uint32_t>(ADS_ABI), 0, pointer(6), pointer(7), pointer(0), pointer(3),
                        0x4000, 0x4000, 0x4000, 0x4000};
        return result;
    }
    FramingContext framing_context() {
        FramingContext result{};
        result.abi = static_cast<uint32_t>(VIEW_ABI);
        result.size = sizeof(result);
        const int indexes[] = {0, 1, 2, 5};
        for (size_t i = 0; i < 4; ++i) result.references[i] = {pointer(indexes[i]), indexes[i], 1};
        result.actor_size = result.root_size = 0x4000;
        result.root_offset = 0x200; result.capsule_offset = 0x208;
        result.location_offset = 0x100; result.parent_offset = 0x118;
        put(1, result.root_offset, pointer(5));
        put(1, result.capsule_offset, pointer(5));
        const double location[] = {500, 0, 0};
        std::memcpy(objects[5] + result.location_offset, location, sizeof(location));
        return result;
    }
    void recycle(size_t index) { store(items[index], OBJECT_SERIAL_OFFSET, int32_t{2}); }
    void restore(size_t index) { store(items[index], OBJECT_SERIAL_OFFSET, int32_t{1}); }
};
}
