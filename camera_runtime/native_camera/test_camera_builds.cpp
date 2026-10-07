#include "camera_builds.h"
#include "ads_test_assert.h"
#include <iostream>

int main(int argc, char**) {
    using namespace camera_builds;
    assert(rva(0x3CD4832) == 0);
    unsigned char unknown[32]{};
    assert(profile_for_digest(unknown, 32) == 0);
    assert(profile_for_digest(nullptr, 32) == 0);
    assert(!publish(0) && !publish(3));
    const unsigned char steam[] = {0x9c,0x3a,0xfb,0x7d,0xc6,0xa5,0x50,0xa6,0xc2,0xe8,0x17,0x84,0x6c,0xd2,0xc4,0x0f,
        0xf1,0x1e,0x06,0x6d,0xc6,0xae,0xfe,0xb8,0x19,0xf8,0x02,0xe6,0xa4,0xc5,0xc3,0xe0};
    const unsigned char epic[] = {0x76,0x4a,0x4b,0xb5,0x40,0x3a,0x26,0x19,0xa0,0xbe,0x62,0x7d,0xe5,0xa7,0x38,0xe2,
        0x3e,0xa0,0x21,0xe8,0x67,0x2f,0x7f,0x0e,0x7a,0x53,0x66,0x97,0xd4,0xa0,0x67,0x19};
    assert(profile_for_digest(steam, 32) == 1 && profile_for_digest(epic, 32) == 2);
    assert(profile_for_digest(epic, 31) == 0);
    const bool use_epic = argc > 1;
    assert(publish(use_epic ? 2 : 1));
    assert(publish(use_epic ? 2 : 1));
    assert(!publish(use_epic ? 1 : 2)); // No mid-session profile changes.
    assert(rva(0x3CD4832) == (use_epic ? 0x3CC9ECAU : 0x3CD4832U));
    assert(rva(0xCB67CB0) == (use_epic ? 0xCB4AEB0U : 0xCB67CB0U));
    assert(rva(0xB004228) == (use_epic ? 0xAFF0268U : 0xB004228U));
    assert(rva(0x1234) == 0);
    assert(std::strcmp(prefix("5657534881ec80000000488b05ff2dff"), use_epic
        ? "5657534881ec80000000488b058f46fc" : "5657534881ec80000000488b05ff2dff") == 0);
    std::cout << "RESULTAT: exact build selection, preserved Steam, immutable profile\n";
}
