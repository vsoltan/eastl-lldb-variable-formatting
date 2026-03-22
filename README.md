# eastl-lldb-variable-formatting

EASTL ships with an EASTL.natvis file that provides variable formatting in Visual Studio debugging sessions. Unfortunately, we do not have the same luxury on platforms that use the Clang compiler (MacOS, iOS, and Android).

Without script:
```
frame var str_heap
(lldb) frame var str_heap
(eastl::string) str_heap = {
  mPair = {
    eastl::compressed_pair_imp<eastl::basic_string<char, eastl::allocator>::Layout, eastl::allocator, 2> = {
      mFirst = {
         ={...}
      }
    }
  }
}
```

With script:
```
frame var str_heap
(lldb) frame var str_heap
(eastl::string) str_heap = {
  length = 49
  capacity = 49
  uses_heap = true
  value = "hellotherethisisalongstringthatexceedsssocapacity"
}
```

## Usage
To add variable formatting to your lldb session, run the following command:
```
command script import eastl-lldb-variable-formatting/EASTL.py
```
or add it to your `.lldbinit` file. In VSCode, if you're using another C++ extension for debugging (such as the CMake extension), you'll need to add the command to the initialization arguments: 

```json
"cmake.debugConfig": {
    "type": "lldb-dap",
    "request": "launch",
    "name": "CMake Debug (LLDB)",
    "program": "${command:cmake.launchTargetPath}",
    "cwd": "${workspaceFolder}",
    "args": [],
        "env": {},
        "initCommands": [
            "command script import eastl-lldb-variable-formatting/EASTL.py"
        ]
    },
```

# Running Tests
```bash
python3 test/test.py # Runs all tests
python3 test/test.py --module="vector"
```

## Reference
https://lldb.llvm.org/use/variable.html
https://github.com/llvm/llvm-project/tree/main/lldb/examples/synthetic
https://github.com/llvm/llvm-project/tree/main/lldb/examples/summaries