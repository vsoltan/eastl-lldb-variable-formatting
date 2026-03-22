from test_utils import (
    BUILD_DIR,
    # add_repo_root_to_path,
    build_target,
    lldb_frame_var,
    marker_line,
)

# add_repo_root_to_path()

import unittest
from pathlib import Path
from formatters.constants import VECTOR_MAX_SIZE

CMAKE_TARGET = "VectorTest"
CPP_SOURCE_FILE = Path(__file__).resolve().parent / f"{CMAKE_TARGET}.cpp"
TEST_EXECUTABLE = BUILD_DIR / CMAKE_TARGET

class VectorFormatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_target(CMAKE_TARGET)

    def test_initialized(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_VECTOR_INITIALIZED"),
            "v",
        )
        self.assertIn("(eastl::vector<int>) v = size=5", output)
        self.assertIn("(eastl_size_t) size = 5", output)
        self.assertIn("(eastl_size_t) capacity = 5", output)
        self.assertIn("(int) [0] = 1", output)
        self.assertIn("(int) [1] = 2", output)
        self.assertIn("(int) [2] = 3", output)
        self.assertIn("(int) [3] = 4", output)
        self.assertIn("(int) [4] = 5", output)

    def test_after_push_back(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_VECTOR_PUSHED"),
            "v",
        )
        self.assertIn("(eastl::vector<int>) v = size=6", output)
        self.assertIn("(int) [5] = 6", output)
    
    def test_after_clear(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_VECTOR_CLEARED"),
            "v",
        )
        self.assertIn("(eastl::vector<int>) v = size=0", output)

    def test_after_large_push_back(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_LARGE_VECTOR"),
            "v",
        )
        # The max size cap is used to limit the number of synthetic children that LLDB creates, but
        # it should not affect the summary or size values.
        self.assertIn("(eastl::vector<int>) v = size=10000", output)
        self.assertIn("(eastl_size_t) size = 10000", output)
        self.assertIn(f"(int) [{VECTOR_MAX_SIZE - 1}] = {VECTOR_MAX_SIZE - 1}", output)
        self.assertNotIn(f"(int) [{VECTOR_MAX_SIZE}] =", output)

    def test_resize(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_VECTOR_RESIZED"),
            "v",
        )
        self.assertIn("(eastl::vector<int>) v = size=100", output)
        self.assertIn("(eastl_size_t) size = 100", output)

if __name__ == "__main__":
    unittest.main(verbosity=2)
