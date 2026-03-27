class unique_ptr_SyntheticChildrenProvider:
    STATIC_SYNTHETIC_CHILDREN = {
        "pointer" : 0,
        "value" : 1,
    }

    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self.pointer = None

    def num_children(self):
        return len(self.STATIC_SYNTHETIC_CHILDREN) if self.pointer and self.pointer.IsValid() else 0

    def get_child_index(self, name):
        return self.STATIC_SYNTHETIC_CHILDREN.get(name, -1)
    
    def get_child_at_index(self, index):
        if index == 0:
            return self._get_pointer_child()
        if index == 1:
            return self._get_value_child()
        return None

    def update(self):
        pair = self.valobj.GetChildMemberWithName("mPair")
        self.pointer = pair.GetChildMemberWithName("mFirst")
        return False

    def _get_pointer_child(self):
        return self.valobj.CreateValueFromData(
            "pointer", self.pointer.GetData(), self.pointer.GetType()
        )

    def _get_value_child(self):
        ptr = self.pointer.GetValueAsUnsigned(0)
        if ptr == 0:
            return None
        value = self.pointer.Dereference()
        if not value or not value.IsValid():
            return None
        return self.valobj.CreateValueFromData("value", value.GetData(), value.GetType())

    


def unique_ptr_SummaryProvider(valobj, internal_dict):
    try:
        provider = unique_ptr_SyntheticChildrenProvider(valobj, internal_dict)
        provider.update()
        if not provider.pointer or not provider.pointer.IsValid():
            return ""
        if provider.pointer.GetValueAsUnsigned(0) == 0:
            return "nullptr"
        value = provider._get_value_child()
        if value and value.IsValid():
            summary = value.GetSummary() or value.GetValue()
            if summary:
                return summary
        return ""
    except Exception:
        return ""
