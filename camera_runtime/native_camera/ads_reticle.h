#pragma once
#include "ads_state.h"

namespace apex_ads {
using Producer = void (*)(void*, void*);
using Getter = bool (*)(void*);
class Reticle {
public:
    explicit Reticle(State& state) : state_(state) {}
    bool configure(Producer producer, Getter getter, uintptr_t caller);
    void set_caller(uintptr_t caller) { caller_ = caller; }
    void** producer_slot() { return reinterpret_cast<void**>(&producer_); }
    void** getter_slot() { return reinterpret_cast<void**>(&getter_); }
    void producer(void* collector, void* weapon);
    bool getter(void* weapon, uintptr_t caller);
private:
    struct Frame {
        Reticle* owner{};
        Ticket ticket{};
        void* collector{};
        void* weapon{};
        bool eligible{};
    };
    static thread_local Frame* frame_;
    State& state_;
    Producer producer_{};
    Getter getter_{};
    uintptr_t caller_{};
};
}
