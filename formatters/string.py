import lldb

from formatters.constants import (
    STRING_MAX_SIZE
)
from formatters.utils import (
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
        self._valobj = valobj

    def update(self):
        self._valid_layout = False

        layout = self._valobj.GetChildMemberWithName("mPair").GetChildMemberWithName("mFirst")
        if not layout.IsValid():
            return False

        sso = layout.GetChildMemberWithName("sso")
        heap = layout.GetChildMemberWithName("heap")
        if not sso.IsValid() or not heap.IsValid():
            return False

        remaining_size_field = sso.GetChildMemberWithName("mRemainingSizeField").GetChildMemberWithName("mnRemainingSize")
        value_type = self._valobj.GetType().GetTemplateArgumentType(0)
        heap_size = heap.GetChildMemberWithName("mnSize")

        if not heap_size.IsValid() or not remaining_size_field.IsValid() or not value_type.IsValid():
            return False

        size_type = heap_size.GetType()
        if not size_type.IsValid() or value_type.GetByteSize() <= 0:
            return False

        self._size_type = size_type
        self._value_type = value_type
        self._value_size = value_type.GetByteSize()
        self._is_heap = self._read_is_heap(remaining_size_field)
        self._length, self._capacity, self._data_address = self._read_memory(heap, sso, heap_size)
        self._string_value = self._read_string_value()
        self._valid_layout = True
        return False

    def _read_is_heap(self, remaining_size_field):
        remaining_size_raw = remaining_size_field.GetValueAsUnsigned(0) & 0xFF
        sso_mask = 0x1 if get_system_byte_order() == lldb.eByteOrderBig else 0x80
        return bool(remaining_size_raw & sso_mask)

    def _read_memory(self, heap, sso, heap_size):
        if self._is_heap:
            heap_begin = heap.GetChildMemberWithName("mpBegin")
            heap_capacity = heap.GetChildMemberWithName("mnCapacity")
            if not heap_begin.IsValid() or not heap_capacity.IsValid():
                return (0, 0, 0)
            length = min(heap_size.GetValueAsUnsigned(0), STRING_MAX_SIZE)
            capacity = self._decode_heap_capacity(heap_capacity.GetValueAsUnsigned(0))
            data_address = heap_begin.GetValueAsUnsigned(0)
        else:
            sso_data = sso.GetChildMemberWithName("mData")
            remaining_size_field = sso.GetChildMemberWithName("mRemainingSizeField").GetChildMemberWithName("mnRemainingSize")
            if not sso_data.IsValid() or not remaining_size_field.IsValid():
                return (0, 0, 0)
            sso_capacity = int(sso_data.GetType().GetByteSize() / self._value_size)
            remaining_size_raw = remaining_size_field.GetValueAsUnsigned(0) & 0xFF
            remaining = min(self._decode_sso_remaining_capacity(remaining_size_raw), sso_capacity)
            length = min(max(0, sso_capacity - remaining), STRING_MAX_SIZE)
            capacity = sso_capacity
            data_address = sso_data.AddressOf().GetValueAsUnsigned(0)
        return (length, capacity, data_address)

    def _read_string_value(self):
        if self._data_address == 0:
            return None
        raw_bytes = self._read_bytes(self._data_address, self._length * self._value_size)
        if not raw_bytes:
            return None
        if self._value_size == 1:
            return raw_bytes.decode("utf-8", errors="replace")
        is_little_endian = get_system_byte_order() != lldb.eByteOrderBig
        if self._value_size == 2:
            return raw_bytes.decode("utf-16-le" if is_little_endian else "utf-16-be", errors="replace")
        if self._value_size == 4:
            return raw_bytes.decode("utf-32-le" if is_little_endian else "utf-32-be", errors="replace")
        return None

    def num_children(self):
        return len(self.STATIC_SYNTHETIC_CHILDREN) if self._valid_layout else 0

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

    def _decode_sso_remaining_capacity(self, remaining_size_raw):
        if get_system_byte_order() == lldb.eByteOrderBig:
            return remaining_size_raw >> 2
        return remaining_size_raw

    def _decode_heap_capacity(self, encoded_capacity):
        if get_system_byte_order() == lldb.eByteOrderBig:
            return encoded_capacity >> 1
        bits = self._size_type.GetByteSize() * 8
        if bits <= 1:
            return 0
        return encoded_capacity & ~(1 << (bits - 1))

    def _read_bytes(self, address, length):
        try:
            error = lldb.SBError()
            process = self._valobj.GetProcess()
            if not process or not process.IsValid():
                return b""
            value = process.ReadMemory(address, length, error)
            return value if error.Success() else b""
        except Exception:
            return b""

    def _escape_string_summary(self):
        if not self._string_value:
            return ""
        return self._string_value.encode("unicode_escape").decode("ascii").replace('"', '\\"')

    def _create_length_child(self):
        return self._valobj.CreateValueFromData(
            "length",
            create_data_from_uint(self._length, self._size_type.GetByteSize()),
            self._size_type,
        )

    def _create_capacity_child(self):
        return self._valobj.CreateValueFromData(
            "capacity",
            create_data_from_uint(self._capacity, self._size_type.GetByteSize()),
            self._size_type,
        )

    def _create_uses_heap_child(self):
        return self._valobj.CreateValueFromData(
            "uses_heap",
            create_data_from_uint(1 if self._is_heap else 0, 1),
            find_type("bool"),
        )

    def _create_value_child(self):
        try:
            if self._value_size == 1:
                if self._data_address == 0:
                    return self._valobj.CreateValueFromData(
                        "value",
                        create_data_from_cstring(""),
                        find_type("char").GetArrayType(1),
                    )
                return self._valobj.CreateValueFromData(
                    "value",
                    self._valobj.CreateValueFromAddress(
                        "__eastl_string_value",
                        self._data_address,
                        find_type("char").GetArrayType(self._length + 1),
                    ).GetData(),
                    find_type("char").GetArrayType(self._length + 1),
                )
            if self._data_address == 0:
                return None
            return self._valobj.CreateValueFromAddress(
                "value", self._data_address, self._value_type.GetArrayType(max(1, self._length + 1))
            )
        except Exception:
            return None


def basic_string_SummaryProvider(valobj, internal_dict):
    try:
        provider = basic_string_SyntheticChildrenProvider(
            get_non_synthetic_value(valobj), internal_dict
        )
        provider.update()
        if not provider._valid_layout:
            return ""
        if provider._string_value is not None:
            return f'"{provider._escape_string_summary()}"'
        return ""
    except Exception:
        return ""
