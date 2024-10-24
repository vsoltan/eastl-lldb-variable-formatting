import lldb


def SummaryProvider(valobj: lldb.SBValue, internal_dict):
    first_summary = valobj.GetChildMemberWithName("first")
    second_summary = valobj.GetChildMemberWithName("second")
    return f"({first_summary}, {second_summary})"


def __lldb_init_module(debugger: lldb.SBDebugger, internal_dict):
    debugger.HandleCommand(
        f"type summary add -x ^eastl::pair<.*>$ -F {__name__}.SummaryProvider -w EASTL"
    )
