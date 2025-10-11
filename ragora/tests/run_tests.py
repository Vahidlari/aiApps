#!/usr/bin/env python3
"""
Test runner script for the RAG system.

This script provides a convenient way to run different types of tests
with various configurations.
"""

import argparse
import subprocess
import sys


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run RAG system tests")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all", "coverage"],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Run tests in verbose mode"
    )
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument(
        "--html-coverage", action="store_true", help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--parallel",
        "-n",
        type=int,
        help="Run tests in parallel (requires pytest-xdist)",
    )

    args = parser.parse_args()

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add verbosity
    if args.verbose:
        cmd.append("-vv")

    # Add coverage options
    if args.coverage or args.html_coverage:
        cmd.extend(["--cov=ragora", "--cov-report=term-missing"])
        if args.html_coverage:
            cmd.append("--cov-report=html")

    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # Add test type filters
    if args.type == "unit":
        cmd.extend(["-m", "unit"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
    elif args.fast:
        cmd.extend(["-m", "not slow"])

    # Add test directory
    cmd.append("tests/")

    # Run the tests
    success = run_command(cmd, f"Running {args.type} tests")

    if not success:
        sys.exit(1)

    # Additional commands for coverage
    if args.html_coverage:
        print(f"\n📊 HTML coverage report generated in htmlcov/index.html")

    print("\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    main()
