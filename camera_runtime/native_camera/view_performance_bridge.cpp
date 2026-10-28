#include "view_performance.h"
#include "ads_memory.h"

extern "C" __declspec(dllexport) int view_perf_enable(uint32_t milliseconds) {
    return apex_performance::enable(milliseconds);
}
extern "C" __declspec(dllexport) int view_perf_read(apex_performance::Snapshot* output) {
    struct Request { uint32_t abi, size; } request{};
    const auto address = reinterpret_cast<uintptr_t>(output);
    if (!apex_ads::read_memory(address, 0, request)) return 1;
    const auto result = apex_performance::snapshot();
    if (request.abi != result.abi || request.size != sizeof(result)) return 1;
    return apex_ads::write_memory(address, 0, result) ? 0 : 1;
}
