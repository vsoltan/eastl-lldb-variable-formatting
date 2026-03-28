from test_utils import (
    BUILD_DIR,
    add_repo_root_to_path,
    build_target,
    lldb_run_markers,
)

from pathlib import Path
import unittest

add_repo_root_to_path()

CMAKE_TARGET = "StringTest"
CPP_SOURCE_FILE = Path(__file__).resolve().parent / f"{CMAKE_TARGET}.cpp"
TEST_EXECUTABLE = BUILD_DIR / CMAKE_TARGET

MARKER_FRAMES = [
    ("BREAK_STRING_SSO",                ["sso"]),
    ("BREAK_STRING_SSO_APPEND",         ["sso"]),
    ("BREAK_STRING_HEAP",               ["heap"]),
    ("BREAK_STRING_SSO_TO_HEAP_APPEND", ["ssoToHeap"]),
    ("BREAK_VARIABLE_WIDTH_STRING",     ["s8", "su8", "s16", "s32"]),
]

class StringFormatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_target(CMAKE_TARGET)
        cls._frames = lldb_run_markers(TEST_EXECUTABLE, CPP_SOURCE_FILE, MARKER_FRAMES)

    def test_string_sso(self):
        output = self._frames["BREAK_STRING_SSO"]
        self.assertIn('(eastl::string) sso = "hello"', output)
        self.assertIn("uses_heap = false", output)
        self.assertIn("length = 5", output)
        self.assertIn('value = "hello"', output)

    def test_string_appended_sso(self):
        output = self._frames["BREAK_STRING_SSO_APPEND"]
        self.assertIn('(eastl::string) sso = "hello world"', output)
        self.assertIn("uses_heap = false", output)
        self.assertIn("length = 11", output)
        self.assertIn('value = "hello world"', output)

    def test_string_heap(self):
        output = self._frames["BREAK_STRING_HEAP"]
        self.assertIn('(eastl::string) heap = "hellotherethisisalongstringthatexceedsssocapacity"', output)
        self.assertIn("uses_heap = true", output)
        self.assertIn("length = 49", output)
        self.assertIn('value = "hellotherethisisalongstringthatexceedsssocapacity"', output)

    def test_string_sso_to_heap(self):
        output = self._frames["BREAK_STRING_SSO_TO_HEAP_APPEND"]
        self.assertIn('(eastl::string) ssoToHeap = "shortStringshouldbetransitionedtoheap"', output)
        self.assertIn("uses_heap = true", output)
        self.assertIn('value = "shortStringshouldbetransitionedtoheap"', output)

    def test_string8(self):
        output = self._frames["BREAK_VARIABLE_WIDTH_STRING"]
        self.assertIn('(eastl::string8) s8 = "regular string"', output)
        self.assertIn("uses_heap = false", output)
        self.assertIn("length = 14", output)

    def test_stringu8(self):
        output = self._frames["BREAK_VARIABLE_WIDTH_STRING"]
        self.assertIn('(eastl::u8string) su8 = "utf8 string"', output)
        self.assertIn("uses_heap = false", output)
        self.assertIn("length = 11", output)

    # string16 and u16string are identical
    def test_string16(self):
        output = self._frames["BREAK_VARIABLE_WIDTH_STRING"]
        self.assertIn('(eastl::string16) s16 = "wide string"', output)
        self.assertIn("uses_heap = false", output)
        self.assertIn("length = 11", output)

    # string32 and u32string are identical
    def test_string32(self):
        output = self._frames["BREAK_VARIABLE_WIDTH_STRING"]
        self.assertIn('(eastl::string32) s32 = "even wider string"', output)
        self.assertIn("uses_heap = true", output)
        self.assertIn("length = 17", output)

if __name__ == "__main__":
    unittest.main(verbosity=2)
