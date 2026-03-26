#include <EASTL/unique_ptr.h>

#include "Allocator.h"

int main()
{
    eastl::unique_ptr<int> unique_null;
    // BREAK_UNIQUE_PTR_NULL

    eastl::unique_ptr<int> unique_value(new int(7));
    // BREAK_UNIQUE_PTR_VALUE

    return 0;
}