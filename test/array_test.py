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


CMAKE_TARGET = "ArrayTest"
CPP_SOURCE_FILE = Path(__file__).resolve().parent / "ArrayTest.cpp"
TEST_EXECUTABLE = BUILD_DIR / CMAKE_TARGET


class ArrayFormatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_target(CMAKE_TARGET)

    def test_array_values(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_ARRAY_VALUES"),
            "numbers",
        )
        self.assertIn("size=3", output)
        self.assertIn("(eastl_size_t) size = 3", output)
        self.assertIn("[0] = 3", output)
        self.assertIn("[1] = 1", output)
        self.assertIn("[2] = 4", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
