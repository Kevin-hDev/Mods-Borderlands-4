#include "ads_compat.h"
#include "generated_ads.h"
#include "camera_memory.h"
#include <array>
#include <bcrypt.h>
#include <cstring>

namespace {
int hex(char character) {
    if (character >= '0' && character <= '9') return character - '0';
    if (character >= 'a' && character <= 'f') return character - 'a' + 10;
    return -1;
}
bool decode(const char* text, unsigned char* output, size_t length) {
    if (!text || strnlen_s(text, length * 2 + 1) != length * 2) return false;
    for (size_t i = 0; i < length; ++i) {
        const int first = hex(text[i * 2]), second = hex(text[i * 2 + 1]);
        if (first < 0 || second < 0) return false;
        output[i] = static_cast<unsigned char>((first << 4) | second);
    }
    return true;
}
struct HashResources {
    HANDLE file = INVALID_HANDLE_VALUE;
    BCRYPT_ALG_HANDLE algorithm{};
    BCRYPT_HASH_HANDLE hash{};
    ~HashResources() {
        if (hash) BCryptDestroyHash(hash);
        if (algorithm) BCryptCloseAlgorithmProvider(algorithm, 0);
        if (file != INVALID_HANDLE_VALUE) CloseHandle(file);
    }
};
bool module_matches(HMODULE module, const char* expected) {
    wchar_t path[32768]{};
    const auto length = GetModuleFileNameW(module, path, static_cast<DWORD>(std::size(path)));
    return length && length < std::size(path) && apex_ads::file_matches(path, expected);
}
}

namespace apex_ads {
bool file_matches(const wchar_t* path, const char* expected) {
    unsigned char wanted[32]{}, digest[32]{};
    if (!path || !decode(expected, wanted, sizeof(wanted))) return false;
    HashResources resources;
    resources.file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING,
                                 FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
    LARGE_INTEGER length{};
    if (resources.file == INVALID_HANDLE_VALUE || !GetFileSizeEx(resources.file, &length)
            || length.QuadPart <= 0 || static_cast<uint64_t>(length.QuadPart) > MAX_HASH_FILE_BYTES
            || BCryptOpenAlgorithmProvider(&resources.algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0) return false;
    DWORD object_size{}, returned{};
    std::array<unsigned char, MAX_HASH_OBJECT_BYTES> object{};
    std::array<unsigned char, HASH_BUFFER_BYTES> buffer{};
    if (BCryptGetProperty(resources.algorithm, BCRYPT_OBJECT_LENGTH,
            reinterpret_cast<PUCHAR>(&object_size), sizeof(object_size), &returned, 0) < 0
            || returned != sizeof(object_size) || !object_size || object_size > object.size()
            || BCryptCreateHash(resources.algorithm, &resources.hash, object.data(), object_size,
                                nullptr, 0, 0) < 0) return false;
    uint64_t total{};
    DWORD count{};
    while (total < static_cast<uint64_t>(length.QuadPart)) {
        if (!ReadFile(resources.file, buffer.data(), static_cast<DWORD>(buffer.size()), &count, nullptr)
                || !count || count > static_cast<uint64_t>(length.QuadPart) - total
                || BCryptHashData(resources.hash, buffer.data(), count, 0) < 0) return false;
        total += count;
    }
    if (BCryptFinishHash(resources.hash, digest, sizeof(digest), 0) < 0) return false;
    unsigned char difference{};
    for (size_t i = 0; i < sizeof(digest); ++i) difference |= digest[i] ^ wanted[i];
    return difference == 0;
}

bool signature_matches(uintptr_t address, const char* expected) {
    unsigned char bytes[MAX_SIGNATURE_BYTES]{};
    const size_t characters = expected ? strnlen_s(expected, MAX_SIGNATURE_BYTES * 2 + 1) : 0;
    const size_t length = characters / 2;
    auto* target = reinterpret_cast<void*>(address);
    if (!length || characters % 2 || length > MAX_SIGNATURE_BYTES || !decode(expected, bytes, length)
            || !apex_camera::executable_in_main_module(target)
            || !apex_camera::memory_access(target, length)) return false;
    __try {
        return std::memcmp(target, bytes, length) == 0;
    } __except(EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

bool compatible_modules() {
    const auto sdk = GetModuleHandleW(L"unrealsdk.dll");
    const auto game = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    return sdk && game && module_matches(sdk, SDK_SHA256) && module_matches(nullptr, GAME_SHA256)
        && signature_matches(game + ZOOM_SCALE_RVA, ZOOM_SCALE_PREFIX)
        && signature_matches(game + HUD_PRODUCER_RVA, HUD_PRODUCER_PREFIX)
        && signature_matches(game + HUD_GETTER_RVA, HUD_GETTER_PREFIX)
        && signature_matches(game + MODE_GETTER_RVA, MODE_GETTER_PREFIX)
        && signature_matches(game + MODE_FINISH_RVA, MODE_FINISH_PREFIX)
        && signature_matches(game + VIEW_UPDATE_RVA, VIEW_UPDATE_PREFIX);
}
}
