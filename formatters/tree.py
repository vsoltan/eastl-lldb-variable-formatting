from formatters.constants import TREE_MAX_SIZE
from formatters.utils import create_data_from_uint, find_type, format_sequence_summary, get_value_display, get_non_synthetic_value


class RBTree_SyntheticChildrenProvider:
    STATIC_CHILD_NAMES = ("size",)
    STATIC_CHILD_INDEX = {name: idx for idx, name in enumerate(STATIC_CHILD_NAMES)}
    STATIC_CHILD_COUNT = len(STATIC_CHILD_NAMES)

    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self.size = 0
        self.anchor = None
        self.anchor_addr = 0
        self.leftmost_addr = 0
        self.node_base_type = None
        self.node_ptr_type = None

    def _get_node_base_value(self, addr):
        if addr == 0 or not self.node_base_type or not self.node_base_type.IsValid():
            return None
        return self.valobj.CreateValueFromAddress(
            "__eastl_tree_node_base", addr, self.node_base_type
        )

    def _get_node_ptr(self, node_base):
        if not node_base or not node_base.IsValid():
            return (0, 0, 0)
        left = node_base.GetChildMemberWithName("mpNodeLeft").GetValueAsUnsigned(0)
        right = node_base.GetChildMemberWithName("mpNodeRight").GetValueAsUnsigned(0)
        parent = node_base.GetChildMemberWithName("mpNodeParent").GetValueAsUnsigned(0)
        return (left, right, parent)

    def _tree_increment(self, node_addr):
        if node_addr == 0:
            return 0
        node = self._get_node_base_value(node_addr)
        if not node:
            return 0

        (_, right, _) = self._get_node_ptr(node)
        if right != 0:
            current = right
            while current != 0:
                current_node = self._get_node_base_value(current)
                if not current_node:
                    return 0
                left, _, _ = self._get_node_ptr(current_node)
                if left == 0:
                    return current
                current = left
            return 0

        current = node_addr
        _, _, parent = self._get_node_ptr(node)
        while parent != 0 and parent != self.anchor_addr:
            parent_node = self._get_node_base_value(parent)
            if not parent_node:
                return 0
            _, parent_right, _ = self._get_node_ptr(parent_node)
            if parent_right != current:
                return parent
            current = parent
            _, _, parent = self._get_node_ptr(parent_node)

        return 0

    def _resolve_node_ptr_type(self):
        expressions = (
            "(node_type*)mAnchor.mpNodeParent",
            "(decltype(*this)::node_type*)mAnchor.mpNodeParent",
        )
        for expr in expressions:
            probe = self.valobj.EvaluateExpression(expr)
            if probe and probe.IsValid():
                t = probe.GetType()
                if t and t.IsValid() and t.IsPointerType():
                    return t
        return None

    def _build_size_child(self):
        return self.valobj.CreateValueFromData(
            "size", create_data_from_uint(self.size), find_type("eastl_size_t")
        )

    def _build_element_child(self, index):
        node_addr = self.leftmost_addr
        for _ in range(index):
            node_addr = self._tree_increment(node_addr)
            if node_addr == 0:
                return None

        if not self.node_ptr_type or not self.node_ptr_type.IsValid():
            node_base = self._get_node_base_value(node_addr)
            if node_base and node_base.IsValid():
                return self.valobj.CreateValueFromData(
                    f"[{index}]", node_base.GetData(), node_base.GetType()
                )
            return None

        node_value = self.valobj.CreateValueFromAddress(
            "__eastl_tree_node", node_addr, self.node_ptr_type.GetPointeeType()
        )
        if not node_value or not node_value.IsValid():
            return None
        value = node_value.GetChildMemberWithName("mValue")
        if value and value.IsValid():
            value_addr = value.AddressOf().GetValueAsUnsigned(0)
            return self.valobj.CreateValueFromAddress(f"[{index}]", value_addr, value.GetType())
        return None

    def num_children(self):
        return min(TREE_MAX_SIZE, self.size) + self.STATIC_CHILD_COUNT

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
        return self._build_element_child(index - self.STATIC_CHILD_COUNT)

    def update(self):
        self.anchor = self.valobj.GetChildMemberWithName("mAnchor")
        self.size = self.valobj.GetChildMemberWithName("mnSize").GetValueAsUnsigned(0)
        self.anchor_addr = self.anchor.AddressOf().GetValueAsUnsigned(0)
        self.leftmost_addr = self.anchor.GetChildMemberWithName("mpNodeLeft").GetValueAsUnsigned(
            0
        )
        self.node_base_type = self.anchor.GetType()
        self.node_ptr_type = self._resolve_node_ptr_type()
        return False


def RBTree_SummaryProvider(valobj, internal_dict):
    try:
        provider = RBTree_SyntheticChildrenProvider(get_non_synthetic_value(valobj), internal_dict)
        provider.update()
        preview = []
        if provider.size > 0:
            preview.append(get_value_display(provider._build_element_child(0)))
        return format_sequence_summary(provider.size, preview, truncated=provider.size > 1)
    except Exception:
        return ""
