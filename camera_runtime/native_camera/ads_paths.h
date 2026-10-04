#pragma once
#include "generated_ads.h"

namespace apex_ads {
using Config = PathsConfig;
using Sample = PathsSample;
using ZoomScale = float (*)(void*, void*, void*);
using Crosshair = bool (*)(void*);
int read_paths(const Config& config, Sample& output, ZoomScale zoom, Crosshair crosshair);
}
