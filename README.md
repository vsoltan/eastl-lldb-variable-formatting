# eastl-lldb-variable-formatting

EASTL ships with an [EASTL.natvis](https://github.com/electronicarts/EASTL/blob/master/doc/EASTL.natvis) file that provides variable formatting in Visual Studio debugging sessions. Unfortunately, we do not have the same luxury on platforms that use the Clang compiler (MacOS, iOS, and Android).

This project provides summaries and synthetic providers for EASTL types.

By default, your stack frames will look like this:
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

Importing the `EASTL.py` script makes this much cleaner and you don't have to descend multiple levels of nested child properties to figure out what the value represents:
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

## Integration

### Terminal
If you are already in an lldb sesssion, you can just run the below command:
```
command script import eastl-lldb-variable-formatting/EASTL.py
```

### Projects
To set and forget, add the above command to your `.lldbinit` file.

### VSCode
I like using the Microsoft CMake extension: you'll need to add the command to the initialization arguments in your `launch.json`:

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
We provide a test suite to ensure that functionality does not break across EASTL versions. An interesting note is that this runs much faster on linux systems.
```bash
python3 test/test.py # Runs all tests
python3 test/test.py --module="vector"
```

## Reference
https://lldb.llvm.org/use/variable.html
https://github.com/llvm/llvm-project/tree/main/lldb/examples/synthetic
https://github.com/llvm/llvm-project/tree/main/lldb/examples/summaries
https://rustc-dev-guide.rust-lang.org/debuginfo/lldb-visualizers.html

## Possible Improvements
The [rustc dev guide](https://rustc-dev-guide.rust-lang.org/debuginfo/lldb-visualizers.html#optional-update) mentions
> The bool returned from this function is somewhat complicated, when in doubt, return False/None. As of Nov 2025, none of the visualizers return True, but that may change as the debug info test suite is improved. LLDB attempts to cache values when possible, including child values. This cache is effectively the number of child objects, and the addresses of the underlying debugee memory that the child object represents. By returning True, you indicate to LLDB that the number of children and the addresses of those children have not changed since the last time update was run, meaning it can reuse the cached children.
