from test_utils import (
    BUILD_DIR,
    add_repo_root_to_path,
    build_target,
    lldb_frame_var,
    marker_line,
)

import unittest
from pathlib import Path

CMAKE_TARGET = "PairTest"
CPP_SOURCE_FILE = Path(__file__).resolve().parent / "PairTest.cpp"
TEST_EXECUTABLE = BUILD_DIR / CMAKE_TARGET


class PairFormatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_target(CMAKE_TARGET)

    def test_set_summary_and_values(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_PAIR_INT"),
            "point",
        )
        self.assertIn("point = (1, 2) {", output)
        self.assertIn("(int) first = 1", output)
        self.assertIn("(int) second = 2", output)

    def test_pair_summary_with_nested_string(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_PAIR_STRING"),
            "mixed",
        )
        self.assertIn('mixed = (5, "hello") {', output)
        self.assertIn("(int) first = 5", output)
        self.assertIn('value = "hello"', output)


if __name__ == "__main__":
    unittest.main(verbosity=2)