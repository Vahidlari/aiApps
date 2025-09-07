#!/usr/bin/env python3
"""
Script to verify that the test setup is working correctly.
This will help confirm that Test Explorer and CodeLens should work.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🔍 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print("Output:", result.stdout.strip())
            return True
        else:
            print("❌ FAILED")
            if result.stderr:
                print("Error:", result.stderr.strip())
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    print("🚀 Verifying Test Setup for RAG System")
    print("=" * 60)

    # Change to the RAG system directory
    script_dir = Path(__file__).parent
    rag_system_dir = script_dir.parent.parent / "rag_system"
    os.chdir(rag_system_dir)

    print(f"Working directory: {rag_system_dir}")

    # Test 1: Check if pytest can discover tests
    success1 = run_command(
        ["python", "-m", "pytest", "--collect-only", "tests/"],
        "Test Discovery - Can pytest find all tests?",
    )

    # Test 2: Check if we can run a specific test
    success2 = run_command(
        [
            "python",
            "-m",
            "pytest",
            "tests/unit/test_dataclasses.py::TestCitation::test_citation_creation",
            "-v",
        ],
        "Test Execution - Can we run a specific test?",
    )

    # Test 3: Check if we can run a few specific tests (not all, as some may fail)
    success3 = run_command(
        [
            "python",
            "-m",
            "pytest",
            "tests/unit/test_dataclasses.py::TestCitation",
            "-v",
            "--tb=short",
        ],
        "Specific Tests - Can we run specific test classes?",
    )

    # Test 4: Check Python path
    success4 = run_command(
        ["python", "-c", "import utils.latex_parser; print('Import successful')"],
        "Import Test - Can we import the main modules?",
    )

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    tests = [
        ("Test Discovery", success1),
        ("Test Execution", success2),
        ("Specific Tests", success3),
        ("Import Test", success4),
    ]

    all_passed = True
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not success:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Test Explorer should now work in VS Code/Cursor")
        print("✅ CodeLens should show 'Run Test | Debug Test' links")
        print("✅ You should see test status indicators")
        print("\nNext steps:")
        print("1. Open test_dataclasses.py in Cursor")
        print("2. Look for 'Run Test | Debug Test' links above test functions")
        print("3. Open Test Explorer panel (View → Test Explorer)")
        print("4. Try running tests from the Test Explorer")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the errors above and fix them.")
        print("Test Explorer and CodeLens may not work until all tests pass.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    import os

    sys.exit(main())
