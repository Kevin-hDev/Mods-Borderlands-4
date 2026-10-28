#include "camera_builds.h"
#include "generated_ads.h"

// Read-only exports: file qualification is owned by the asynchronous ADS preflight.
extern "C" __declspec(dllexport) uint64_t view_update_rva() {
    return camera_builds::rva(apex_ads::VIEW_UPDATE_RVA);
}
extern "C" __declspec(dllexport) unsigned view_game_build() {
    return camera_builds::selected.load(std::memory_order_acquire);
}
