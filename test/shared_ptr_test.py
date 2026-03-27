from test_utils import (
    BUILD_DIR,
    add_repo_root_to_path,
    build_target,
    lldb_frame_var,
    marker_line,
)

add_repo_root_to_path()

import unittest
from pathlib import Path


CMAKE_TARGET = "SharedPtrTest"
CPP_SOURCE_FILE = Path(__file__).resolve().parent / "SharedPtrTest.cpp"
TEST_EXECUTABLE = BUILD_DIR / CMAKE_TARGET


class SharedPtrFormatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_target(CMAKE_TARGET)

    def test_shared_ptr_null(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_SHARED_PTR_NULL"),
            "null_ptr",
        )
        self.assertIn("null_ptr = (nullptr)", output)
        self.assertIn("(eastl::shared_ptr<int>::element_type *) pointer = 0x0000000000000000", output)
        self.assertIn("(int32_t) use_count = 0", output)
        self.assertIn("(int32_t) weak_count = 0", output)

    def test_shared_ptr_value(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_SHARED_PTR_VALUE"),
            "ptr",
        )
        self.assertIn("ptr = (0x", output)
        self.assertIn(" = 42)", output)
        self.assertIn("(eastl::shared_ptr<int>::element_type *) pointer = 0x", output)
        self.assertIn("(int32_t) use_count = 1", output)
        self.assertIn("(int32_t) weak_count = 1", output)
        self.assertIn("(eastl::shared_ptr<int>::element_type) value = 42", output)

    def test_shared_ptr_copy_increments_counts(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_SHARED_PTR_COPIED"),
            "ptr ptr_copy",
        )
        self.assertIn("ptr = (0x", output)
        self.assertIn("(int32_t) use_count = 2", output)
        self.assertIn("(eastl::shared_ptr<int>::element_type) value = 42", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
