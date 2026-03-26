# LLDB has its own cap (`target.max-children-count`), but we use provider-level
# caps to avoid expensive synthetic expansion that can impact debugger performance.
VECTOR_MAX_SIZE = 500
ARRAY_MAX_SIZE = 500
SPAN_MAX_SIZE = 500
STRING_MAX_SIZE = 500
TREE_MAX_SIZE = 500

