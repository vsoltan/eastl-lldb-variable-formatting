import argparse

import array_test
import map_test
import pair_test
import set_test
import shared_ptr_test
import span_test
import string_test
import unique_ptr_test
import vector_test
import weak_ptr_test

import unittest

TEST_MODULES = {
    "array": array_test,
    "map": map_test,
    "pair": pair_test,
    "set": set_test,
    "shared_ptr": shared_ptr_test,
    "span": span_test,
    "string": string_test,
    "unique_ptr": unique_ptr_test,
    "vector": vector_test,
    "weak_ptr": weak_ptr_test,
}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run all LLDB formatter tests or a single test module."
    )
    parser.add_argument(
        "module",
        nargs="?",
        choices=sorted(TEST_MODULES),
        
        help="single module to run (for example: string, vector, map)",
    )
    return parser.parse_args()


def suite(module_name=None):
    loader = unittest.defaultTestLoader
    combined = unittest.TestSuite()
    modules = TEST_MODULES.items()
    if module_name is not None:
        modules = [(module_name, TEST_MODULES[module_name])]

    for _, module in modules:
        combined.addTests(loader.loadTestsFromModule(module))
    return combined


if __name__ == "__main__":
    args = parse_args()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite(args.module))
    raise SystemExit(0 if result.wasSuccessful() else 1)
