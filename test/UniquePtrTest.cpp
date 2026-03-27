#include <EASTL/unique_ptr.h>

#include "Allocator.h"

void foo(eastl::unique_ptr<int> v)
{
}

int main()
{
    eastl::unique_ptr<int> unique_null;
    // BREAK_UNIQUE_PTR_NULL

    eastl::unique_ptr<int> unique_value(new int(7));
    // BREAK_UNIQUE_PTR_VALUE

    foo(eastl::move(unique_value));
    // BREAK_UNIQUE_PTR_MOVED

    return 0;
}