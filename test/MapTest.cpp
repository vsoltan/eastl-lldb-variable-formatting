#include <EASTL/map.h>
#include <EASTL/string.h>

#include "Allocator.h"

int main()
{
    eastl::map<int, eastl::string> labels;
    labels[1] = "one";
    labels[4] = "four";
    labels[2] = "two";
    // BREAK_MAP_VALUES
    return 0;
}
