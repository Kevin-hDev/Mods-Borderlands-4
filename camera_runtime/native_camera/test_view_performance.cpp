#include "view_performance.h"
#include "ads_test_assert.h"
#include <cassert>
#include <iostream>
#include <array>
#include <cstring>

extern "C" int view_perf_read(apex_performance::Snapshot* output);

int main() {
    using namespace apex_performance;
    assert(begin() == 0);
    alignas(8) std::array<unsigned char, sizeof(Snapshot)> undersized{};
    undersized.fill(0x5a);
    const uint32_t request[] = {2, 8};
    std::memcpy(undersized.data(), request, sizeof(request));
    const auto untouched = undersized;
    assert(view_perf_read(reinterpret_cast<Snapshot*>(undersized.data())) != 0);
    assert(undersized == untouched); // Never overwrite a caller using an older/smaller ABI.
    Snapshot exported{};
    assert(view_perf_read(&exported) == 0);
    assert(exported.abi == 2 && exported.size == sizeof(exported));
    assert(enable(0) == 0);
    assert(enable(max_duration_ms + 1) != 0);
    assert(begin() == 0);
    assert(enable(1000) == 0);
    const auto first = begin();
    assert(first != 0);
    record(Stage::view, true, first, first + 42);
    record(Stage::view, true, first, first + 18);
    record(Stage::view, false, first, first + 7);
    auto result = snapshot();
    assert(result.frequency > 0);
    assert(result.rows[0][1].count == 2);
    assert(result.rows[0][1].ticks == 60);
    assert(result.rows[0][1].maximum == 42);
    assert(result.rows[0][0].count == 1 && result.rows[0][0].ticks == 7);
    record(Stage::view, true, 0, first + 99);
    record(Stage::view, true, first + 99, first);
    assert(snapshot().rows[0][1].count == 2);
    assert(enable(0) == 0);
    assert(begin() == 0);
    assert(snapshot().rows[0][1].count == 2);
    assert(enable(1000) == 0);
    assert(snapshot().rows[0][1].count == 0);
    {
        Measurement timing(Stage::framing, true);
        Sleep(1);
    }
    assert(snapshot().rows[static_cast<size_t>(Stage::framing)][1].count == 1);
    assert(enable(1) == 0);
    Sleep(10);
    assert(begin() == 0);
    std::cout << "RESULTAT: native performance timing OK\n";
}
