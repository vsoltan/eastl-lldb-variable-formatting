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


CMAKE_TARGET = "SetTest"
CPP_SOURCE_FILE = Path(__file__).resolve().parent / "SetTest.cpp"
TEST_EXECUTABLE = BUILD_DIR / CMAKE_TARGET


class SetFormatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_target(CMAKE_TARGET)

    def test_set_summary_and_values(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_SET_VALUES"),
            "numbers",
        )
        self.assertIn("numbers = [3] { 3, ... }", output)
        self.assertIn("(eastl_size_t) size = 3", output)
        self.assertIn("(int) [0] = 3", output)
        self.assertIn("(int) [1] = 8", output)
        self.assertIn("(int) [2] = 10", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
