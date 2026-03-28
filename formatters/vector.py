from formatters.constants import (
    VECTOR_MAX_SIZE,
    VECTOR_MAX_SUMMARY_SIZE,
    TYPE_SIZE_T
)
from formatters.utils import (
    create_data_from_uint,
    find_type,
    get_value_display,
)

STATIC_SYNTHETIC_CHILDREN = {
    "size": 0,
    "capacity": 1
}

class VectorBase_SyntheticChildrenProvider:
    def __init__(self, valobj, internal_dict):
        self._valobj = valobj

    def update(self):
        try:
            self._begin_addr = self._valobj.GetChildMemberWithName("mpBegin")
            self._end_addr = self._valobj.GetChildMemberWithName("mpEnd")
            self._capacity_addr = self._valobj.GetChildMemberWithName(
                "mCapacityAllocator"
            ).GetChildMemberWithName("mFirst")
            self._data_type = self._begin_addr.GetType().GetPointeeType()
            self._data_size = self._data_type.GetByteSize()
            self._size = self._calculate_size()
            self._capacity = self._calculate_capacity()
            
        except Exception as e:
            print(e)
        return False

    def num_children(self):
        return min(VECTOR_MAX_SIZE, self._size) + len(STATIC_SYNTHETIC_CHILDREN)

    def get_child_index(self, name):
        if name.startswith("[") and name.endswith("]"):
            try:
                return int(name.lstrip("[").rstrip("]")) + len(STATIC_SYNTHETIC_CHILDREN)
            except Exception:
                return -1
        return STATIC_SYNTHETIC_CHILDREN.get(name, -1)

    def get_child_at_index(self, index):
        if index < 0 or index >= self.num_children():
            return None
        if index == 0:
            return self._create_size_child(self._size)
        if index == 1:
            return self._create_capacity_child(self._capacity)
        try:
            return self._create_element_child(index)
        except Exception:
            return None

    def _create_size_child(self, size):
        return self._valobj.CreateValueFromData(
            "size",
            create_data_from_uint(size),
            find_type(TYPE_SIZE_T),
        )

    def _create_capacity_child(self, capacity):
        return self._valobj.CreateValueFromData(
            "capacity",
            create_data_from_uint(capacity),
            find_type(TYPE_SIZE_T),
        )
    
    def _create_element_child(self, index):
        actual_index = index - len(STATIC_SYNTHETIC_CHILDREN)
        offset = actual_index * self._data_size
        return self._begin_addr.CreateChildAtOffset(
            f"[{actual_index}]",
            offset,
            self._data_type
        )

    def _calculate_size(self):
        try:
            begin_addr = self._begin_addr.GetValueAsUnsigned(0)
            end_addr = self._end_addr.GetValueAsUnsigned(0)
            capacity_addr = self._capacity_addr.GetValueAsUnsigned(0)

            if begin_addr >= end_addr:
                return 0
            if capacity_addr < end_addr:
                return 0
            contiguous_bytes_length = end_addr - begin_addr
            if contiguous_bytes_length % self._data_size != 0:
                return 0
            return int(contiguous_bytes_length / self._data_size)
        except Exception:
            return 0
        
    def _calculate_capacity(self):
        try:
            begin_addr = self._begin_addr.GetValueAsUnsigned(0)
            capacity_addr = self._capacity_addr.GetValueAsUnsigned(0)

            if capacity_addr < begin_addr:
                return 0
            contiguous_bytes_length = capacity_addr - begin_addr
            if contiguous_bytes_length % self._data_size != 0:
                return 0
            return int((capacity_addr - begin_addr) / self._data_size)
        except Exception:
            return 0

def VectorBase_SummaryProvider(valobj, internal_dict):
    size = valobj.GetChildAtIndex(STATIC_SYNTHETIC_CHILDREN.get("size")).GetValueAsUnsigned(0)
    elems = [ 
        get_value_display(valobj.GetChildAtIndex(i + len(STATIC_SYNTHETIC_CHILDREN))) 
        for i in range(min(size, VECTOR_MAX_SUMMARY_SIZE))
    ]
    if size > VECTOR_MAX_SUMMARY_SIZE:
        elems.append("...")
    if not elems:
        return f"[{size}] {{}}"
    return f"[{size}] {{ {', '.join(elems)} }}"
