from test_utils import (
    BUILD_DIR,
    add_repo_root_to_path,
    build_target,
    lldb_frame_var,
    marker_line,
)

import unittest
from pathlib import Path

add_repo_root_to_path()


CMAKE_TARGET = "UniquePtrTest"
CPP_SOURCE_FILE = Path(__file__).resolve().parent / "UniquePtrTest.cpp"
TEST_EXECUTABLE = BUILD_DIR / CMAKE_TARGET


class UniquePtrFormatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_target(CMAKE_TARGET)

    def test_unique_ptr_null(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_UNIQUE_PTR_NULL"),
            "unique_null",
        )
        self.assertIn("unique_null = (nullptr)", output)
        self.assertIn("pointer = 0x0000000000000000", output)

    def test_unique_ptr_value(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_UNIQUE_PTR_VALUE"),
            "unique_value",
        )
        self.assertIn("unique_value = (0x", output)
        self.assertIn(" = 7)", output)
        self.assertIn("pointer = 0x", output)
        self.assertIn("(int) value = 7", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)