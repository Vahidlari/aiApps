"""
Pytest configuration for release-scripts tests.
Completely independent from ragora's test infrastructure.
"""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_milestone_content():
    """Return sample milestone summary content."""
    return """## Milestone Summary

### Issues Closed
- #123 Add new feature
- #124 Fix bug in parser

### Pull Requests Merged
- #125 Implement feature X
- #126 Update documentation

*Milestone: v1.0.0 Release*
"""
