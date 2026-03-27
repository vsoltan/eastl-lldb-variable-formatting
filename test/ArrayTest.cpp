#include <EASTL/array.h>

#include "Allocator.h"

int main()
{
    eastl::array<int, 3> numbers{{3, 1, 4}};
    // BREAK_ARRAY_VALUES

    eastl::array<int, 7> many_numbers{{1, 2, 3, 4, 5, 6, 7}};
    // BREAK_ARRAY_EXCEEDS_SUMMARY_MAX
    return 0;
}
