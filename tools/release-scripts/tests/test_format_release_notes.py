"""
Tests for format-release-notes.py script.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Get path to the script
SCRIPT_DIR = Path(__file__).parent.parent
SCRIPT_PATH = SCRIPT_DIR / "format-release-notes.py"


def run_script(args, expect_success=True):
    """
    Helper function to run the format-release-notes.py script.

    Args:
        args: List of arguments to pass to the script
        expect_success: Whether to expect successful execution

    Returns:
        Tuple of (stdout, stderr, returncode)
    """
    cmd = [sys.executable, str(SCRIPT_PATH)] + args
    result = subprocess.run(cmd, capture_output=True, text=True)

    if expect_success and result.returncode != 0:
        pytest.fail(f"Script failed unexpectedly:\n{result.stderr}")

    return result.stdout, result.stderr, result.returncode


@pytest.mark.unit
def test_basic_installation_instructions():
    """Test basic installation instructions without milestone summary."""
    stdout, stderr, returncode = run_script(["1.2.0", "Vahidlari/aiApps"])

    assert returncode == 0
    assert "## 📦 Installation" in stdout
    assert "pip install ragora==1.2.0" in stdout
    assert "v1.2.0/ragora-1.2.0-py3-none-any.whl" in stdout
    assert "v1.2.0/ragora-1.2.0.tar.gz" in stdout
    assert "Vahidlari/aiApps" in stdout


@pytest.mark.unit
def test_with_milestone_summary(temp_dir, sample_milestone_content):
    """Test with milestone summary file."""
    # Create a temporary milestone summary file
    milestone_file = temp_dir / "milestone.md"
    milestone_file.write_text(sample_milestone_content)

    stdout, stderr, returncode = run_script(
        ["1.2.0", "Vahidlari/aiApps", str(milestone_file)]
    )

    assert returncode == 0
    assert "## 📦 Installation" in stdout
    assert "## Milestone Summary" in stdout
    assert "Issues Closed" in stdout
    assert "Pull Requests Merged" in stdout


@pytest.mark.unit
def test_missing_milestone_file():
    """Test with missing milestone summary file (should not fail)."""
    stdout, stderr, returncode = run_script(
        ["1.2.0", "Vahidlari/aiApps", "/nonexistent/file.md"]
    )

    assert returncode == 0
    assert "## 📦 Installation" in stdout
    assert "Warning" in stderr or "not found" in stderr.lower()


@pytest.mark.unit
def test_different_versions():
    """Test with different version formats."""
    test_cases = [
        ("1.0.0", "User/Repo"),
        ("2.5.3", "OrgName/ProjectName"),
        ("0.1.0-alpha", "Test/Test"),
    ]

    for version, repo in test_cases:
        stdout, stderr, returncode = run_script([version, repo])

        assert returncode == 0
        assert f"ragora=={version}" in stdout
        assert f"v{version}/ragora-{version}" in stdout
        assert repo in stdout


@pytest.mark.unit
def test_no_arguments():
    """Test script fails gracefully with no arguments."""
    stdout, stderr, returncode = run_script([], expect_success=False)

    assert returncode != 0
    assert "version" in stderr.lower() or "required" in stderr.lower()


@pytest.mark.unit
def test_missing_repository():
    """Test script fails gracefully with missing repository argument."""
    stdout, stderr, returncode = run_script(["1.0.0"], expect_success=False)

    assert returncode != 0
    assert "repository" in stderr.lower() or "required" in stderr.lower()


@pytest.mark.unit
def test_output_format():
    """Test that output is valid markdown format."""
    stdout, stderr, returncode = run_script(["1.0.0", "Test/Repo"])

    assert returncode == 0
    # Check markdown structure
    assert "##" in stdout  # Has headers
    assert "```bash" in stdout  # Has code blocks
    assert "pip install" in stdout  # Has installation commands


@pytest.mark.unit
def test_with_existing_milestone_fixture(fixtures_dir):
    """Test with the sample milestone fixture."""
    milestone_file = fixtures_dir / "sample_milestone.md"

    if milestone_file.exists():
        stdout, stderr, returncode = run_script(
            ["1.2.0", "Vahidlari/aiApps", str(milestone_file)]
        )

        assert returncode == 0
        assert "## 📦 Installation" in stdout
        assert "Milestone Summary" in stdout


@pytest.mark.integration
def test_script_as_module():
    """Test that script can be imported as a module."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("format_release_notes", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Test the functions
    instructions = module.format_installation_instructions("1.0.0", "Test/Repo")
    assert "pip install ragora==1.0.0" in instructions

    # Test milestone reading
    result = module.read_milestone_summary("/nonexistent/file.md")
    assert result is None
