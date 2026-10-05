#pragma once
// Opt-in, bounded diagnostics. Disabled by default and expires without a caller.
#include <windows.h>
#include <atomic>
#include <cstdint>
#include <cstddef>

namespace apex_performance {
enum class Stage : size_t {
    view, original, zoom, framing, progress,
    progress_signatures, progress_find, progress_cast, progress_call, count
};
constexpr uint32_t max_duration_ms = 120000;
constexpr size_t stage_count = static_cast<size_t>(Stage::count);
struct Row { uint64_t count{}, ticks{}, maximum{}; };
struct Snapshot {
    uint32_t abi = 2, size = sizeof(Snapshot);
    uint64_t frequency{};
    Row rows[stage_count][2]{};
};
inline SRWLOCK timing_guard = SRWLOCK_INIT;
inline std::atomic<uint64_t> deadline{};
inline Snapshot totals{};

inline uint64_t counter() {
    LARGE_INTEGER value{};
    return QueryPerformanceCounter(&value) ? static_cast<uint64_t>(value.QuadPart) : 0;
}
inline uint64_t begin() {
    const auto until = deadline.load(std::memory_order_relaxed);
    return until && GetTickCount64() < until ? counter() : 0;
}
inline int enable(uint32_t duration_ms) {
    deadline.store(0, std::memory_order_relaxed);
    if (duration_ms > max_duration_ms) return 1;
    if (!duration_ms) return 0;
    LARGE_INTEGER frequency{};
    if (!QueryPerformanceFrequency(&frequency) || frequency.QuadPart <= 0) return 1;
    AcquireSRWLockExclusive(&timing_guard);
    totals = {};
    totals.frequency = static_cast<uint64_t>(frequency.QuadPart);
    ReleaseSRWLockExclusive(&timing_guard);
    deadline.store(GetTickCount64() + duration_ms, std::memory_order_relaxed);
    return 0;
}
inline void record(Stage stage, bool aiming, uint64_t start, uint64_t end) {
    const auto index = static_cast<size_t>(stage);
    if (!start || end < start || index >= stage_count) return;
    AcquireSRWLockExclusive(&timing_guard);
    auto& row = totals.rows[index][aiming ? 1 : 0];
    ++row.count;
    row.ticks += end - start;
    if (end - start > row.maximum) row.maximum = end - start;
    ReleaseSRWLockExclusive(&timing_guard);
}
inline Snapshot snapshot() {
    AcquireSRWLockShared(&timing_guard);
    const auto result = totals;
    ReleaseSRWLockShared(&timing_guard);
    return result;
}
class Measurement {
    Stage stage_;
    uint64_t start_;
public:
    bool aiming;
    Measurement(Stage stage, bool aim) : stage_(stage), start_(begin()), aiming(aim) {}
    ~Measurement() { if (start_) record(stage_, aiming, start_, counter()); }
    Measurement(const Measurement&) = delete;
    Measurement& operator=(const Measurement&) = delete;
};
}
