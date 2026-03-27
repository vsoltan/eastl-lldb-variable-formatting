import lldb

from formatters.constants import STRING_MAX_SIZE
from formatters.utils import (
    create_data_from_cstring,
    create_data_from_uint,
    find_type,
    get_system_byte_order,
)

class basic_string_SyntheticChildrenProvider:
    SYNTHETIC_CHILDREN_NAMES = [
        "length",
        "capacity",
        "uses_heap",
        "value",
    ]
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self._valid_layout = False
        self._runtime_state_valid = False

    def _size_type_bits(self) -> int:
        return self.size_type.GetByteSize() * 8

    def _get_sso_capacity(self) -> int:
        try:
            return int(self.sso_data.GetType().GetByteSize() / self.value_type.GetByteSize())
        except Exception:
            return 0

    def _get_sso_mask(self) -> int:
        byte_order = get_system_byte_order()
        if byte_order == lldb.eByteOrderBig:
            return 0x1
        return 0x80

    def _remaining_size_field_raw(self) -> int:
        return self.remaining_size_field.GetValueAsUnsigned(0) & 0xFF

    def is_heap(self) -> bool:
        return bool(self._remaining_size_field_raw() & self._get_sso_mask())

    def is_sso(self) -> bool:
        return not self.is_heap()

    def _decode_sso_remaining_capacity(self) -> int:
        raw = self._remaining_size_field_raw()
        if get_system_byte_order() == lldb.eByteOrderBig:
            return raw >> 2
        return raw

    def _decode_heap_capacity(self) -> int:
        encoded_capacity = self.heap_capacity.GetValueAsUnsigned(0)
        if get_system_byte_order() == lldb.eByteOrderBig:
            return encoded_capacity >> 1

        bits = self._size_type_bits()
        if bits <= 1:
            return 0
        heap_mask = 1 << (bits - 1)
        return encoded_capacity & ~heap_mask

    def _read_element_at(self, base_addr: int, index: int):
        try:
            if base_addr == 0 or index < 0:
                return None
            value = self.valobj.CreateValueFromAddress(
                "__eastl_str_probe", base_addr, self.value_type.GetArrayType(index + 1)
            ).GetChildAtIndex(index)
            if not value or not value.IsValid():
                return None
            return value.GetValueAsUnsigned(0)
        except Exception:
            return None

    def _has_terminator(self, base_addr: int, length: int) -> bool:
        terminator = self._read_element_at(base_addr, length)
        if terminator is None:
            return False
        return terminator == 0

    def _has_valid_runtime_state(self) -> bool:
        try:
            if self.is_heap():
                length = self.heap_size.GetValueAsUnsigned(0)
                capacity = self._decode_heap_capacity()
                begin_ptr = self.heap_begin.GetValueAsUnsigned(0)
                if length > capacity:
                    return False
                if capacity > 0 and begin_ptr == 0:
                    return False
                if begin_ptr == 0:
                    return length == 0
                return self._has_terminator(begin_ptr, int(length))

            sso_capacity = self._get_sso_capacity()
            remaining = self._decode_sso_remaining_capacity()
            if remaining > sso_capacity:
                return False
            length = sso_capacity - remaining
            begin_ptr = self.sso_data.AddressOf().GetValueAsUnsigned(0)
            return self._has_terminator(begin_ptr, int(length))
        except Exception:
            return False

    def calculate_length(self) -> int:
        try:
            if not self._runtime_state_valid:
                return 0
            if self.is_heap():
                return self.heap_size.GetValueAsUnsigned(0)

            sso_capacity = self._get_sso_capacity()
            remaining = self._decode_sso_remaining_capacity()
            return max(0, min(sso_capacity, sso_capacity - remaining))
        except Exception:
            return 0

    def calculate_capacity(self) -> int:
        try:
            if not self._runtime_state_valid:
                return 0
            if self.is_heap():
                return self._decode_heap_capacity()
            return self._get_sso_capacity()
        except Exception:
            return 0

    def _create_size_t_child(self, name: str, value: int) -> lldb.SBValue:
        return self.valobj.CreateValueFromData(
            name, create_data_from_uint(value, self.size_type.GetByteSize()), self.size_type
        )

    def get_length(self) -> lldb.SBValue:
        return self._create_size_t_child("length", self.calculate_length())

    def get_capacity(self) -> lldb.SBValue:
        return self._create_size_t_child("capacity", self.calculate_capacity())

    def get_value(self) -> lldb.SBValue:
        try:
            if not self._runtime_state_valid:
                return self.valobj.CreateValueFromData(
                    "value", create_data_from_cstring(""), find_type("char").GetArrayType(1)
                )
            string_length = self.calculate_length()
            count_with_terminator = max(1, string_length + 1)

            if self.is_heap():
                begin_ptr = self.heap_begin.GetValueAsUnsigned(0)
            else:
                begin_ptr = self.sso_data.AddressOf().GetValueAsUnsigned(0)

            if begin_ptr == 0:
                return None

            return self.valobj.CreateValueFromAddress(
                "value", begin_ptr, self.value_type.GetArrayType(count_with_terminator)
            )
        except Exception:
            message = "Error reading basic_string value"
            return self.valobj.CreateValueFromData(
                "value",
                create_data_from_cstring(message),
                find_type("char").GetArrayType(len(message) + 1),
            )

    def get_uses_heap(self) -> lldb.SBValue:
        return self.valobj.CreateValueFromData(
            "uses_heap",
            create_data_from_uint(1 if self.is_heap() else 0, 1),
            find_type("bool"),
        )

    def num_children(self):
        if not self._valid_layout:
            return 0
        return len(self.staticChildren)

    def get_child_index(self, name):
        return self.staticChildren.index(name)

    def get_child_at_index(self, index):
        if not self._valid_layout:
            return None
        if index == 0:
            return self.get_length()
        if index == 1:
            return self.get_capacity()
        if index == 2:
            return self.get_uses_heap()
        if index == 3:
            return self.get_value()
        return None

    def update(self):
        self._valid_layout = False
        self._runtime_state_valid = False
        string_data = self.valobj.GetChildMemberWithName("mPair").GetChildMemberWithName(
            "mFirst"
        )
        if not string_data.IsValid():
            return False

        self.sso_buffer = string_data.GetChildMemberWithName("sso")
        self.heap_buffer = string_data.GetChildMemberWithName("heap")
        self.sso_data = self.sso_buffer.GetChildMemberWithName("mData")
        self.remaining_size_field = self.sso_buffer.GetChildMemberWithName(
            "mRemainingSizeField"
        ).GetChildMemberWithName("mnRemainingSize")
        self.heap_begin = self.heap_buffer.GetChildMemberWithName("mpBegin")
        self.heap_size = self.heap_buffer.GetChildMemberWithName("mnSize")
        self.heap_capacity = self.heap_buffer.GetChildMemberWithName("mnCapacity")
        self.size_type = self.heap_size.GetType()
        self.value_type = self.valobj.GetType().GetTemplateArgumentType(0)
        self._valid_layout = (
            self.sso_buffer.IsValid()
            and self.heap_buffer.IsValid()
            and self.sso_data.IsValid()
            and self.remaining_size_field.IsValid()
            and self.heap_begin.IsValid()
            and self.heap_size.IsValid()
            and self.heap_capacity.IsValid()
            and self.size_type.IsValid()
            and self.value_type.IsValid()
        )
        self._runtime_state_valid = self._valid_layout and self._has_valid_runtime_state()
        return False


def basic_string_SummaryProvider(valobj, internal_dict):
    try:
        provider = basic_string_SyntheticChildrenProvider(get_non_synthetic_value(valobj, internal_dict))
        provider.update()
        if not provider._valid_layout or not provider._runtime_state_valid:
            return ""
        value = provider.get_value()
        if value and value.IsValid():
            value_summary = value.GetSummary()
            if value_summary:
                return value_summary
        return ""
    except Exception:
        return ""
