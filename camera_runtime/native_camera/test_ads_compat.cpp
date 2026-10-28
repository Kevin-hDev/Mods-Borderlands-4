#include "ads_compat.h"
#include "generated_ads.h"
#include <windows.h>
#include <cassert>
#include <iostream>
#include "ads_test_assert.h"

int main(int argc, char** argv) {
    assert(argc == 2);
    const auto module = GetModuleHandleW(nullptr);
    const char* wrong = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    // The shell independently hashes this executable; both real module-file boundaries use it.
    assert(apex_ads::module_files_error(module, argv[1], argv[1]) == 0);
    assert(apex_ads::module_files_error(nullptr, argv[1], argv[1]) == apex_ads::ERROR_SDK_COMPATIBILITY);
    assert(apex_ads::module_files_error(module, wrong, argv[1]) == apex_ads::ERROR_SDK_COMPATIBILITY);
    assert(apex_ads::module_files_error(module, argv[1], wrong) == apex_ads::ERROR_GAME_COMPATIBILITY);
    assert(apex_ads::module_signatures_error(reinterpret_cast<uintptr_t>(module)) == apex_ads::ERROR_SIGNATURE);
    wchar_t folder[MAX_PATH]{}, file[MAX_PATH]{};
    assert(GetTempPathW(MAX_PATH, folder));
    assert(GetTempFileNameW(folder, L"ads", 0, file));
    HANDLE handle = CreateFileW(file, GENERIC_WRITE, 0, nullptr, OPEN_EXISTING, 0, nullptr);
    assert(handle != INVALID_HANDLE_VALUE);
    DWORD written{};
    assert(WriteFile(handle, "abc", 3, &written, nullptr) && written == 3);
    CloseHandle(handle);
    assert(apex_ads::file_matches(file,
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"));
    assert(!apex_ads::file_matches(file,
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015aa"));
    assert(!apex_ads::file_matches(file, "abc"));
    assert(DeleteFileW(file));
    assert(!apex_ads::file_matches(file,
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"));
    std::cout << "RESULTAT: OK (bounded streaming hash; SDK/game/signature refusal causes)\n";
}
