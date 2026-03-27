import re

from formatters.constants import SPAN_MAX_SIZE
from formatters.utils import create_data_from_uint, find_type, format_sequence_summary, get_value_display

class span_SyntheticChildrenProvider:
    STATIC_CHILD_NAMES = ("size",)
    STATIC_CHILD_INDEX = {name: idx for idx, name in enumerate(STATIC_CHILD_NAMES)}
    STATIC_CHILD_COUNT = len(STATIC_CHILD_NAMES)

    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self.size = 0
        self.data_ptr = None
        self.data_type = None
        self.data_size = 0

    def _static_extent_from_type_name(self):
        type_name = self.valobj.GetTypeName() or ""
        match = re.search(r"eastl::span<.*,\s*(-?\d+)\s*>", type_name)
        if not match:
            return None
        try:
            return int(match.group(1))
        except Exception:
            return None

    def _resolve_size(self):
        extent = self._static_extent_from_type_name()
        # EASTL dynamic extent may appear as size_t(-1) in type names.
        if extent == ((1 << 64) - 1):
            extent = None
        if extent is not None and extent >= 0:
            return extent
        storage = self.valobj.GetChildMemberWithName("mStorage")
        size_child = storage.GetChildMemberWithName("mnSize")
        if size_child and size_child.IsValid():
            return size_child.GetValueAsUnsigned(0)
        return 0

    def _build_size_child(self):
        return self.valobj.CreateValueFromData(
            "size", create_data_from_uint(self.size), find_type("eastl_size_t")
        )

    def num_children(self):
        return min(self.size, SPAN_MAX_SIZE) + self.STATIC_CHILD_COUNT

    def get_child_index(self, name):
        if name.startswith("[") and name.endswith("]"):
            try:
                return int(name.lstrip("[").rstrip("]")) + self.STATIC_CHILD_COUNT
            except Exception:
                return -1
        return self.STATIC_CHILD_INDEX.get(name, -1)

    def get_child_at_index(self, index):
        if index < 0 or index >= self.num_children():
            return None
        if index == 0:
            return self._build_size_child()

        element_index = index - self.STATIC_CHILD_COUNT
        if not self.data_ptr or not self.data_ptr.IsValid():
            return None
        if self.data_ptr.GetValueAsUnsigned(0) == 0:
            return None
        return self.data_ptr.CreateChildAtOffset(
            f"[{element_index}]",
            element_index * self.data_size,
            self.data_type,
        )

    def update(self):
        storage = self.valobj.GetChildMemberWithName("mStorage")
        self.data_ptr = storage.GetChildMemberWithName("mpData")
        self.data_type = self.data_ptr.GetType().GetPointeeType()
        self.data_size = self.data_type.GetByteSize() if self.data_type and self.data_type.IsValid() else 0
        self.size = self._resolve_size()
        return False


def span_SummaryProvider(valobj, internal_dict):
    try:
        raw_valobj = valobj.GetNonSyntheticValue()
        probe = raw_valobj if raw_valobj and raw_valobj.IsValid() else valobj
        provider = span_SyntheticChildrenProvider(probe, internal_dict)
        provider.update()
        preview = [
            get_value_display(provider.get_child_at_index(index + provider.STATIC_CHILD_COUNT))
            for index in range(min(provider.size, 6))
        ]
        return format_sequence_summary(provider.size, preview, truncated=provider.size > 6)
    except Exception:
        return ""
