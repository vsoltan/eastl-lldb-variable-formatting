#include <EASTL/shared_ptr.h>

#include "Allocator.h"

int main()
{
    eastl::shared_ptr<int> shared(new int(42));
    eastl::weak_ptr<int> weak_live = shared;
    // BREAK_WEAK_PTR_LIVE

    shared.reset();
    // BREAK_WEAK_PTR_EXPIRED

    return 0;
}
