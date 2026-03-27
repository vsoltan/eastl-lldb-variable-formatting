
from formatters.string import (
    basic_string_SummaryProvider,
    basic_string_SyntheticChildrenProvider,
)
from formatters.vector import (
    VectorBase_SummaryProvider,
    VectorBase_SyntheticChildrenProvider,
)
from formatters.ref_counted_ptr import (
    RefCountedPtrSyntheticChildrenProvider,
    shared_ptr_SummaryProvider,
    WeakPtr_SummaryProvider,
)
from formatters.unique_ptr import (
    unique_ptr_SummaryProvider,
    unique_ptr_SyntheticChildrenProvider,
)
from formatters.tree import (
    RBTree_SummaryProvider,
    RBTree_SyntheticChildrenProvider,
)
from formatters.array import (
    Array_SummaryProvider,
    Array_SyntheticChildrenProvider,
)
from formatters.span import (
    span_SummaryProvider,
    span_SyntheticChildrenProvider,
)
from formatters.pair import (
    pair_SummaryProvider,
    pair_SyntheticChildrenProvider
)


#LLDB resolves formatter symbols against the Python module object loaded by command script import (EASTL.py). We cannot directly register
# commands using formatters.*, instead we make them available in the current module.
_ = (
    basic_string_SummaryProvider,
    basic_string_SyntheticChildrenProvider,
    VectorBase_SummaryProvider,
    VectorBase_SyntheticChildrenProvider,
    RefCountedPtrSyntheticChildrenProvider,
    shared_ptr_SummaryProvider,
    unique_ptr_SummaryProvider,
    unique_ptr_SyntheticChildrenProvider,
    WeakPtr_SummaryProvider,
    RBTree_SummaryProvider,
    RBTree_SyntheticChildrenProvider,
    Array_SummaryProvider,
    Array_SyntheticChildrenProvider,
    span_SummaryProvider,
    span_SyntheticChildrenProvider,
    pair_SummaryProvider,
    pair_SyntheticChildrenProvider
)

EASTL_TYPE_CATEGORY = "EASTL"

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::basic_string<.*>$ -C true -l EASTL.basic_string_SyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::basic_string<.*>$ -e -F EASTL.basic_string_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::VectorBase<.*>$ -C true -l EASTL.VectorBase_SyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::vector<.*>$ -C true -l EASTL.VectorBase_SyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::VectorBase<.*>$ -e -F EASTL.VectorBase_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::vector<.*>$ -e -F EASTL.VectorBase_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::shared_ptr<.*>$ -C true -l EASTL.RefCountedPtrSyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::shared_ptr<.*>$ -e -F EASTL.shared_ptr_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::unique_ptr<.*>$ -C true -l EASTL.unique_ptr_SyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::unique_ptr<.*>$ -e -F EASTL.unique_ptr_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::weak_ptr<.*>$ -C true -l EASTL.RefCountedPtrSyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::weak_ptr<.*>$ -e -F EASTL.WeakPtr_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::set<.*>$ -C true -l EASTL.RBTree_SyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::set<.*>$ -e -F EASTL.RBTree_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::multiset<.*>$ -C true -l EASTL.RBTree_SyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::multiset<.*>$ -e -F EASTL.RBTree_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::map<.*>$ -C true -l EASTL.RBTree_SyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::map<.*>$ -e -F EASTL.RBTree_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::multimap<.*>$ -C true -l EASTL.RBTree_SyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::multimap<.*>$ -e -F EASTL.RBTree_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::array<.*>$ -C true -l EASTL.Array_SyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::array<.*>$ -e -F EASTL.Array_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::span<.*>$ -C true -l EASTL.span_SyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::span<.*>$ -e -F EASTL.span_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::pair<.*>$ -C true -l EASTL.pair_SyntheticChildrenProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::pair<.*>$ -e -F EASTL.pair_SummaryProvider -w {EASTL_TYPE_CATEGORY}"
    )
    debugger.HandleCommand(f"type category enable {EASTL_TYPE_CATEGORY}")
