import lldb

from formatters.constants import STRING_MAX_SIZE
from formatters.utils import (
    create_data_from_bytes,
    create_data_from_cstring,
    create_data_from_uint,
    find_type,
    get_non_synthetic_value,
    get_system_byte_order,
)

class basic_string_SyntheticChildrenProvider:
    STATIC_SYNTHETIC_CHILDREN = {
        "length": 0,
        "capacity": 1,
        "uses_heap": 2,
        "value": 3,
    }

    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self.valid_layout = False
        self.length = 0
        self.capacity = 0
        self.uses_heap = False
        self.data_address = 0
        self.string_value = ""
        self.value_bytes = b""
        self.size_type = None
        self.value_type = None
        self.value_size = 0

    def _size_type_bits(self):
        return self.size_type.GetByteSize() * 8

    def _calculate_sso_capacity(self, sso_data_type):
        if self.value_size <= 0 or not sso_data_type or not sso_data_type.IsValid():
            return 0
        return int(sso_data_type.GetByteSize() / self.value_size)

    def _get_sso_mask(self):
        byte_order = get_system_byte_order()
        if byte_order == lldb.eByteOrderBig:
            return 0x1
        return 0x80

    def _calculate_is_heap(self, remaining_size_raw):
        return bool(remaining_size_raw & self._get_sso_mask())

    def _decode_sso_remaining_capacity(self, remaining_size_raw):
        if get_system_byte_order() == lldb.eByteOrderBig:
            return remaining_size_raw >> 2
        return remaining_size_raw

    def _decode_heap_capacity(self, encoded_capacity):
        if get_system_byte_order() == lldb.eByteOrderBig:
            return encoded_capacity >> 1

        bits = self._size_type_bits()
        if bits <= 1:
            return 0
        heap_mask = 1 << (bits - 1)
        return encoded_capacity & ~heap_mask

    def _read_char_bytes(self, address, length):
        try:
            if address == 0 or length < 0 or self.value_size != 1:
                return b""
            error = lldb.SBError()
            process = self.valobj.GetProcess()
            if not process or not process.IsValid():
                return b""
            value = process.ReadMemory(address, length, error)
            return value if error.Success() else b""
        except Exception:
            return b""

    def _escape_string_summary(self):
        return self.string_value.encode("unicode_escape").decode("ascii").replace('"', '\\"')

    def _create_length_child(self):
        return self.valobj.CreateValueFromData(
            "length",
            create_data_from_uint(self.length, self.size_type.GetByteSize()),
            self.size_type,
        )

    def _create_capacity_child(self):
        return self.valobj.CreateValueFromData(
            "capacity",
            create_data_from_uint(self.capacity, self.size_type.GetByteSize()),
            self.size_type,
        )

    def _create_value_child(self):
        try:
            if not self.valid_layout:
                return None
            if self.value_size == 1:
                value_bytes = self.value_bytes + b"\0"
                return self.valobj.CreateValueFromData(
                    "value",
                    create_data_from_bytes(value_bytes),
                    find_type("char").GetArrayType(len(self.string_value) + 1),
                )
            if self.data_address == 0:
                return None
            return self.valobj.CreateValueFromAddress(
                "value", self.data_address, self.value_type.GetArrayType(max(1, self.length + 1))
            )
        except Exception:
            return None

    def _create_uses_heap_child(self):
        return self.valobj.CreateValueFromData(
            "uses_heap",
            create_data_from_uint(1 if self.uses_heap else 0, 1),
            find_type("bool"),
        )

    def num_children(self):
        return len(self.STATIC_SYNTHETIC_CHILDREN) if self.valid_layout else 0

    def get_child_index(self, name):
        return self.STATIC_SYNTHETIC_CHILDREN.get(name, -1)

    def get_child_at_index(self, index):
        if index < 0 or index >= self.num_children():
            return None
        if index == 0:
            return self._create_length_child()
        if index == 1:
            return self._create_capacity_child()
        if index == 2:
            return self._create_uses_heap_child()
        if index == 3:
            return self._create_value_child()
        return None

    def update(self):
        self.valid_layout = False
        self.length = 0
        self.capacity = 0
        self.uses_heap = False
        self.data_address = 0
        self.string_value = ""
        self.value_bytes = b""
        self.size_type = None
        self.value_type = None
        self.value_size = 0

        string_data = self.valobj.GetChildMemberWithName("mPair").GetChildMemberWithName("mFirst")
        if not string_data.IsValid():
            return False

        sso_buffer = string_data.GetChildMemberWithName("sso")
        heap_buffer = string_data.GetChildMemberWithName("heap")
        sso_data = sso_buffer.GetChildMemberWithName("mData")
        remaining_size_field = sso_buffer.GetChildMemberWithName(
            "mRemainingSizeField"
        ).GetChildMemberWithName("mnRemainingSize")
        heap_begin = heap_buffer.GetChildMemberWithName("mpBegin")
        heap_size = heap_buffer.GetChildMemberWithName("mnSize")
        heap_capacity = heap_buffer.GetChildMemberWithName("mnCapacity")
        self.size_type = heap_size.GetType()
        self.value_type = self.valobj.GetType().GetTemplateArgumentType(0)
        self.value_size = self.value_type.GetByteSize()
        self.valid_layout = (
            sso_buffer.IsValid()
            and heap_buffer.IsValid()
            and sso_data.IsValid()
            and remaining_size_field.IsValid()
            and heap_begin.IsValid()
            and heap_size.IsValid()
            and heap_capacity.IsValid()
            and self.size_type.IsValid()
            and self.value_type.IsValid()
            and self.value_size > 0
        )
        if not self.valid_layout:
            return False

        remaining_size_raw = remaining_size_field.GetValueAsUnsigned(0) & 0xFF
        self.uses_heap = self._calculate_is_heap(remaining_size_raw)
        if self.uses_heap:
            self.length = heap_size.GetValueAsUnsigned(0)
            self.capacity = self._decode_heap_capacity(heap_capacity.GetValueAsUnsigned(0))
            self.data_address = heap_begin.GetValueAsUnsigned(0)
        else:
            sso_capacity = self._calculate_sso_capacity(sso_data.GetType())
            remaining = min(self._decode_sso_remaining_capacity(remaining_size_raw), sso_capacity)
            self.length = max(0, sso_capacity - remaining)
            self.capacity = sso_capacity
            self.data_address = sso_data.AddressOf().GetValueAsUnsigned(0)

        self.length = min(self.length, STRING_MAX_SIZE)
        if self.value_size == 1 and self.data_address != 0:
            self.value_bytes = self._read_char_bytes(self.data_address, self.length)[: self.length]
            self.string_value = self.value_bytes.decode("latin-1")
        return False


def basic_string_SummaryProvider(valobj, internal_dict):
    try:
        provider = basic_string_SyntheticChildrenProvider(
            get_non_synthetic_value(valobj), internal_dict
        )
        provider.update()
        if not provider.valid_layout:
            return ""
        if provider.value_size == 1:
            return f'"{provider._escape_string_summary()}"'
        value = provider._create_value_child()
        if value and value.IsValid() and value.GetSummary():
            return value.GetSummary()
        return ""
    except Exception:
        return ""
