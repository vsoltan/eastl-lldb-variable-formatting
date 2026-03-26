from formatters.utils import (
    create_data_from_uint,
    find_type
)

class RefCountedPtrSyntheticChildrenProviderBase:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self.value = None
        self.valid_layout = False
        self.refcount = None

    def get_child_index(self, name):
        return self.STATIC_CHILD_INDEX.get(name, -1)

    def _count_type(self):
        count_type = find_type("int32_t")
        if count_type and count_type.IsValid():
            return count_type
        return find_type("int")

    def _read_atomic_count(self, atomic_value):
        if not atomic_value or not atomic_value.IsValid():
            return 0
        loaded = atomic_value.EvaluateExpression("load()")
        if loaded and loaded.IsValid() and loaded.GetError().Success():
            return loaded.GetValueAsUnsigned(0)
        nested = self._find_nested_child(atomic_value, "mAtomic", 0, 8)
        if nested and nested.IsValid():
            return nested.GetValueAsUnsigned(0)
        return atomic_value.GetValueAsUnsigned(0)

    def _find_nested_child(self, value, child_name, depth, max_depth):
        if depth > max_depth or not value or not value.IsValid():
            return None
        num_children = value.GetNumChildren()
        for idx in range(num_children):
            child = value.GetChildAtIndex(idx)
            if not child or not child.IsValid():
                continue
            if child.GetName() == child_name:
                return child
            found = self._find_nested_child(child, child_name, depth + 1, max_depth)
            if found and found.IsValid():
                return found
        return None

    def _get_pointer_child(self):
        return self.valobj.CreateValueFromData(
            "pointer", self.value.GetData(), self.value.GetType()
        )

    def _get_use_count_value(self):
        if not self.ref_count_obj or not self.ref_count_obj.IsValid():
            return 0
        return self._read_atomic_count(
            self.ref_count_obj.GetChildMemberWithName("mRefCount")
        )

    def _get_use_count_child(self):
        return self.valobj.CreateValueFromData(
            "use_count",
            create_data_from_uint(self._get_use_count_value(), 4),
            self._count_type(),
        )

    def _get_weak_count_value(self):
        if not self.ref_count_obj or not self.ref_count_obj.IsValid():
            return 0
        return self._read_atomic_count(
            self.ref_count_obj.GetChildMemberWithName("mWeakRefCount")
        )

    def _get_weak_count_child(self):
        return self.valobj.CreateValueFromData(
            "weak_count",
            create_data_from_uint(self._get_weak_count_value(), 4),
            self._count_type(),
        )

    def _get_value_child(self):
        ptr = self.value.GetValueAsUnsigned(0)
        if ptr == 0:
            return None
        deref = self.value.Dereference()
        if not deref or not deref.IsValid():
            return None
        return self.valobj.CreateValueFromData("value", deref.GetData(), deref.GetType())

    def update(self):
        self.value = self.valobj.GetChildMemberWithName("mpValue")
        self.valid_layout = self.value and self.value.IsValid()
        refcount_obj = self.valobj.GetChildMemberWithName("mpRefCount")
        if refcount_obj and refcount_obj.IsValid() and refcount_obj.GetValueAsUnsigned(0) != 0:
            self.refcount = refcount_obj.Dereference()
        
        return False