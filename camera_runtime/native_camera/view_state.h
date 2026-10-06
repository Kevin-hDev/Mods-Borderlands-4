#pragma once
#include "view_target_bridge.h"
#include "framing_view.h"
#include "offset_blend.h"
#include <windows.h>

// One owner for view state; the dispatch releases this lock before calling SDK physics.
namespace apex_view::detail {
using Update = void (*)(void*, void*, float);
extern SRWLOCK guard;
extern Update original;
extern void** hooked_slot;
extern void* target_manager;
extern Config config;
extern Stats stats;
extern ULONGLONG deadline;
extern bool installed, suspended;
extern apex_ads::FramingContext framing;
extern apex_framing::Status framing_status;
extern bool framing_zoom_pending;
extern CollisionResolver collision;
extern DWORD owner_thread;
extern uint64_t generation;
extern OffsetBlend offset_blend;
extern double shoulder_seconds;
extern bool offset_smoothing;
extern bool shoulder_blending;
int stop_locked();
void dispatch(void* manager, void* view_target, float delta_time);
}
