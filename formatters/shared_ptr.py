from formatters.ref_counted_ptr import RefCountedPtrSyntheticChildrenProviderBase


class shared_ptr_SyntheticChildrenProvider(RefCountedPtrSyntheticChildrenProviderBase):
    STATIC_CHILDREN_NAMES = ("pointer", "use_count", "weak_count", "value")
    STATIC_CHILD_INDEX = {name: idx for idx, name in enumerate(STATIC_CHILD_NAMES)}
    STATIC_CHILD_COUNT = len(STATIC_CHILD_NAMES)

    def num_children(self):
        return self.STATIC_CHILD_COUNT if self._valid_layout else 0

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
            return self._get_value_child()
        return None

def shared_ptr_SummaryProvider(valobj, internal_dict):
    try:
        provider = shared_ptr_SyntheticChildrenProvider(valobj, internal_dict)
        provider.update()
        if not provider._valid_layout:
            return ""
        ptr = provider.mp_value.GetValueAsUnsigned(0)
        if ptr == 0:
            return "nullptr"
        use_count = provider._get_use_count_child().GetValueAsUnsigned(0)
        return f"use_count={use_count}"
    except Exception:
        return ""
