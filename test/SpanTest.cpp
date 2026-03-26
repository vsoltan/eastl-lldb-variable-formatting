#include <EASTL/span.h>

#include "Allocator.h"

int main()
{
    int values[] = {5, 6, 7};
    eastl::span<int> dynamic_span(values, 3);
    // BREAK_SPAN_DYNAMIC

    eastl::span<int, 3> static_span(values, 3);
    // BREAK_SPAN_STATIC

    return 0;
}
