#pragma once
#include <cstdlib>
#include <iostream>
#undef assert
#define assert(condition) do { if (!(condition)) { \
    std::cerr << "RESULTAT: ECHEC line=" << __LINE__ << "\n"; std::exit(1); \
} } while (false)
