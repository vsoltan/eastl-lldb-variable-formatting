from formatters.utils import (
    create_data_from_uint,
    find_type,
    get_non_synthetic_value,
)

class RefCountedPtrSyntheticProvider:
    SHARED_CHILDREN_NAMES = ("pointer", "use_count", "weak_count", "value")
    SHARED_CHILD_INDEX = {
        "pointer": 0,
        "use_count": 1,
        "weak_count": 2,
        "value": 3,
    }
    WEAK_CHILDREN_NAMES = ("pointer", "use_count", "weak_count", "expired", "value")
    WEAK_CHILD_INDEX = {
        "pointer": 0,
        "use_count": 1,
        "weak_count": 2,
        "expired": 3,
        "value": 4,
    }

    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self.value = None
        self._valid_layout = False
        self.ref_count_obj = None
        self._is_weak = False
        self._children_names = self.SHARED_CHILDREN_NAMES
        self._child_index = self.SHARED_CHILD_INDEX

    def get_child_index(self, name):
        return self._child_index.get(name, -1)

    def num_children(self):
        return len(self._children_names) if self._valid_layout else 0

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

    def _is_expired(self):
        return self._is_weak and self._get_use_count_value() == 0

    def _get_expired_child(self):
        return self.valobj.CreateValueFromData(
            "expired",
            create_data_from_uint(1 if self._is_expired() else 0, 1),
            find_type("bool"),
        )

    def _get_value_child(self):
        if self._is_expired():
            return None
        ptr = self.value.GetValueAsUnsigned(0)
        if ptr == 0:
            return None
        deref = self.value.Dereference()
        if not deref or not deref.IsValid():
            return None
        return self.valobj.CreateValueFromData("value", deref.GetData(), deref.GetType())

    def get_child_at_index(self, index):
        if not self._valid_layout or index < 0 or index >= len(self._children_names):
            return None

        child_name = self._children_names[index]
        if child_name == "pointer":
            return self._get_pointer_child()
        if child_name == "use_count":
            return self._get_use_count_child()
        if child_name == "weak_count":
            return self._get_weak_count_child()
        if child_name == "expired":
            return self._get_expired_child()
        if child_name == "value":
            return self._get_value_child()
        return None

    def update(self):
        type_name = self.valobj.GetTypeName() or ""
        self._is_weak = "weak_ptr<" in type_name
        if self._is_weak:
            self._children_names = self.WEAK_CHILDREN_NAMES
            self._child_index = self.WEAK_CHILD_INDEX
        else:
            self._children_names = self.SHARED_CHILDREN_NAMES
            self._child_index = self.SHARED_CHILD_INDEX

        self.value = self.valobj.GetChildMemberWithName("mpValue")
        self._valid_layout = bool(self.value and self.value.IsValid())
        self.ref_count_obj = None
        refcount_obj = self.valobj.GetChildMemberWithName("mpRefCount")
        if refcount_obj and refcount_obj.IsValid() and refcount_obj.GetValueAsUnsigned(0) != 0:
            self.ref_count_obj = refcount_obj.Dereference()

        return False


def shared_ptr_SummaryProvider(valobj, internal_dict):
    try:
        provider = RefCountedPtrSyntheticProvider(
            get_non_synthetic_value(valobj), internal_dict
        )
        provider.update()
        if not provider._valid_layout:
            return ""
        if provider.value.GetValueAsUnsigned(0) == 0:
            return "nullptr"
        return f"use_count={provider._get_use_count_value()}"
    except Exception:
        return ""


def WeakPtr_SummaryProvider(valobj, internal_dict):
    try:
        provider = RefCountedPtrSyntheticProvider(
            get_non_synthetic_value(valobj), internal_dict
        )
        provider.update()
        if not provider._valid_layout:
            return ""
        if provider._is_expired():
            return "expired"
        return f"use_count={provider._get_use_count_value()}"
    except Exception:
        return ""