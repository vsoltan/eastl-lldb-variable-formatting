#include <EASTL/utility.h>
#include <EASTL/string.h>

#include "Allocator.h"

int main()
{
    eastl::pair<int, int> point {1, 2};
    // BREAK_PAIR_INT
    eastl::pair<int, eastl::string> mixed { 5, "hello" };
}