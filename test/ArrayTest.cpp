#include <EASTL/array.h>

#include "Allocator.h"

int main()
{
    eastl::array<int, 3> numbers{{3, 1, 4}};
    // BREAK_ARRAY_VALUES
    return 0;
}
