cmake_minimum_required(VERSION 3.11)

# Satisfies EASTL requirement
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)

include(FetchContent)

project(MyProject VERSION 1.0)

# Specify the C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

FetchContent_Declare(
    EASTL
    GIT_REPOSITORY https://github.com/electronicarts/EASTL.git
    GIT_TAG        master # can also specify a specific commit here
)

set(CMAKE_BUILD_TYPE DEBUG)

FetchContent_MakeAvailable(EASTL)

add_executable(ManualTest ManualTest.cpp Allocator.h)
target_link_libraries(ManualTest EASTL)

add_executable(VectorTest VectorTest.cpp Allocator.h)
target_link_libraries(VectorTest EASTL)

add_executable(StringTest StringTest.cpp Allocator.h)
target_link_libraries(StringTest EASTL)

add_executable(SharedPtrTest SharedPtrTest.cpp Allocator.h)
target_link_libraries(SharedPtrTest EASTL)

add_executable(UniquePtrTest UniquePtrTest.cpp Allocator.h)
target_link_libraries(UniquePtrTest EASTL)

add_executable(WeakPtrTest WeakPtrTest.cpp Allocator.h)
target_link_libraries(WeakPtrTest EASTL)

add_executable(MapTest MapTest.cpp Allocator.h)
target_link_libraries(MapTest EASTL)

add_executable(SetTest SetTest.cpp Allocator.h)
target_link_libraries(SetTest EASTL)

add_executable(ArrayTest ArrayTest.cpp Allocator.h)
target_link_libraries(ArrayTest EASTL)

add_executable(SpanTest SpanTest.cpp Allocator.h)
target_link_libraries(SpanTest EASTL)

add_executable(PairTest PairTest.cpp Allocator.h)
target_link_libraries(PairTest EASTL)
