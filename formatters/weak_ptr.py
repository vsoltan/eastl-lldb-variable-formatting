from formatters.ref_counted_ptr import RefCountedPtrSyntheticChildrenProviderBase
from formatters.utils import (
    create_data_from_uint,
    find_type
)

class WeakPtr_SyntheticChildrenProvider(RefCountedPtrSyntheticChildrenProviderBase):
    STATIC_CHILDREN_NAMES = (
        "pointer", "use_count", "weak_count", "expired", "value"
    )

    def get_child_index(self, name):
        return self.STATIC_CHILDREN_NAMES.index(name)

    def _get_expired_child(self):
        expired = self._get_use_count_child().GetValueAsUnsigned(0) == 0
        return self.valobj.CreateValueFromData(
            "expired",
            create_data_from_uint(1 if expired else 0, 1),
            find_type("bool"),
        )

    def _get_value_child(self):
        if self._get_use_count_child().GetValueAsUnsigned(0) == 0:
            return None
        return super()._get_value_child()

    def get_child_at_index(self, index):
        if not self._valid_layout or index < 0 or index >= self.STATIC_CHILD_COUNT:
            return None
        if index == 0:
            return self._get_pointer_child()
        if index == 1:
            return self._get_use_count_child()
        if index == 2:
            return self._get_weak_count_child()
        if index == 3:
            return self._get_expired_child()
        if index == 4:
            return self._get_value_child()
        return None


def WeakPtr_SummaryProvider(valobj, internal_dict):
    try:
        provider = WeakPtr_SyntheticChildrenProvider(valobj, internal_dict)
        provider.update()
        if not provider._valid_layout:
            return ""
        use_count = provider._get_use_count_child().GetValueAsUnsigned(0)
        if use_count == 0:
            return "expired"
        return f"use_count={use_count}"
    except Exception:
        return ""
