#!/usr/bin/env python3
"""
Format release notes with installation instructions and milestone summary.

This script generates formatted markdown for GitHub releases, including
PyPI and GitHub installation instructions, optionally appending milestone
summary information.

Usage:
    python format-release-notes.py <version> <repository> [milestone_summary_file]

Example:
    python format-release-notes.py 1.2.0 Vahidlari/aiApps milestone_summary.md
"""

import argparse
import sys
from pathlib import Path
from typing import Optional


def format_installation_instructions(version: str, repository: str) -> str:
    """
    Generate formatted installation instructions for PyPI and GitHub releases.

    Args:
        version: The release version (e.g., "1.2.0")
        repository: The repository name (e.g., "Vahidlari/aiApps")

    Returns:
        Formatted markdown string with installation instructions
    """
    instructions = f"""## 📦 Installation

### From PyPI
```bash
# Install specific version
pip install ragora=={version}
```

### From GitHub Releases (Alternative)
```bash
# Install wheel directly
pip install https://github.com/{repository}/releases/download/v{version}/ragora-{version}-py3-none-any.whl

# Or install from source
pip install https://github.com/{repository}/releases/download/v{version}/ragora-{version}.tar.gz
```"""

    return instructions


def read_milestone_summary(filepath: Optional[str]) -> Optional[str]:
    """
    Read milestone summary from a file if provided.

    Args:
        filepath: Path to the milestone summary markdown file

    Returns:
        Content of the file or None if not provided/not found
    """
    if not filepath:
        return None

    path = Path(filepath)
    if not path.exists():
        print(f"Warning: Milestone summary file not found: {filepath}", file=sys.stderr)
        return None

    try:
        return path.read_text().strip()
    except Exception as e:
        print(f"Warning: Error reading milestone summary: {e}", file=sys.stderr)
        return None


def format_release_notes(
    version: str, repository: str, milestone_summary_file: Optional[str] = None
) -> str:
    """
    Generate complete release notes with installation instructions and optional milestone summary.

    Args:
        version: The release version
        repository: The repository name
        milestone_summary_file: Optional path to milestone summary file

    Returns:
        Complete formatted markdown for release notes
    """
    # Generate installation instructions
    instructions = format_installation_instructions(version, repository)

    # Read milestone summary if provided
    milestone_summary = read_milestone_summary(milestone_summary_file)

    # Combine sections
    if milestone_summary:
        return f"{instructions}\n\n{milestone_summary}"
    else:
        return instructions


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Format release notes with installation instructions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 1.2.0 Vahidlari/aiApps
  %(prog)s 1.2.0 Vahidlari/aiApps milestone_summary.md
        """,
    )

    parser.add_argument("version", help="Release version (e.g., 1.2.0)")

    parser.add_argument("repository", help="Repository name (e.g., Vahidlari/aiApps)")

    parser.add_argument(
        "milestone_summary_file",
        nargs="?",
        default=None,
        help="Optional path to milestone summary markdown file",
    )

    args = parser.parse_args()

    # Generate and print release notes
    release_notes = format_release_notes(
        args.version, args.repository, args.milestone_summary_file
    )

    print(release_notes)


if __name__ == "__main__":
    main()
