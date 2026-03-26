#include <EASTL/string.h>

#include "Allocator.h"

int main()
{
    eastl::string sso = "hello";
    // BREAK_STRING_SSO
    sso += " world";
    // BREAK_STRING_SSO_APPEND

    eastl::string heap = "hellotherethisisalongstringthatexceedsssocapacity";
    // BREAK_STRING_HEAP
    heap += "shouldbeheapsized";
    // BREAK_STRING_HEAP_APPEND

    eastl::string ssoToHeap = "shortString";
    // BREAK_STRING_SSO_TO_HEAP
    ssoToHeap += "shouldbetransitionedtoheap";
    // BREAK_STRING_SSO_TO_HEAP_APPEND
    return 0;
}
