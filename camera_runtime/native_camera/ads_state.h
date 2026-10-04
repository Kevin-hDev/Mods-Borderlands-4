#pragma once
#include "ads_mode.h"
#include "ads_paths.h"
#include <windows.h>

namespace apex_ads {
struct Ticket {
    AdsContext context{};
    ModeSnapshot mode{};
    uintptr_t table{};
    uint64_t third_name{};
    ZoomScale zoom{};
};
bool validate_context(uintptr_t table, const AdsContext& context);
bool owner_alive(uintptr_t table, const AdsContext& context);

class State {
public:
    bool configure(uintptr_t table, uint64_t third_name, ZoomScale zoom);
    void set_installed(bool value);
    int publish(const AdsContext& candidate);
    int publish_pointer(const AdsContext* input);
    int clear(uint64_t generation);
    int release(uint64_t generation);
    bool ticket(void* manager, Ticket& output);
    bool ticket(Ticket& output);
    bool current(const Ticket& ticket);
    bool reticle_ticket(Ticket& output);
    bool reticle_current(const Ticket& ticket);
    AdsStats statistics();
    void note_error(uint32_t error);
    void record_fov(const Ticket& ticket, float before, float after, float scale);
    void record_reticle(const Ticket& ticket);
    void producer_called();
    void getter_called();
    void restored(void* collector);
    void installation_attempted();
private:
    SRWLOCK guard_ = SRWLOCK_INIT;
    AdsContext context_{};
    AdsStats stats_{};
    uintptr_t table_{};
    uint64_t third_name_{}, last_generation_{};
    DWORD thread_{};
    ZoomScale zoom_{};
    bool touched_{};
    bool reticle_enabled_{};
};
inline void increment(uint64_t& value) { if (value != UINT64_MAX) ++value; }
}
