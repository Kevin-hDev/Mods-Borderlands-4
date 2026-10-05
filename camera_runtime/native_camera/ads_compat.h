#pragma once
#include <cstdint>
#include <windows.h>

namespace apex_ads {
bool file_matches(const wchar_t* path, const char* expected);
int module_files_error(HMODULE sdk, const char* sdk_hash, const char* game_hash);
int module_signatures_error(uintptr_t game);
int verify_module_files_error();
int compatible_modules_error();
bool signature_matches(uintptr_t address, const char* expected);
}
