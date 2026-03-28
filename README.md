# eastl-lldb-variable-formatting

EASTL ships with an EASTL.natvis file that provides variable formatting in Visual Studio debugging sessions. Unfortunately, we do not have the same luxury on platforms that use the Clang compiler (MacOS, iOS, and Android).

Without script:
```bash
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
```bash
frame var str_heap
(lldb) frame var str_heap
(eastl::string) str_heap = {
  length = 49
  capacity = 49
  uses_heap = true
  value = "hellotherethisisalongstringthatexceedsssocapacity"
}
```

## Requirements
You will need an lldb installation with `LLDB_PYTHON` enabled. You can verify this by doing
```bash
$ lldb -o "script"
(lldb) script
Python Interactive Interpreter. To exit, type 'quit()', 'exit()'.
>>> 
now exiting InteractiveConsole...
```
You should see the python interpreter open. The version should also be reasonably new to ensure that the Clang APIs used in our scripts (via python binding) actually exist. I've run into issues on MacOS where certain APIs cannot be used because the lldb that ships with the system does not support it.

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
https://rustc-dev-guide.rust-lang.org/debuginfo/lldb-visualizers.html

## Improvements
The rust [docs](https://rustc-dev-guide.rust-lang.org/debuginfo/lldb-visualizers.html#optional-update) mention
> The bool returned from this function is somewhat complicated, when in doubt, return False/None. As of Nov 2025, none of the visualizers return True, but that may change as the debug info test suite is improved. LLDB attempts to cache values when possible, including child values. This cache is effectively the number of child objects, and the addresses of the underlying debugee memory that the child object represents. By returning True, you indicate to LLDB that the number of children and the addresses of those children have not changed since the last time update was run, meaning it can reuse the cached children.
