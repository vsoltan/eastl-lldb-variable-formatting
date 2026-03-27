
from formatters.utils import (
    get_value_display,
    get_non_synthetic_value
)

STATIC_SYNTHETIC_CHILDREN = {
    "first": 0,
    "second": 1
}

class pair_SyntheticChildrenProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
    
    def update(self):
        self.first = self.valobj.GetChildMemberWithName("first")
        self.second = self.valobj.GetChildMemberWithName("second")
        return False
    
    def num_children(self):
        return len(STATIC_SYNTHETIC_CHILDREN)
    
    def get_child_index(self, name):
        return STATIC_SYNTHETIC_CHILDREN.get(name, -1)
    
    def get_child_at_index(self, index):
        if (index >= len(STATIC_SYNTHETIC_CHILDREN)):
            return None
        if index == 0:
            return self.first
        if index == 1:
            return self.second

def pair_SummaryProvider(valobj, internal_dict):
    raw_valobj = get_non_synthetic_value(valobj)
    first = get_value_display(raw_valobj.GetChildMemberWithName("first"))
    second = get_value_display(raw_valobj.GetChildMemberWithName("second"))
    return f"({first}, {second})"