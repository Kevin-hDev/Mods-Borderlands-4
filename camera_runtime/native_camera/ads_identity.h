#pragma once
#include "generated_ads.h"

namespace apex_ads {
bool resolve_id(uintptr_t table, const ObjectId& identity, uintptr_t& resolved);
bool capture_id(uintptr_t table, uintptr_t object, ObjectId& identity);
uintptr_t sdk_object_table();
}
