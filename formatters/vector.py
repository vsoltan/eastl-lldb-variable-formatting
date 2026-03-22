from formatters.utils import (
    create_data_from_uint,
    find_type,
    get_non_synthetic_value,
)
from formatters.constants import VECTOR_MAX_SIZE

class VectorBase_SyntheticProvider:
    STATIC_CHILDREN_NAMES = [
        "size",
        "capacity",
    ]
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj

    def num_children(self):
        return self._num_children()

    def _num_children(self, apply_limit: bool = True):
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
            num_children = int(contiguous_bytes_length / self.data_size) + len(self.STATIC_CHILDREN_NAMES)

            if apply_limit and VECTOR_MAX_SIZE is not None:
                return min(VECTOR_MAX_SIZE + len(self.STATIC_CHILDREN_NAMES), num_children)
            return num_children
        except Exception:
            return 0

    def get_child_index(self, name):
        if name.startswith("[") and name.endswith("]"):
            try:
                return int(name.lstrip("[").rstrip("]")) + len(self.STATIC_CHILDREN_NAMES)
            except Exception:
                return -1
        return self.STATIC_CHILDREN_NAMES.index(name)

    def get_child_at_index(self, index):
        num_children = self._num_children(False)
        if index < 0 or index >= num_children:
            return None
        if index == 0:
            return self.valobj.CreateValueFromData(
                "size",
                create_data_from_uint(num_children - len(self.STATIC_CHILDREN_NAMES)),
                find_type("eastl_size_t"),
            )
        if index == 1:
            capacity = int(
                (self.capacity.GetValueAsUnsigned(0) - self.begin.GetValueAsUnsigned(0))
                / self.data_size
            )
            return self.valobj.CreateValueFromData(
                "capacity",
                create_data_from_uint(capacity),
                find_type("eastl_size_t"),
            )
        try:
            offset = (index - 2) * self.data_size
            return self.begin.CreateChildAtOffset(f"[{index - 2}]", offset, self.data_type)
        except Exception:
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
        # Trying to construct a synthetic provider using the synthetic valobj results in invalid state.
        rawValObj = get_non_synthetic_value(valobj)
        provider = VectorBase_SyntheticProvider(rawValObj, internal_dict)
        provider.update()
        num_elements = provider._num_children(False) - len(provider.STATIC_CHILDREN_NAMES)
        return f"size={num_elements}" if num_elements >= 0 else ""
    except Exception:
        return ""
