from test_utils import (
    BUILD_DIR,
    add_repo_root_to_path,
    build_target,
    lldb_frame_var,
    marker_line,
)

from pathlib import Path
import unittest

add_repo_root_to_path()

CMAKE_TARGET = "StringTest"
CPP_SOURCE_FILE = Path(__file__).resolve().parent / f"{CMAKE_TARGET}.cpp"
TEST_EXECUTABLE = BUILD_DIR / CMAKE_TARGET

class StringFormatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_target(CMAKE_TARGET)

    def test_string_sso(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_STRING_SSO"),
            "sso",
        )
        self.assertIn('(eastl::string) sso = "hello"', output)
        self.assertIn("(bool) uses_heap = false", output)
        self.assertIn("(size_type) length = 5", output)
        self.assertIn('value = "hello"', output)

    def test_string_appended_sso(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_STRING_SSO_APPEND"),
            "sso",
        )
        self.assertIn('(eastl::string) sso = "hello world"', output)
        self.assertIn("(bool) uses_heap = false", output)
        self.assertIn("(size_type) length = 11", output)
        self.assertIn('value = "hello world"', output)

    def test_string_heap(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_STRING_HEAP"),
            "heap",
        )
        self.assertIn('(eastl::string) heap = "hellotherethisisalongstringthatexceedsssocapacity"', output)
        self.assertIn("(bool) uses_heap = true", output)
        self.assertIn("(size_type) length = 49", output)
        self.assertIn('value = "hellotherethisisalongstringthatexceedsssocapacity"', output)

    def test_string_sso_to_heap(self):
        output = lldb_frame_var(
            TEST_EXECUTABLE,
            CPP_SOURCE_FILE,
            marker_line(CPP_SOURCE_FILE, "BREAK_STRING_SSO_TO_HEAP_APPEND"),
            "ssoToHeap",
        )
        self.assertIn('(eastl::string) ssoToHeap = "shortStringshouldbetransitionedtoheap"', output)
        self.assertIn("(bool) uses_heap = true", output)
        self.assertIn('value = "shortStringshouldbetransitionedtoheap"', output)


# TODO: make sure this works with different width string types, string16, string32

if __name__ == "__main__":
    unittest.main(verbosity=2)
