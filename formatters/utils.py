import lldb

def get_system_byte_order():
    return lldb.debugger.GetSelectedTarget().GetByteOrder()

def create_data_from_uint(value: int, byte_size=None) -> lldb.SBData:
    target = lldb.debugger.GetSelectedTarget()
    data_byte_size = byte_size if byte_size is not None else target.GetAddressByteSize()

    if data_byte_size <= 4:
        return lldb.SBData.CreateDataFromUInt32Array(
            get_system_byte_order(), data_byte_size, [value & 0xFFFFFFFF]
        )

    if hasattr(lldb.SBData, "CreateDataFromUInt64Array"):
        return lldb.SBData.CreateDataFromUInt64Array(
            get_system_byte_order(), data_byte_size, [value & 0xFFFFFFFFFFFFFFFF]
        )

    return lldb.SBData.CreateDataFromUInt32Array(
        get_system_byte_order(), min(data_byte_size, 4), [value & 0xFFFFFFFF]
    )

def create_data_from_cstring(value: str) -> lldb.SBData:
    addr_byte_size = lldb.debugger.GetSelectedTarget().GetAddressByteSize()
    return lldb.SBData.CreateDataFromCString(
        get_system_byte_order(), addr_byte_size, value
    )

def create_data_from_bytes(value: bytes) -> lldb.SBData:
    if hasattr(lldb.SBData, "CreateDataFromUInt8Array"):
        return lldb.SBData.CreateDataFromUInt8Array(
            get_system_byte_order(), 1, list(value)
        )
    return create_data_from_cstring(value.decode("latin-1"))

def find_type(type_name: str) -> lldb.SBType:
    return lldb.debugger.GetSelectedTarget().FindFirstType(type_name)

# This function is most helpful in our summary providers that receive a synthetic instance of our object.
# To provide the summary, we sometimes need to query information from the object and the logic is already
# implemented in the synthetic child provider. However, constructing a provider instance using a synthetic
# instance of the object results in an invalid state. This is because the synthetic instance only contains
# synthetic child members, not the original members that are used in the provider implementation.
def get_non_synthetic_value(valobj):
    non_synthetic = valobj.GetNonSyntheticValue()
    return non_synthetic if non_synthetic and non_synthetic.IsValid() else valobj

def get_value_display(value):
    if not value or not value.IsValid():
        return "?"
    return value.GetSummary() or value.GetValue() or "?"

def format_sequence_summary(size, preview_values, truncated=False):
    values = list(preview_values)
    if truncated:
        values.append("...")
    if not values:
        return f"[{size}] {{}}"
    return f"[{size}] {{ {', '.join(values)} }}"
