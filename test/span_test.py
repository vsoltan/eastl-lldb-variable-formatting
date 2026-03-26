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


CMAKE_TARGET = "SpanTest"
CPP_SOURCE_FILE = Path(__file__).resolve().parent / f"{CMAKE_TARGET}.cpp"
TEST_EXECUTABLE = BUILD_DIR / CMAKE_TARGET


class SpanFormatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_target(CMAKE_TARGET)

    def test_dynamic_span(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_SPAN_DYNAMIC"),
            "dynamic_span",
        )
        self.assertIn("size=3", output)
        self.assertIn("(eastl_size_t) size = 3", output)
        self.assertIn("(int) [0] = 5", output)
        self.assertIn("(int) [1] = 6", output)
        self.assertIn("(int) [2] = 7", output)

    def test_static_span(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_SPAN_STATIC"),
            "static_span",
        )
        self.assertIn("size=3", output)
        self.assertIn("(eastl_size_t) size = 3", output)
        self.assertIn("(int) [0] = 5", output)
        self.assertIn("(int) [1] = 6", output)
        self.assertIn("(int) [2] = 7", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
