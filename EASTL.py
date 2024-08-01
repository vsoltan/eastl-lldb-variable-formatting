import lldb

type_category = "EASTL"


def GetSystemByteOrder():
    return lldb.debugger.GetSelectedTarget().GetByteOrder()


def CreateDataFromUInt32(value: int) -> lldb.SBData:
    addr_byte_size = lldb.debugger.GetSelectedTarget().GetAddressByteSize()
    return lldb.SBData.CreateDataFromUInt32Array(
        GetSystemByteOrder(), addr_byte_size, [value]
    )


def CreateDataFromCString(value: str) -> lldb.SBData:
    addr_byte_size = lldb.debugger.GetSelectedTarget().GetAddressByteSize()
    return lldb.SBData.CreateDataFromCString(
        GetSystemByteOrder(), addr_byte_size, value
    )


def FindType(type_name: str) -> lldb.SBType:
    return lldb.debugger.GetSelectedTarget().FindFirstType(type_name)


def pair_SummaryProvider(valobj, internal_dict):
    first_summary = valobj.GetChildMemberWithName("first")
    second_summary = valobj.GetChildMemberWithName("second")
    return f"({first_summary}, {second_summary})"


class VectorBase_SyntheticProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj

    def num_children(self):
        return self.get_num_children_impl()

    def get_num_children_impl(self, apply_limit: bool = True):
        try:
            begin_addr = self.begin.GetValueAsUnsigned(0)
            end_addr = self.end.GetValueAsUnsigned(0)
            capacity_addr = self.capacity.GetValueAsUnsigned(0)

            if begin_addr > end_addr:
                return 0
            if capacity_addr < end_addr:
                return 0
            num_children = end_addr - begin_addr
            if num_children % self.data_size != 0:
                return 0
            num_children = int(num_children / self.data_size) + 2

            global _vector_capping_size
            if apply_limit and _vector_capping_size is not None:
                return min(_vector_capping_size + 2, num_children)
            return num_children
        except Exception:
            return 0

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
        num_children = self.get_num_children_impl(False)
        if index < 0 or index >= num_children:
            return None
        if index == 0:
            return self.valobj.CreateValueFromData(
                "size",
                CreateDataFromUInt32(num_children - 2),
                FindType("eastl_size_t"),
            )
        if index == 1:
            capacity = int(
                (self.capacity.GetValueAsUnsigned(0) - self.begin.GetValueAsUnsigned(0))
                / self.data_size
            )
            return self.valobj.CreateValueFromData(
                "capacity",
                CreateDataFromUInt32(capacity),
                FindType("eastl_size_t"),
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
            print(e)
        return False


def VectorBase_SummaryProvider(valobj, internal_dict):
    try:
        num_elements = valobj.GetNumChildren() - 2
        if num_elements < 0:  # uninitialized
            return ""
        return f"size={num_elements}"
    except Exception:
        return ""


class basic_string_SyntheticProvider:
    def get_length(self) -> lldb.SBValue:
        return self.valobj.CreateValueFromExpression(
            "length", f"{self.valobj.GetName()}.internalLayout.GetSize()"
        )

    def get_capacity(self) -> lldb.SBValue:
        return self.valobj.CreateValueFromExpression(
            "capacity", f"{self.valobj.GetName()}.capacity()"
        )

    def get_value(self) -> lldb.SBValue:
        # TODO: cast this to an array type for better viewing of the string buffer data
        return self.valobj.CreateValueFromExpression(
            "value", f"{self.valobj.GetName()}.internalLayout().BeginPtr()"
        )

    def get_uses_heap(self) -> lldb.SBValue:
        return self.valobj.CreateValueFromExpression(
            "uses_heap", f"{self.valobj.GetName()}.internalLayout().IsHeap()"
        )

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
            return self.get_uses_heap()
        if index == 3:
            return self.get_value()
        else:
            return None

    def update(self):
        return False


# class shared_ptr_SyntheticProvider:
#     def __init__(self, valobj, internal_dict):
#         self.valobj = valobj

#     def num_children(self):
#         return 3

#     def get_child_index(self, name):
#         if name == "pointer":
#             return 0
#         elif name == "reference count":
#             return 1
#         elif name == "weak reference count":
#             return 2
#         else:
#             return -1

#     def get_child_at_index(self, index):
#         if index == 0:
#             pointer_value = self.valobj.CreateValueFromExpression(
#                 "pointer", f"{self.valobj.GetName()}.mpValue"
#             )
#             # prevent recursive formatting shared_ptr<T>::value_type
#             return pointer_value.Cast(
#                 pointer_value.GetType()
#                 .GetPointeeType()
#                 .GetTypedefedType()
#                 .GetPointerType()
#             )
#         if index == 1:
#             # TODO: use use_count instead
#             return self.valobj.CreateValueFromExpression(
#                 "reference count", f"{self.valobj.GetName()}.mpRefCount.mRefCount"
#             )
#         if index == 2:
#             # TODO: use
#             print(
#                 self.valobj.CreateValueFromExpression(
#                     "weak reference count", f"{self.valobj.GetName()}.mpRefCount.mWeakRefCount"
#                 )
#             )
#             return self.valobj.CreateValueFromExpression(
#                 "weak reference count", f"{self.valobj.GetName()}.mpRefCount "
#             )
#         else:
#             return None

#     def update(self):
#         try:
#             self.pointer = self.valobj.EvaluateExpression("mpValue")
#             self.value = self.valobj.EvaluateExpression("*mpValue")
#         except Exception as e:
#             print(e)
#         return False


"""
class UniquePtrSyntheticProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj

    def num_children(self):
        return 2

    def get_child_index(self, name):
        if name == 'pointer':
            return 0
        elif name == 'value':
            return 1
        else:
            return -1

    def get_child_at_index(self, index):
        if index == 0:
            if self.pointer.GetData() is None:
                return self.valobj.CreateValueFromData('pointer', lldb.SBData(), self.pointer.GetType())
            else:
                return self.valobj.CreateValueFromData('pointer', self.pointer.GetData(), self.pointer.GetType())
        if index == 1:
            if self.value.GetData() is None:
                return self.valobj.CreateValueFromData('value', lldb.SBData(), self.value.GetType())
            else:
                return self.valobj.CreateValueFromData('value', self.value.GetData(), self.value.GetType())
        else:
            return None

    def update(self):
        self.pointer = self.valobj.EvaluateExpression('mPair.mFirst')
        self.value = self.pointer.Dereference()
        return False

def UniquePtrSummaryProvider(valobj, internal_dict):
    pointer = valobj.EvaluateExpression('mPair.mFirst')
    print('pointer', pointer)
    if pointer.GetValue() is None:
        return 'nullptr'
    else:
        value = pointer.Dereference().GetValue()
        print('value', value)
        return 'nullptr' if value is None else value
"""

# NOTE: SBValue already has EvaluateExpression which doesn't seem to work
# def get_child_member_with_path(valobj: SBValue, path: list[str]):
#     result = valobj
#     try:
#         for name in path:
#             result = result.GetChildMemberWithName(name)
#             if valobj.GetValue() is None:
#                 return None
#     except Exception as e:
#         print(e)
#         return None


def __lldb_init_module(debugger, internal_dict):
    # When debugging, run this command so that formatters are properly replaced instead of appended
    debugger.HandleCommand(f"type category delete {type_category}")

    debugger.HandleCommand(
        f"type summary add -x ^eastl::pair<.*>$ -F EASTL.pair_SummaryProvider -w {type_category}"
    )

    debugger.HandleCommand(
        f"type synthetic add -prx ^eastl::basic_string<.*>$ -C true -l EASTL.basic_string_SyntheticProvider -w {type_category}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::VectorBase<.*>$ -C true -l EASTL.VectorBase_SyntheticProvider -w {type_category}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::VectorBase<.*>$ -e -F EASTL.VectorBase_SummaryProvider -w {type_category}"
    )
    # debugger.HandleCommand(
    # f"type synthetic add -x ^eastl::shared_ptr<.*>$ -C true -l EASTL.shared_ptr_SyntheticProvider -w {type_category}"
    # )
    debugger.HandleCommand(f"type category enable {type_category}")
    return


_vector_capping_size = 200
