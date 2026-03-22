from formatters.constants import ARRAY_MAX_SIZE
from formatters.utils import (
    create_data_from_uint,
    find_type,
    get_non_synthetic_value,
)

class Array_SyntheticProvider:
    STATIC_CHILDREN_NAMES = ("size",)

    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self.values = None
        self.size = 0

    def num_children(self):
        total_children = self.size + len(self.STATIC_CHILDREN_NAMES)
        return min(ARRAY_MAX_SIZE + len(self.STATIC_CHILDREN_NAMES), total_children)

    def get_child_index(self, name):
        if name.startswith("[") and name.endswith("]"):
            try:
                return int(name.lstrip("[").rstrip("]")) + len(self.STATIC_CHILDREN_NAMES)
            except Exception:
                return -1
        return self.STATIC_CHILDREN_NAMES.index(name)

    def get_child_at_index(self, index):
        if index < 0 or index >= self.num_children():
            return None
        if index == 0:
            return self.valobj.CreateValueFromData(
                "size",
                create_data_from_uint(self.size),
                find_type("eastl_size_t")
            )

        element_index = index - len(self.STATIC_CHILDREN_NAMES)
        if element_index >= self.size:
            return None
        value = self.values.GetChildAtIndex(element_index)
        if not value or not value.IsValid():
            return None
        return self.valobj.CreateValueFromData(
            f"[{element_index}]",
            value.GetData(),
            value.GetType(),
        )

    def update(self):
        self.values = self.valobj.GetChildMemberWithName("mValue")
        self.size = self.values.GetNumChildren() if self.values and self.values.IsValid() else 0
        return False

def Array_SummaryProvider(valobj, internal_dict):
    try:
        state = get_non_synthetic_value(valobj)
        provider = Array_SyntheticProvider(state, internal_dict)
        provider.update()
        size = provider.size
        return f"size={size}"
    except Exception:
        return ""
