import lldb
import lldb_utils

from constants import TYPE_CATEGORY

import logging

_size_cap = 200


class SyntheticProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj

    def num_children(self):
        self.cached_num_children = self.num_children_impl()
        global _size_cap
        if _size_cap is not None:
            return min(self.cached_num_children, _size_cap)
        return self.cached_num_children

    def get_child_index(self, name):
        if name.startswith("[") and name.endswith("]"):
            try:
                return int(name.lstrip("[").rstrip("]")) + 2
            except:
                return -1
        if name == "size":
            return 0
        if name == "capacity":
            return 1

    def get_child_at_index(self, index):
        if index not in range(0, self.cached_num_children):
            return None
        if index == 0:
            return self.valobj.CreateValueFromData(
                "size",
                lldb_utils.CreateDataFromUInt32(self.cached_num_children - 2),
                lldb_utils.FindType("eastl_size_t").GetTypedefedType(),
            )
        if index == 1:
            capacity = int(
                (self.capacity.GetValueAsUnsigned(0) - self.begin.GetValueAsUnsigned(0))
                / self.data_size
            )
            return self.valobj.CreateValueFromData(
                "capacity",
                lldb_utils.CreateDataFromUInt32(capacity),
                lldb_utils.FindType("eastl_size_t").GetTypedefedType(),
            )
        try:
            offset = (index - 2) * self.data_size
            return self.begin.CreateChildAtOffset(
                f"[{index - 2}]", offset, self.data_type
            )
        except:
            return None

    def update(self):
        try:
            self.begin = self.valobj.GetChildMemberWithName("mpBegin")
            self.end = self.valobj.GetChildMemberWithName("mpEnd")
            self.capacity = self.valobj.GetChildMemberWithName(
                "mCapacityAllocator"
            ).GetChildMemberWithName("mFirst")
            self.data_type = self.begin.GetType().GetPointeeType()
            self.data_size = self.data_type.GetByteSize()
        except Exception as e:
            logging.debug(e)
        return False

    def num_children_impl(self):
        try:
            begin_addr = self.begin.GetValueAsUnsigned(0)
            end_addr = self.end.GetValueAsUnsigned(0)
            capacity_addr = self.capacity.GetValueAsUnsigned(0)

            if begin_addr > end_addr:
                return 0
            if capacity_addr < end_addr:
                return 0
            byte_range = end_addr - begin_addr
            if byte_range % self.data_size != 0:
                return 0
            return int(byte_range / self.data_size) + 2
        except Exception as e:
            logging.debug(e)
            return 0


# TODO: fix this...
def SummaryProvider(valobj, internal_dict):
    try:
        synth_obj = SyntheticProvider(valobj, internal_dict)
        synth_obj.update()
        num_elements = synth_obj.num_children_impl() - 2
        print(num_elements)
        if num_elements < 0:  # uninitialized
            return ""
        return f"size={num_elements}"
    except Exception as e:
        logging.debug(e)
        return ""


def init(debugger: lldb.SBDebugger, internal_dict):
    type_regex = "^eastl::VectorBase<.*>$"
    debugger.HandleCommand(
        f"type summary add -x {type_regex} -e -F SummaryProvider -w {TYPE_CATEGORY}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x {type_regex} -C true -l SyntheticProvider -w {TYPE_CATEGORY}"
    )


def foo():
    print("hi")
