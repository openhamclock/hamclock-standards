// antenna_demo.cpp
#include <cstdint>
#include <cstdio>
#include "antenna_lookup.h"

int main()
{
    antenna_lookup_init();

    struct TestCase { int msb; int lsb; };
    static const TestCase tests[] = {
        { 0,   0 },
        { 1,  17 },
        { 4,   5 },
        { 2,  17 },
        { 5,  14 },
        { 9,  99 },     // not found
    };

    for (const auto& t : tests) {
        uint16_t index = static_cast<uint16_t>(t.msb * 256 + t.lsb);
        const AntennaInfo* info = antenna_lookup(index);
        if (info) {
            std::printf("index=%5u (msb=%d, lsb=%3d)  path='%s'  desc='%s'\n",
                        index, t.msb, t.lsb,
                        info->path.c_str(),
                        info->description.c_str());
        } else {
            std::printf("index=%5u (msb=%d, lsb=%3d)  NOT FOUND\n",
                        index, t.msb, t.lsb);
        }
    }
    return 0;
}