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


CMAKE_TARGET = "WeakPtrTest"
CPP_SOURCE_FILE = Path(__file__).resolve().parent / "WeakPtrTest.cpp"
TEST_EXECUTABLE = BUILD_DIR / CMAKE_TARGET


class WeakPtrFormatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_target(CMAKE_TARGET)

    def test_weak_ptr_live(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_WEAK_PTR_LIVE"),
            "weak_live",
        )
        self.assertIn("weak_live = 0x", output)
        self.assertIn("(int32_t) use_count = 1", output)
        self.assertIn("(bool) expired = false", output)
        self.assertIn("(eastl::weak_ptr<int>::element_type) value = 42", output)

    def test_weak_ptr_expired(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_WEAK_PTR_EXPIRED"),
            "weak_live",
        )
        self.assertIn("weak_live = nullptr", output)
        self.assertIn("(int32_t) use_count = 0", output)
        self.assertIn("(bool) expired = true", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
