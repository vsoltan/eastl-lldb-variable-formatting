#include <EASTL/array.h>

#include "Allocator.h"

int main()
{
    eastl::array<int, 3> numbers{{3, 1, 4}};
    eastl::array<int, 7> many_numbers{{1, 2, 3, 4, 5, 6, 7}};
    // BREAK_ARRAY_VALUES
    return 0;
}
