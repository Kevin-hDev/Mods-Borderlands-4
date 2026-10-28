#include "generated_ads.h"
#include <cstddef>
#include <iostream>

static_assert(offsetof(apex_ads::AdsContext, references) == 24, "Reference layout");
static_assert(offsetof(apex_ads::AdsContext, paths) == 152, "Reader layout");
static_assert(offsetof(apex_ads::ViewStats, ads_generation) == 104, "View extension");

int main() {
    std::cout << "RESULTAT: OK (native ADS layouts)\n";
}
