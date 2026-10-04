#pragma once
#include <cstdint>

namespace apex_ads {
bool file_matches(const wchar_t* path, const char* expected);
bool compatible_modules();
bool signature_matches(uintptr_t address, const char* expected);
}
