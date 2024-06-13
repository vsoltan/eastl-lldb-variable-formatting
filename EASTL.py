import lldb

type_category = 'EASTL'

'''
class UniquePtrSyntheticProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj

    def num_children(self):
        return 2

    def get_child_index(self, name):
        if name == 'pointer':
            return 0
        elif name == 'value':
            return 1
        else:
            return -1

    def get_child_at_index(self, index):
        if index == 0:
            if self.pointer.GetData() is None:
                return self.valobj.CreateValueFromData('pointer', lldb.SBData(), self.pointer.GetType())
            else:
                return self.valobj.CreateValueFromData('pointer', self.pointer.GetData(), self.pointer.GetType())
        if index == 1:
            if self.value.GetData() is None:
                return self.valobj.CreateValueFromData('value', lldb.SBData(), self.value.GetType())
            else:
                return self.valobj.CreateValueFromData('value', self.value.GetData(), self.value.GetType())
        else:
            return None

    def update(self):
        self.pointer = self.valobj.EvaluateExpression('mPair.mFirst')
        self.value = self.pointer.Dereference()
        return False

def UniquePtrSummaryProvider(valobj, internal_dict):
    pointer = valobj.EvaluateExpression('mPair.mFirst')
    print('pointer', pointer)
    if pointer.GetValue() is None:
        return 'nullptr'
    else:
        value = pointer.Dereference().GetValue()
        print('value', value)
        return 'nullptr' if value is None else value
'''

# TODO: add a limit to the number of children for large lists
class VectorBase_SyntheticProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj

    def num_children(self):
        begin_addr = self.begin.GetValueAsUnsigned()
        end_addr = self.end.GetValueAsUnsigned()
        capacity_addr = self.capacity.GetValueAsUnsigned()

        if None in (begin_addr, end_addr, capacity_addr):
            return 0
        if 0 in (begin_addr, end_addr, capacity_addr):
            return 0
        if begin_addr >= end_addr:
            return 0
        if capacity_addr < end_addr:
            return 0
        num_children = end_addr - begin_addr
        if num_children % self.data_size != 0:
            return 0
        num_children = int(num_children / self.data_size) + 2
        return num_children

    def get_child_index(self, name):
        if name.startswith('[') and name.endswith(']'):
            try:
                return int(name.lstrip('[').rstrip(']'))
            except:
                return -1
        num_children = self.num_children()
        if name == 'size':
            return num_children - 2
        if name == 'capacity':
            return num_children - 1

    def get_child_at_index(self, index):
        num_children = self.num_children()
        if index < 0 or index >= num_children:
            return None
        target = lldb.debugger.GetSelectedTarget()
        byte_order = target.GetByteOrder()
        if index == num_children - 2:
            size_data = lldb.SBData.CreateDataFromUInt32Array(byte_order, 8, [ self.num_children() - 2 ])
            return self.valobj.CreateValueFromData('size', size_data, target.FindFirstType('eastl_size_t'))
        if index == num_children - 1:
            capacity = int((self.capacity.GetValueAsUnsigned() - self.begin.GetValueAsUnsigned()) / self.data_size)
            size_data = lldb.SBData.CreateDataFromUInt32Array(byte_order, 8, [ capacity ])
            return self.valobj.CreateValueFromData('capacity', size_data, target.FindFirstType('eastl_size_t'))
        try:
            offset = index * self.data_size
            return self.begin.CreateChildAtOffset(f'[{index}]', offset, self.data_type)
        except:
            return None

    def update(self):
        try:
            self.begin = self.valobj.GetChildMemberWithName('mpBegin')
            self.end = self.valobj.GetChildMemberWithName('mpEnd')
            self.capacity = self.valobj.GetChildMemberWithName('mCapacityAllocator') \
                                       .GetChildMemberWithName('mFirst')
            self.data_type = self.begin.GetType().GetPointeeType()
            self.data_size = self.data_type.GetByteSize()
        except Exception as e:
            print(e)
        return False

# def VectorBase_SummaryProvider(valobj, internal_dict):
#     begin = valobj.GetChildMemberWithName('mpBegin')
#     end = valobj.GetChildMemberWithName('mpEnd')
#     capacityAllocator = valobj.GetChildMemberWithName('mCapacityAllocator')
#     capacityPtr = capacityAllocator.GetChildMemberWithName('mFirst')
#
#     if begin.GetValue() is None or end.GetValue() is None:
#         return 'empty'
#
#     begin_address = begin.GetValueAsUnsigned()
#     end_address = end.GetValueAsUnsigned()
#     capacity_address = capacityPtr.GetValueAsUnsigned()
#
#     if begin_address == end_address:
#         return 'empty'
#
#     if begin_address == capacity_address:
#         return 'full'
#
#     return f'{(end_address - begin_address) / begin.GetType().GetPointeeType().GetByteSize()} elements'

'''
class shared_ptr_SyntheticChildrenProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj

    def num_children(self):
        return 2

    def get_child_index(self, name):
        print('from get_child_index', name)
        if name == 'pointer':
            return 0
        elif name == 'value':
            return 1
        else:
            return -1

    def get_child_at_index(self, index):
        if index == 0:
            return self.valobj.CreateValueFromData('pointer', self.pointer.GetData(), self.pointer.GetType())
        if index == 1:
            return self.valobj.CreateValueFromData('value', self.value.GetData(), self.value.GetType())
        else:
            return None

    def update(self):
        try:
            self.pointer = self.valobj.EvaluateExpression('mpValue')
            self.value = self.valobj.EvaluateExpression('*mpValue')
        except Exception as e:
            print(e)
        return False
'''

'''
class basic_string_SyntheticChildrenProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self.update()

    def num_children(self):
        return 3

    def get_child_index(self, name):
        if name == 'length':
            return 0
        #elif name == 'capacity':
        #    return 1
        #elif name == 'value':
        #    return 2
        else:
            return -1

    def get_child_at_index(self, index):
        if index == 0:
            return self.valobj.CreateValueFromExpression('length', 'size()')
        #if index == 1:
        #    return self.valobj.CreateValueFromExpression('capacity', 'capacity()')
        #if index == 2:
        #    return self.valobj.CreateValueFromExpression('value', 'c_str()')
        else:
            return None

    def update(self):
        #self.length = self.valobj.EvaluateExpression('length()')
        #self.capacity = self.valobj.EvaluateExpression('capacity()')
        #self.value = self.valobj.EvaluateExpression('data()')
        return
'''

def __lldb_init_module(debugger, internal_dict):
    #debugger.HandleCommand(f'type synthetic add -x ^eastl::unique_ptr<.+> >$ --python-class EASTL.UniquePtrSyntheticProvider -w {type_category}')
    #debugger.HandleCommand(f'type summary add -x ^eastl::unique_ptr<.+> >$ --python-function EASTL.UniquePtrSummaryProvider -w {type_category}')

    debugger.HandleCommand(f'type synthetic add -x ^eastl::VectorBase<.*> --python-class EASTL.VectorBase_SyntheticProvider -w {type_category} -C true')
    debugger.HandleCommand(f'type category enable {type_category}')
    return
