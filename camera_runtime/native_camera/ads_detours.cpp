#include "ads_detours.h"

namespace apex_ads {
int Detours::install(State& state, Reticle& reticle, const DetourBindings& bindings) {
    if (attempted_) return installed_ ? 0 : static_cast<int>(ERROR_INSTALL);
    if (!bindings.verified || !bindings.install || !bindings.pin || !bindings.module
            || !bindings.getter || !bindings.producer) return static_cast<int>(ERROR_UNSUPPORTED);
    attempted_ = true;
    state.installation_attempted();
    state.set_installed(false);
    reticle.set_caller(bindings.module + HUD_GETTER_RETURN_RVA);
    if (!bindings.pin(bindings.getter)
            || !bindings.install(bindings.module + HUD_GETTER_RVA, bindings.getter,
                                 reticle.getter_slot(), "ApexADS.Getter", sizeof("ApexADS.Getter") - 1)
            || !*reticle.getter_slot()
            || !bindings.install(bindings.module + HUD_PRODUCER_RVA, bindings.producer,
                                 reticle.producer_slot(), "ApexADS.Producer", sizeof("ApexADS.Producer") - 1)
            || !*reticle.producer_slot()) {
        state.note_error(static_cast<uint32_t>(ERROR_INSTALL));
        return static_cast<int>(ERROR_INSTALL);
    }
    installed_ = true;
    state.set_installed(true);
    return 0;
}
}
