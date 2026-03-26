#include <EASTL/array.h>
#include <EASTL/map.h>
#include <EASTL/set.h>
#include <EASTL/shared_ptr.h>
#include <EASTL/string.h>
#include <EASTL/span.h>
#include <EASTL/unique_ptr.h>
#include <EASTL/vector.h>

#include "Allocator.h"

int main(int argc, char** argv)
{
    eastl::vector<int> vec = {1, 2, 3};
    eastl::string str_sso = "hello";
    eastl::string str_heap = "hellotherethisisalongstringthatexceedsssocapacity";

    eastl::shared_ptr<int> shared(new int(42));
    eastl::weak_ptr<int> weak = shared;
    eastl::unique_ptr<int> unique(new int(7));

    eastl::set<int> set_values = {3, 8, 10};
    eastl::map<int, eastl::string> map_values;
    map_values[1] = "one";
    map_values[2] = "two";

    eastl::array<int, 3> arr = {{3, 1, 4}};
    int raw[] = {5, 6, 7};
    eastl::span<int> dynamic_span(raw, 3);
    eastl::span<int, 3> static_span(raw, 3);

    // BREAK_MANUAL_SHOWCASE
    return argc + (argv ? 0 : 1);
}
