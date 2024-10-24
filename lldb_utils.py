import lldb


def GetSystemByteOrder():
    return lldb.debugger.GetSelectedTarget().GetByteOrder()


def CreateDataFromUInt32(value: int) -> lldb.SBData:
    addr_byte_size = lldb.debugger.GetSelectedTarget().GetAddressByteSize()
    return lldb.SBData.CreateDataFromUInt32Array(
        GetSystemByteOrder(), addr_byte_size, [value]
    )


def CreateDataFromCString(value: str) -> lldb.SBData:
    addr_byte_size = lldb.debugger.GetSelectedTarget().GetAddressByteSize()
    return lldb.SBData.CreateDataFromCString(
        GetSystemByteOrder(), addr_byte_size, value
    )


def FindType(type_name: str) -> lldb.SBType:
    return lldb.debugger.GetSelectedTarget().FindFirstType(type_name)
