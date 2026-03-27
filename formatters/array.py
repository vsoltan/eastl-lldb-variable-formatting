from formatters.constants import ARRAY_MAX_SIZE
from formatters.utils import (
    create_data_from_uint,
    find_type,
    get_non_synthetic_value,
)

STATIC_SYNTHETIC_CHILDREN = {
    "size": 0
}

ARRAY_SUMMARY_MAX_ELEMENTS = 6

class Array_SyntheticProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self.values = None
        self.size = 0

    def update(self):
        self.values = self.valobj.GetChildMemberWithName("mValue")
        self.size = self.values.GetNumChildren() if self.values and self.values.IsValid() else 0
        return False

    def num_children(self):
        return min(ARRAY_MAX_SIZE, self.size) + len(STATIC_SYNTHETIC_CHILDREN)

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
            return self._create_size_child(self.size)
        return self._create_element_child(index)

    def _create_size_child(self, size):
        return self.valobj.CreateValueFromData(
            "size",
            create_data_from_uint(self.size),
            find_type("eastl_size_t")
        )
    
    def _create_element_child(self, index):
        actual_index = index - len(STATIC_SYNTHETIC_CHILDREN)
        value = self.values.GetChildAtIndex(actual_index)
        if not value or not value.IsValid():
            return None
        return self.valobj.CreateValueFromData(
            f"[{actual_index}]",
            value.GetData(),
            value.GetType(),
        )

def Array_SummaryProvider(valobj, internal_dict):
    try:
        state = get_non_synthetic_value(valobj)
        provider = Array_SyntheticProvider(state, internal_dict)
        provider.update()

        preview = []
        preview_count = min(provider.size, ARRAY_SUMMARY_MAX_ELEMENTS)
        for index in range(preview_count):
            value = provider.values.GetChildAtIndex(index)
            if not value or not value.IsValid():
                break

            display_value = value.GetSummary()
            if display_value is None:
                display_value = value.GetValue()
            if display_value is None:
                display_value = "?"
            preview.append(display_value)

        if provider.size > ARRAY_SUMMARY_MAX_ELEMENTS:
            preview.append("...")

        return f"[{provider.size}] {{ {', '.join(preview)} }}"
    except Exception:
        return ""
