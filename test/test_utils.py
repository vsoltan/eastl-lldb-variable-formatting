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


def lldb_run_markers(exe_path, cpp_path, marker_frames):
    """
    Launch one lldb instance, set a breakpoint at each marker, and capture
    `frame variable` output at each stop.

    marker_frames: list of (marker_name, [variable_names])
    Returns: dict mapping marker_name -> captured output string
    """
    commands = [f"command script import {FORMATTER_SCRIPT}"]

    for marker, _ in marker_frames:
        line = marker_line(cpp_path, marker)
        commands.append(f"breakpoint set --file {cpp_path.name} --line {line}")

    commands.append("run")

    for i, (marker, variables) in enumerate(marker_frames):
        commands.append(f'script print("===BEGIN {marker}===")')
        for var in variables:
            commands.append(f"frame variable -TA {var}")
        commands.append(f'script print("===END {marker}===")')
        if i < len(marker_frames) - 1:
            commands.append("continue")

    commands.append("quit")

    lldb_args = ["lldb", "-b", str(exe_path)]
    for cmd in commands:
        lldb_args.extend(["-o", cmd])

    completed = subprocess.run(
        lldb_args, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False
    )
    output = completed.stdout + "\n" + completed.stderr

    results = {}
    for marker, _ in marker_frames:
        begin_tag = f"===BEGIN {marker}==="
        end_tag = f"===END {marker}==="
        start = output.find(begin_tag)
        end = output.find(end_tag)
        if start != -1 and end != -1:
            results[marker] = output[start + len(begin_tag):end]

    return results


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
