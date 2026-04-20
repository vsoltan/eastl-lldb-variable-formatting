#include <EASTL/string.h>
#include <EASTL/vector.h>

#include "Allocator.h"

int main()
{
    // BREAK_STRING_UNINITIALIZED
    eastl::string empty = "";
    // BREAK_STRING_EMPTY

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

    eastl::string8 s8 = "regular string";
    eastl::u8string su8 = u8"utf8 string";
    eastl::string16 s16 = u"wide string";
    eastl::string32 s32 = U"even wider string";
    // BREAK_VARIABLE_WIDTH_STRING

    eastl::vector<eastl::string> strings = {"hello", "world", "foo"};
    volatile int dummy = 0;
    for (const auto& s : strings) {
        dummy += s.length(); // BREAK_STRING_RANGE_LOOP
    }
    return dummy;
}
