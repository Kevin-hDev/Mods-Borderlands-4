#include "framing_view.h"
#include "framing_progress.h"
#include "framing_code.h"
#include "ads_memory.h"
#include "ads_compat.h"
#include "view_performance.h"

namespace {
using namespace apex_ads;
using namespace apex_framing;
void* pointer_at(uintptr_t base, size_t offset = 0) {
    uintptr_t pointer{};
    return read_memory(base, offset, pointer) ? reinterpret_cast<void*>(pointer) : nullptr;
}
void* virtual_at(void* object, size_t slot) {
    // Calls belong to the camera thread. Separate thread-local caches avoid shared mutation.
    static thread_local ExecutableCache code;
    void* table = pointer_at(reinterpret_cast<uintptr_t>(object));
    void* method = pointer_at(reinterpret_cast<uintptr_t>(table), slot);
    return code.accepts(method) ? method : nullptr;
}
void* find(void* actor, void* type) {
    apex_performance::Measurement timing(apex_performance::Stage::progress_find, true);
    auto method = reinterpret_cast<Find>(virtual_at(actor, ZOOM_FIND_SLOT));
    if (!method) return nullptr;
    void* object = method(actor, type);
    return apex_camera::memory_access(object, OBJECT_OUTER_OFFSET + 8) ? object : nullptr;
}
void* cast(void* object, void* type) {
    apex_performance::Measurement timing(apex_performance::Stage::progress_cast, true);
    const uintptr_t module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    auto method = reinterpret_cast<Cast>(module + ZOOM_CAST_RVA);
    void* value = method(object, type);
    // Exactly the three getters used by the game's qualified progress reader.
    return value && value != object && virtual_at(value, 0x10) && virtual_at(value, 0x18)
        && virtual_at(value, 0x28) ? value : nullptr;
}
float progress(void* value) {
    apex_performance::Measurement timing(apex_performance::Stage::progress_call, true);
    const auto module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    return reinterpret_cast<Progress>(module + ZOOM_PROGRESS_RVA)(value);
}
bool read(void* manager, void* actor, float& output) {
    apex_performance::Measurement timing(apex_performance::Stage::progress, true);
    const auto module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    {
        apex_performance::Measurement signatures(apex_performance::Stage::progress_signatures, true);
        // As with ADS preparation, qualify fixed game code once per library lifetime.
        // A mismatch is terminal; live object identities and vtables are never cached here.
        static const bool compatible = module
            && signature_matches(module + ZOOM_PROGRESS_RVA, ZOOM_PROGRESS_PREFIX)
            && signature_matches(module + ZOOM_CAST_RVA, ZOOM_CAST_PREFIX);
        if (!compatible) return false;
    }
    void* inputs = pointer_at(reinterpret_cast<uintptr_t>(manager), MANAGER_INPUTS_OFFSET);
    void* target = pointer_at(reinterpret_cast<uintptr_t>(inputs), ZOOM_TARGET_OFFSET);
    void* type = pointer_at(module, ZOOM_TYPE_RVA);
    if (!apex_camera::memory_access(type, OBJECT_OUTER_OFFSET + 8)) return false;
    float current{};
    if (!read_progress(target, actor, type, find, cast, progress, current)
        || pointer_at(reinterpret_cast<uintptr_t>(manager), MANAGER_INPUTS_OFFSET) != inputs
        || pointer_at(reinterpret_cast<uintptr_t>(inputs), ZOOM_TARGET_OFFSET) != target
        || pointer_at(module, ZOOM_TYPE_RVA) != type) return false;
    output = current;
    return true;
}
}
namespace apex_framing {
bool native_progress(void* manager, void* actor, float& output) {
    __try { return read(manager, actor, output); }
    // Recover stale-pointer faults only; native gameplay exceptions keep their original handler.
    __except(GetExceptionCode() == EXCEPTION_ACCESS_VIOLATION
                 ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH) { return false; }
}
}
