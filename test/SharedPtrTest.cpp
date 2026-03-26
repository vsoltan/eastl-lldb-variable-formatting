#include <EASTL/shared_ptr.h>

#include "Allocator.h"

int main()
{
    eastl::shared_ptr<int> null_ptr;
    // BREAK_SHARED_PTR_NULL

    eastl::shared_ptr<int> ptr(new int(42));
    // BREAK_SHARED_PTR_VALUE

    eastl::shared_ptr<int> ptr_copy = ptr;
    // BREAK_SHARED_PTR_COPIED

    return 0;
}
