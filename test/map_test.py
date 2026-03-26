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


CMAKE_TARGET = "MapTest"
CPP_SOURCE_FILE = Path(__file__).resolve().parent / "MapTest.cpp"
TEST_EXECUTABLE = BUILD_DIR / CMAKE_TARGET


class MapFormatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_target(CMAKE_TARGET)

    def test_map_summary_and_values(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_MAP_VALUES"),
            "labels",
        )
        self.assertIn("size=3", output)
        self.assertIn("(eastl_size_t) size = 3", output)
        self.assertIn("(const int) first = 1", output)
        self.assertIn("(const int) first = 2", output)
        self.assertIn("(const int) first = 4", output)
        self.assertIn("(char[4]) value = \"one\"", output)
        self.assertIn("(char[4]) value = \"two\"", output)
        self.assertIn("(char[5]) value = \"four\"", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
