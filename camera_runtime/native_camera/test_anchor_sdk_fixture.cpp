// Test-only SDK boundary. Never bundled with the trial or loaded by the game.
#include <cstdint>
#include <cwchar>

namespace { void* object_table{}; }
extern "C" __declspec(dllexport) void set_test_object_table(void* table) {
    object_table = table;
}
extern "C" __declspec(dllexport) const void* _unrealsdk_export__gobjects() {
    return &object_table;
}
extern "C" __declspec(dllexport) void _unrealsdk_export__fname_init(
        uint64_t* output, const wchar_t* text, uint32_t number) {
    *output = 0;
    if (number) return;
    if (std::wcscmp(text, L"ThirdPersonClimbing") == 0) *output = 57;
    if (std::wcscmp(text, L"Camera") == 0) *output = 27;
}
