from formatters.constants import VECTOR_MAX_SIZE
from formatters.utils import (
    create_data_from_uint,
    find_type,
    get_non_synthetic_value,
)

STATIC_SYNTHETIC_CHILDREN = {
    "size": 0,
    "capacity": 1
}

class VectorBase_SyntheticProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj

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

    def num_children(self):
        # limit the amount of synthetic children that are created by LLDB
        size = self._calculate_size()
        return min(VECTOR_MAX_SIZE, size) + len(STATIC_SYNTHETIC_CHILDREN)

    def get_child_index(self, name):
        if name.startswith("[") and name.endswith("]"):
            try:
                return int(name.lstrip("[").rstrip("]")) + len(STATIC_SYNTHETIC_CHILDREN)
            except Exception:
                return -1
        return STATIC_SYNTHETIC_CHILDREN.get(name, -1)

    def get_child_at_index(self, index):
        size = self._calculate_size()
        if index < 0 or index >= size + len(STATIC_SYNTHETIC_CHILDREN):
            return None
        if index == 0:
            return self._create_size_child(size)
        if index == 1:
            return self._create_capacity_child(self.__calculate_capacity())
        try:
            return self._create_element_child(index)
        except Exception:
            return None

    def _create_size_child(self, size):
        return self.valobj.CreateValueFromData(
            "size",
            create_data_from_uint(size),
            find_type("eastl_size_t"),
        )
    def _create_capacity_child(self, capacity):
        return self.valobj.CreateValueFromData(
            "capacity",
            create_data_from_uint(capacity),
            find_type("eastl_size_t"),
        )
    
    def _create_element_child(self, index):
        actual_index = index - len(STATIC_SYNTHETIC_CHILDREN)
        offset = actual_index * self.data_size
        return self.begin.CreateChildAtOffset(
            f"[{actual_index}]",
            offset,
            self.data_type
        )

    def _calculate_size(self):
        try:
            begin_addr = self.begin.GetValueAsUnsigned(0)
            end_addr = self.end.GetValueAsUnsigned(0)
            capacity_addr = self.capacity.GetValueAsUnsigned(0)

            if begin_addr > end_addr:
                return 0
            if capacity_addr < end_addr:
                return 0
            contiguous_bytes_length = end_addr - begin_addr
            if contiguous_bytes_length % self.data_size != 0:
                return 0
            return int(contiguous_bytes_length / self.data_size)
        except Exception:
            return 0
        
    def __calculate_capacity(self):
        return int((self.capacity.GetValueAsUnsigned(0) - self.begin.GetValueAsUnsigned(0)) / self.data_size)

def VectorBase_SummaryProvider(valobj, internal_dict):
    try:
        # Trying to construct a synthetic provider using the synthetic valobj results in invalid state.
        rawValObj = get_non_synthetic_value(valobj)
        provider = VectorBase_SyntheticProvider(rawValObj, internal_dict)
        provider.update()
        size = provider._calculate_size()
        return f"size={size}" if size >= 0 else ""
    except Exception:
        return ""
