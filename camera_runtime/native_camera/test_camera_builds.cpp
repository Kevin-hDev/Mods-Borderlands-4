#include "camera_builds.h"
#include "ads_test_assert.h"
#include <iostream>
#include <string>

// One run per profile, since a selected profile never changes: no argument = Steam 4845623, "epic", "steam_4906557".
int main(int argc, char** argv) {
    using namespace camera_builds;
    assert(rva(0x3CD4832) == 0);
    unsigned char unknown[32]{};
    assert(profile_for_digest(unknown, 32) == 0);
    assert(profile_for_digest(nullptr, 32) == 0);
    assert(!publish(0) && !publish(profile_count + 1));
    const unsigned char steam[] = {0x9c,0x3a,0xfb,0x7d,0xc6,0xa5,0x50,0xa6,0xc2,0xe8,0x17,0x84,0x6c,0xd2,0xc4,0x0f,
        0xf1,0x1e,0x06,0x6d,0xc6,0xae,0xfe,0xb8,0x19,0xf8,0x02,0xe6,0xa4,0xc5,0xc3,0xe0};
    const unsigned char epic[] = {0x76,0x4a,0x4b,0xb5,0x40,0x3a,0x26,0x19,0xa0,0xbe,0x62,0x7d,0xe5,0xa7,0x38,0xe2,
        0x3e,0xa0,0x21,0xe8,0x67,0x2f,0x7f,0x0e,0x7a,0x53,0x66,0x97,0xd4,0xa0,0x67,0x19};
    const unsigned char steam_4906557[] = {0xba,0x75,0xf7,0xc2,0x87,0x4b,0x16,0xef,0xb5,0x53,0x6a,0x5c,0x0c,0xc2,0x89,
        0x18,0xa0,0x3e,0xfd,0x3e,0x55,0xd7,0x90,0xd2,0xe4,0xdb,0x57,0xde,0x0c,0x3a,0x35,0x3a};
    assert(profile_for_digest(steam, 32) == 1 && profile_for_digest(epic, 32) == 2);
    assert(profile_for_digest(steam_4906557, 32) == 3);
    assert(profile_for_digest(epic, 31) == 0);
    const std::string choice = argc > 1 ? argv[1] : "steam";
    const unsigned profile = choice == "epic" ? 2 : choice == "steam_4906557" ? 3 : 1;
    assert(publish(profile));
    assert(publish(profile));
    assert(!publish(profile == 1 ? 2 : 1)); // No mid-session profile changes.
    const uintptr_t view[] = {0x3CD4832, 0x3CC9ECA, 0x3CD7982};
    const uintptr_t zoom_type[] = {0xCB67CB0, 0xCB4AEB0, 0xCB6FD70};
    const uintptr_t eye_slot[] = {0xB004228, 0xAFF0268, 0xB00BB58};
    const char* zoom_cast[] = {"5657534881ec80000000488b05ff2dff", "5657534881ec80000000488b058f46fc",
                               "5657534881ec80000000488b05eff0fe"};
    assert(rva(0x3CD4832) == view[profile - 1]);
    assert(rva(0xCB67CB0) == zoom_type[profile - 1]);
    assert(rva(0xB004228) == eye_slot[profile - 1]);
    assert(rva(0x1234) == 0);
    assert(std::strcmp(prefix("5657534881ec80000000488b05ff2dff"), zoom_cast[profile - 1]) == 0);
    assert(std::strcmp(prefix("4157415641545657534881ec78030000"), "4157415641545657534881ec78030000") == 0);
    std::cout << "RESULTAT: exact build selection, preserved Steam, immutable profile (" << choice << ")\n";
}
