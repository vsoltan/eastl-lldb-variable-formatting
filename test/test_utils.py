import subprocess
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
FORMATTER_SCRIPT = REPO_ROOT / "EASTL.py"
BUILD_DIR = REPO_ROOT / "test" / "build"
TEST_DIR = REPO_ROOT / "test"

_configured = False

def run_checked(command, cwd):
    completed = subprocess.run(
        command, cwd=str(cwd), capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(command)}\n"
            f"Exit code: {completed.returncode}\n"
            f"Output:\n{completed.stdout}\n{completed.stderr}"
        )
    return completed

def add_repo_root_to_path():
    TEST_DIR = Path(__file__).resolve().parent
    REPO_ROOT = TEST_DIR.parent
    for path in (REPO_ROOT, TEST_DIR):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def ensure_configured():
    global _configured
    if _configured:
        return

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    run_checked(["cmake", "-S", ".", "-B", "build"], cwd=TEST_DIR)
    _configured = True


def build_target(target_name):
    ensure_configured()
    run_checked(["cmake", "--build", "build", "--target", target_name], cwd=TEST_DIR)


def marker_line(source_file, marker):
    text = Path(source_file).read_text()
    for idx, line in enumerate(text.splitlines(), start=1):
        if marker in line:
            return idx
    raise AssertionError(f"Missing marker: {marker}")


def lldb_frame_var(exe_path, cpp_path, source_line, expression):
    command = [
        "lldb",
        "-b", str(exe_path),
        "-o", f"command script import {FORMATTER_SCRIPT}",
        "-o", f"breakpoint set --file {cpp_path.name} --line {source_line}",
        "-o", "run",
        "-o", f"frame variable -TA {expression}",
        "-o", "quit",
    ]
    completed = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    if completed.returncode != 0:
        raise AssertionError(
            f"LLDB exited with {completed.returncode}\n"
            f"Command: {' '.join(command)}\n"
            f"Output:\n{output}"
        )
    return output
