#include <EASTL/vector.h>

#include "Allocator.h"

int main()
{
    eastl::vector<int> v = {1, 2, 3, 4, 5};
    // BREAK_VECTOR_INITIALIZED
    v.push_back(6);
    // BREAK_VECTOR_PUSHED
    v.clear();
    // BREAK_VECTOR_CLEARED
    for (int i = 0; i < 10000; i++) {
        v.push_back(i);
    }
    // BREAK_LARGE_VECTOR
    v.resize(100);
    // BREAK_VECTOR_RESIZED
    return 0;
}
