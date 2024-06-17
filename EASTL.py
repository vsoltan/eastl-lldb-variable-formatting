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


class basic_string_SyntheticChildrenProvider:
    # We could get SSO_CAPACITY using GetStaticFieldWithName if we were able to use a more up-to-date version of lldb
    # XCode insists on using the python that ships with the OS as well as the LLDB framework that was built with it
    # https://lldb.llvm.org/python_api/lldb.SBType.html#lldb.SBType.GetStaticFieldWithName
    # Until a newer version ships with MacOS, we reimplement the logic here for now
    def get_sso_capacity(self) -> int:
        try:
            return int(
                (FindType("HeapLayout").GetByteSize() - FindType("char").GetByteSize())
                / self.value_type.GetByteSize()
            )
        except Exception:
            return 0

    # I could not figure out a way to get this from the binary image, might be inlined by the compiler...
    def get_sso_mask(self) -> int:
        byte_order = GetSystemByteOrder()
        if byte_order == lldb.eByteOrderLittle:
            return 0x80
        elif byte_order == lldb.eByteOrderBig:
            return 0x1
        print("error: unrecognized byte ordering. Not little or big endian")
        return 0x0

    def is_sso(self) -> bool:
        return not self.is_heap()

    def is_heap(self) -> bool:
        remaining_size = self.sso_buffer.GetChildMemberWithName(
            "mRemainingSizeField"
        ).GetChildMemberWithName("mnRemainingSize")
        return not not (remaining_size.GetValueAsUnsigned() & self.get_sso_mask())

    def get_heap_mask(self) -> int:
        byte_order = GetSystemByteOrder()
        if byte_order == lldb.eByteOrderLittle:
            # TODO: actually implement this properly ~(size_type(~size_type(0)) >> 1)
            return 0x8000000000000000
        elif byte_order == lldb.eByteOrderBig:
            return 0x1
        else:
            print("error: unrecognized byte ordering. Not little or big endian")
            return 0x0

    def calculate_length(self) -> int:
        if self.is_sso():
            length_value = self.sso_buffer.GetChildMemberWithName(
                "mRemainingSizeField"
            ).GetChildMemberWithName("mnRemainingSize")
            return self.get_sso_capacity() - length_value.GetValueAsUnsigned()
        else:
            # heap_len = self.heap_buffer.GetChildMemberWithName('mnSize')
            # return self.valobj.CreateValueFromData('length',  heap_len.GetData(), length_type)
            return 0

    def calculate_capacity(self) -> int:
        if self.is_sso():
            return self.get_sso_capacity()
        else:
            return 0
            # TODO: account for mask
            # heap_capacity = self.heap_buffer.GetChildMemberWithName('mnCapacity')
            # return self.valobj.CreateValueFromData('capacity', heap_capacity.GetData(), capacity_type)

    def get_length(self) -> lldb.SBValue:
        length_type = FindType("size_type").GetTypedefedType()
        return self.valobj.CreateValueFromData(
            "length", CreateDataFromUInt32(self.calculate_length()), length_type
        )

    def get_capacity(self) -> lldb.SBValue:
        capacity_type = FindType("size_type").GetTypedefedType()
        return self.valobj.CreateValueFromData(
            "capacity", CreateDataFromUInt32(self.calculate_capacity()), capacity_type
        )

    def get_value(self) -> lldb.SBValue:
        print("callced get_value")
        try:
            str_len = self.calculate_length()
            print("str_len", str_len)
            if self.is_sso():
                string_value = self.sso_buffer.GetChildMemberWithName("mData")
                element_type = string_value.GetType().GetArrayElementType()
                return self.valobj.CreateValueFromData(
                    "value", string_value.GetData(), element_type.GetArrayType(str_len)
                )
            else:
                print("oi?")
                return None
        except Exception as e:
            print("get_value exception", e)
            print("get_value", e)
            message = "Error reading characters of string"
            return self.valobj.CreateValueFromData(
                "value",
                CreateDataFromCString(message),
                FindType("char").GetArrayType(len(message) + 1),
            )

    def get_uses_heap(self) -> lldb.SBValue:
        return self.valobj.CreateValueFromData(
            "uses_heap",
            CreateDataFromUInt32(1 if self.is_heap() else 0),
            FindType("bool"),
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
        string_data = self.valobj.GetChildMemberWithName(
            "mPair"
        ).GetChildMemberWithName("mFirst")
        self.sso_buffer = string_data.GetChildMemberWithName("sso")
        self.heap_buffer = string_data.GetChildMemberWithName("heap")
        self.value_type = self.valobj.GetType().GetTemplateArgumentType(0)

        # if self.valobj.GetType().IsPointerType():
        #     self.value_type = self.valobj.GetPointeeType().GetTemplateArgumentType(0)
        return False


"""
class shared_ptr_SyntheticChildrenProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj

    def num_children(self):
        return 2

    def get_child_index(self, name):
        print('from get_child_index', name)
        if name == 'pointer':
            return 0
        elif name == 'value':
            return 1
        else:
            return -1

    def get_child_at_index(self, index):
        if index == 0:
            return self.valobj.CreateValueFromData('pointer', self.pointer.GetData(), self.pointer.GetType())
        if index == 1:
            return self.valobj.CreateValueFromData('value', self.value.GetData(), self.value.GetType())
        else:
            return None

    def update(self):
        try:
            self.pointer = self.valobj.EvaluateExpression('mpValue')
            self.value = self.valobj.EvaluateExpression('*mpValue')
        except Exception as e:
            print(e)
        return False
"""


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


# TODO: fix
# def CreateDataFromString(value: str):
#     return lldb.SBData.CreateDataFromCString(GetSystemByteOrder(), len(value), value)


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand(
        f"type summary add -x ^eastl::pair<.*> -F EASTL.pair_SummaryProvider -w {type_category}"
    )

    debugger.HandleCommand(
        f"type synthetic add -prx ^eastl::basic_string<char>$ -l EASTL.basic_string_SyntheticChildrenProvider -w {type_category}"
    )
    debugger.HandleCommand(
        f"type synthetic add -x ^eastl::VectorBase<.*> -C true -l EASTL.VectorBase_SyntheticProvider -w {type_category}"
    )
    debugger.HandleCommand(
        f"type summary add -x ^eastl::VectorBase<.*> -e -F EASTL.VectorBase_SummaryProvider -w {type_category}"
    )
    # debugger.HandleCommand(f'type synthetic add -x ^eastl::unique_ptr<.+> >$ --python-class EASTL.UniquePtrSyntheticProvider -w {type_category}')
    debugger.HandleCommand(f"type category enable {type_category}")
    return


_vector_capping_size = 200
