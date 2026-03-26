#include <EASTL/set.h>

#include "Allocator.h"

int main()
{
    eastl::set<int> numbers;
    numbers.insert(10);
    numbers.insert(3);
    numbers.insert(8);
    // BREAK_SET_VALUES
    return 0;
}
