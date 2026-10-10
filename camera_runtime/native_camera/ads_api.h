#pragma once
#include "ads_state.h"

namespace apex_ads { State& shared_ads(); }
#define ADS_API extern "C" __declspec(dllexport)
ADS_API int ads_prepare();
ADS_API int ads_verify_files();
ADS_API int ads_identify(uint64_t address, apex_ads::ObjectId* identity);
ADS_API int ads_publish(const apex_ads::AdsContext* context);
ADS_API int ads_clear(uint64_t generation);
ADS_API int ads_release(uint64_t generation);
ADS_API int ads_set_optic(uint64_t generation, float scale);
// Present when heavy weapons can aim at the shoulder: the Python side asks for it before offering them.
ADS_API int ads_heavy_aim();
ADS_API int ads_stats(apex_ads::AdsStats* output);
