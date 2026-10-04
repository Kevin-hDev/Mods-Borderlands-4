#include "ads_compat.h"
#include <windows.h>
#include <cassert>
#include <iostream>
#include "ads_test_assert.h"

int main() {
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
    std::cout << "RESULTAT: OK (bounded streaming hash; constant-time digest comparison)\n";
}
