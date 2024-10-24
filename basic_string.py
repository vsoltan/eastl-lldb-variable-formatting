import lldb
import lldb_utils

import logging

logger = logging.getLogger(__name__)


class SyntheticChildrenProvider:
    def is_heap(self) -> bool:
        return self.uses_heap().GetValueAsUnsigned() != 0

    def calculate_length(self) -> int:
        try:
            if self.is_heap():
                return self.valobj.EvaluateExpression(
                    "internalLayout().heap.mnSize"
                ).GetValueAsUnsigned()
            return (
                # TODO: fix
                self.calculate_capacity()
                - self.valobj.EvaluateExpression("").GetValueAsUnsigned()
            )
        except Exception as e:
            logger.error(e)
            return 0

    def get_length(self) -> lldb.SBValue:
        return self.valobj.CreateValueFromData(
            "length",
            lldb_utils.CreateDataFromUInt32(self.calculate_length()),
            lldb_utils.FindType("eastl_size_t"),
        )

    def calculate_capacity(self) -> int:
        try:
            if self.uses_heap().GetValueAsUnsigned():
                return self.valobj.EvaluateExpression(
                    "internalLayout().GetHeapCapacity()"
                ).GetValueAsUnsigned()
            else:
                return int(
                    (
                        lldb_utils.FindType("HeapLayout").GetByteSize()
                        - lldb_utils.FindType("char").GetByteSize()
                    )
                    / self.value_type.GetByteSize()
                )
        except Exception as e:
            logger.error(e)
            return 0

    def get_capacity(self) -> lldb.SBValue:
        return self.valobj.CreateValueFromData(
            "capacity",
            lldb_utils.CreateDataFromUInt32(self.calculate_capacity()),
            lldb_utils.FindType("eastl_size_t"),
        )

        return lldb.SBValue()

    def get_value(self) -> lldb.SBValue:
        return lldb.SBValue()

    #     try:
    #         str_len = self.calculate_length()
    #         if self.is_sso():
    #             string_value = self.sso_buffer.GetChildMemberWithName("mData")
    #             element_type = string_value.GetType().GetArrayElementType()
    #             return self.valobj.CreateValueFromData(
    #                 "value", string_value.GetData(), element_type.GetArrayType(str_len)
    #             )
    #         else:
    #             logger.error("Heap strings not supported yet")
    #             return None
    #     except Exception as e:
    #         logger.debug(e)
    #         message = "Error reading characters of string"
    #         return self.valobj.CreateValueFromData(
    #             "value",
    #             lldb_utils.CreateDataFromCString(message),
    #             lldb_utils.FindType("char").GetArrayType(len(message) + 1),
    #         )

    def uses_heap(self) -> lldb.SBValue:
        return self.valobj.EvaluateExpression("internalLayout().IsHeap()")

    def __init__(self, valobj, internal_dict):
        self.valobj = valobj

    def num_children(self):
        return 4

    def get_child_index(self, name):
        if name == "length":
            return 0
        if name == "capacity":
            return 1
        if name == "uses_heap":
            return 2
        if name == "value":
            return 3
        else:
            return -1

    def get_child_at_index(self, index):
        if index == 0:
            return self.get_length()
        if index == 1:
            return self.get_capacity()
        if index == 2:
            return self.uses_heap()
        if index == 3:
            return self.get_value()
        else:
            return None

    def update(self):
        string_data = self.valobj.GetChildMemberWithName(
            "mPair"
        ).GetChildMemberWithName("mFirst")
        self.sso_buffer = string_data.GetChildMemberWithName("sso")
        self.heap_buffer = string_data.GetChildMemberWithName("heap")
        self.value_type = self.valobj.GetType().GetTemplateArgumentType(0)
        return False


def __lldb_init_module(debugger: lldb.SBDebugger, internal_dict):
    type_regex = "^eastl::basic_string<.*>$"
    debugger.HandleCommand(
        f"type synthetic add -prx {type_regex} -C true -l {__name__}.SyntheticChildrenProvider -w EASTL"
    )
