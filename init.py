import lldb

from constants import TYPE_CATEGORY

import vector_base


def __lldb_init_module(debugger: lldb.SBDebugger, internal_dict):
    # When debugging, run this command so that formatters are properly replaced instead of appended
    debugger.HandleCommand(f"type category delete {TYPE_CATEGORY}")
    vector_base.init(debugger, internal_dict)
    debugger.HandleCommand(f"type category enable {TYPE_CATEGORY}")
