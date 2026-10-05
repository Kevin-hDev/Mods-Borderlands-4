#include "ads_api.h"
#include <cassert>
#include <iostream>
#include "ads_test_assert.h"

int main() {
    assert(ads_verify_files() == apex_ads::ERROR_SDK_COMPATIBILITY);
    assert(ads_prepare() == apex_ads::ERROR_SDK_COMPATIBILITY);
    assert(ads_prepare() == apex_ads::ERROR_SDK_COMPATIBILITY);
    apex_ads::AdsStats stats{};
    assert(ads_stats(&stats) == 0 && !stats.installed && !stats.active && !stats.install_attempts);
    assert(stats.error == apex_ads::ERROR_SDK_COMPATIBILITY);
    apex_ads::ObjectId identity{};
    assert(ads_identify(0x10000, &identity) != 0 && !identity.address);
    assert(ads_publish(nullptr) != 0);
    assert(ads_release(1) != 0);
    assert(ads_stats(nullptr) != 0);
    std::cout << "RESULTAT: OK (native API refuses unsupported process before hooking)\n";
}
