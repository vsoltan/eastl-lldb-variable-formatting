from formatters.constants import (
    ARRAY_MAX_SIZE,
    ARRAY_MAX_SUMMARY_SIZE,
    TYPE_SIZE_T
)
from formatters.utils import (
    create_data_from_uint,
    find_type,
    get_value_display,
)

STATIC_SYNTHETIC_CHILDREN = {
    "size": 0
}

class Array_SyntheticChildrenProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj

    def update(self):
        self._values = self.valobj.GetChildMemberWithName("mValue")
        self._size = self._calculate_size()
        return False

    def num_children(self):
        return min(ARRAY_MAX_SIZE, self._size) + len(STATIC_SYNTHETIC_CHILDREN)

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
        return self._create_element_child(index)

    def _create_size_child(self, size):
        return self.valobj.CreateValueFromData(
            "size",
            create_data_from_uint(self._size),
            find_type(TYPE_SIZE_T)
        )
    
    def _create_element_child(self, index):
        actual_index = index - len(STATIC_SYNTHETIC_CHILDREN)
        value = self._values.GetChildAtIndex(actual_index)
        if not value or not value.IsValid():
            return None
        return self.valobj.CreateValueFromData(
            f"[{actual_index}]",
            value.GetData(),
            value.GetType(),
        )
    
    def _calculate_size(self):
        return self._values.GetNumChildren() if self._values and self._values.IsValid() else 0
        
def Array_SummaryProvider(valobj, internal_dict):
    size = valobj.GetChildAtIndex(STATIC_SYNTHETIC_CHILDREN.get("size")).GetValueAsUnsigned(0)
    elems = [ 
        get_value_display(valobj.GetChildAtIndex(i + len(STATIC_SYNTHETIC_CHILDREN))) 
        for i in range(min(size, ARRAY_MAX_SUMMARY_SIZE))
    ]
    if size > ARRAY_MAX_SUMMARY_SIZE:
        elems.append("...")
    if not elems:
        return f"[{size}] {{}}"
    return f"[{size}] {{ {', '.join(elems)} }}"