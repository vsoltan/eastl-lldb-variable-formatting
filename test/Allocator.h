#include <cstddef>

inline void* operator new[](size_t size,
    const char* /*name*/,
    int /*flags*/,
    unsigned /*debugFlags*/,
    const char* /*file*/,
    int /*line*/)
{
    return ::operator new[](size);
}

inline void* operator new[](size_t size,
    size_t /*alignment*/,
    size_t /*alignmentOffset*/,
    const char* /*name*/,
    int /*flags*/,
    unsigned /*debugFlags*/,
    const char* /*file*/,
    int /*line*/)
{
    return ::operator new[](size);
}