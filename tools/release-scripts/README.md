# Release Helper Scripts

This directory contains helper scripts used by the GitHub Actions release workflow. These scripts are designed to be testable, maintainable, and runnable locally without GitHub-specific dependencies.

## Overview

The release scripts handle key parts of the release process:
- Checking for release-worthy commits based on conventional commits
- Building Python packages with proper versioning
- Creating database server archives
- Formatting release notes
- Managing version metadata

All scripts follow clean architecture principles:
- Separated concerns
- Testable in isolation
- No direct GitHub API dependencies (GitHub-specific logic remains in workflow)
- Can run locally for testing

## Scripts

### `check-release-commits.sh`

Checks if there are release-worthy commits since the last tag based on conventional commit patterns.

**Usage:**
```bash
check-release-commits.sh <last_tag> [target_ref]
```

**Example:**
```bash
bash check-release-commits.sh v1.0.0 HEAD
```

**Behavior:**
- Returns exit code 0 if release-worthy commits found
- Returns exit code 1 if no release-worthy commits
- Prints found commits to stdout

**Detects:**
- Conventional commit types: `feat`, `fix`, `perf`, `refactor`, `style`, `docs`, `test`, `build`, `ci`, `chore`
- Breaking changes marked with `!` or `BREAKING CHANGE`
- Commits with scopes: `feat(api):`

---

### `build-python-package.sh`

Builds Python package with proper version handling for dry-run mode.

**Usage:**
```bash
build-python-package.sh <version> <dry_run_flag> [work_dir]
```

**Example:**
```bash
# Normal build
bash build-python-package.sh 1.2.0 false ./ragora

# Dry-run build (creates temporary tag for setuptools_scm)
bash build-python-package.sh 1.2.0 true ./ragora
```

**Behavior:**
- Cleans up any previous `dist/` directory
- In dry-run mode: Creates temporary git tag for setuptools_scm, then cleans up
- Validates working directory contains `pyproject.toml` or `setup.py`
- Runs `python -m build`
- Checks for build artifacts (`.whl` and `.tar.gz` files)
- Succeeds if artifacts are created, even if build command had warnings
- Lists built packages

**Note:** The script tolerates non-zero exit codes from `python -m build` as long as the build artifacts are created. This handles cases where git-related warnings (like "listing git files failed") occur but don't prevent package creation.

---

### `create-db-archives.sh`

Creates database server archives with version metadata.

**Usage:**
```bash
create-db-archives.sh <version> <git_commit> <git_branch> <repository>
```

**Example:**
```bash
bash create-db-archives.sh 1.2.0 abc123def main Vahidlari/aiApps
```

**Creates:**
- `database_server-{version}.tar.gz` - tar.gz archive
- `database_server-{version}.zip` - zip archive (if zip command available)
- Version metadata files (via helper scripts)
- Updated README with version info

**Excludes from archives:**
- `*.pyc` files
- `__pycache__` directories
- `.git` directory
- `node_modules`
- `*.log` and `*.tmp` files

**Prints:** Archive filenames to stdout for workflow capture

---

### `format-release-notes.py`

Formats release notes with installation instructions and optional milestone summary.

**Usage:**
```bash
python format-release-notes.py <version> <repository> [milestone_summary_file]
```

**Example:**
```bash
# Without milestone summary
python format-release-notes.py 1.2.0 Vahidlari/aiApps

# With milestone summary
python format-release-notes.py 1.2.0 Vahidlari/aiApps milestone_summary.md
```

**Output:** Formatted markdown to stdout with:
- PyPI installation instructions
- GitHub release installation instructions
- Optional milestone summary

**Why Python:** Better string formatting, file I/O, and error handling for text processing compared to bash.

---

### `create-version-metadata.sh`

Creates version metadata files for database server releases.

**Usage:**
```bash
create-version-metadata.sh <version> <git_commit> <git_branch> <repository>
```

**Example:**
```bash
bash create-version-metadata.sh 1.0.0 abc123def main Vahidlari/aiApps
```

**Creates:**
- `tools/database_server/config/VERSION` - Simple version file
- `tools/database_server/config/release-info.json` - Complete release metadata

**Output Files:**

`VERSION`:
```
1.0.0
```

`release-info.json`:
```json
{
  "version": "1.0.0",
  "release_date": "2024-01-15T10:30:00Z",
  "git_tag": "v1.0.0",
  "git_commit": "abc123def",
  "git_branch": "main",
  "release_url": "https://github.com/Vahidlari/aiApps/releases/tag/v1.0.0",
  "repository": "Vahidlari/aiApps"
}
```

---

### `update-readme-version.sh`

Updates the database server README with version information.

**Usage:**
```bash
update-readme-version.sh <version> <repository>
```

**Example:**
```bash
bash update-readme-version.sh 1.0.0 Vahidlari/aiApps
```

**Actions:**
1. Updates the README header to include version: `# Ragora Database Server - v1.0.0`
2. Adds a "Release Information" section at the end with:
   - Link to VERSION file
   - Link to release-info.json
   - Link to documentation

---

## Testing

### Automated Test Suite

All scripts have comprehensive test coverage. The test infrastructure is completely independent from the ragora project tests.

**Test Structure:**
```
tools/release-scripts/tests/
├── test-*.sh              # Bash tests for bash scripts
├── test_*.py              # pytest tests for Python scripts
├── pytest.ini             # pytest configuration (independent)
├── conftest.py            # pytest fixtures
├── run_tests.sh           # Master test runner
└── fixtures/              # Test data
```

**Running Tests:**

```bash
# Run all tests (bash + Python)
cd tools/release-scripts/tests
bash run_tests.sh

# Run with verbose output
bash run_tests.sh -v

# Run specific test
bash run_tests.sh -t test-check-commits.sh

# Run only bash tests
bash run_tests.sh --bash-only

# Run only Python tests
bash run_tests.sh --python-only
```

**Test Features:**
- Bash tests: Simple, no external dependencies
- Python tests: pytest with proper fixtures
- Master test runner provides comprehensive summary
- All tests can run locally without GitHub environment
- Exit code 0 if all pass, 1 if any fail

### Manual Testing Locally

You can also test scripts manually before a release:

```bash
# From the repository root
cd /workspaces/aiApps

# Test checking release commits
bash tools/release-scripts/check-release-commits.sh v1.0.0 HEAD

# Test format release notes
python tools/release-scripts/format-release-notes.py 1.2.0 Vahidlari/aiApps

# Test metadata creation
bash tools/release-scripts/create-version-metadata.sh \
  "1.0.0-test" \
  "abc123" \
  "test-branch" \
  "Vahidlari/aiApps"

# Test README update
bash tools/release-scripts/update-readme-version.sh \
  "1.0.0-test" \
  "Vahidlari/aiApps"

# Check the results
cat tools/database_server/config/VERSION
cat tools/database_server/config/release-info.json

# Clean up test files
rm tools/database_server/config/VERSION
rm tools/database_server/config/release-info.json
git restore tools/database_server/README.md
```

---

## Integration with GitHub Actions

These scripts are called by the `.github/workflows/milestone-release.yml` workflow:

```yaml
# Check for release-worthy commits
- name: Check for release-worthy commits
  run: |
    if bash tools/release-scripts/check-release-commits.sh "${{ steps.get_last_tag.outputs.tag }}" "HEAD"; then
      echo "has_release_commits=true" >> $GITHUB_OUTPUT
    else
      echo "has_release_commits=false" >> $GITHUB_OUTPUT
    fi

# Build Python package
- name: Build Python package
  working-directory: ./ragora
  run: |
    bash ../tools/release-scripts/build-python-package.sh \
      "${{ steps.semantic_release.outputs.new_release_version }}" \
      "${{ needs.check-milestone.outputs.dry_run }}"

# Create database server archives
- name: Create database server archive
  run: |
    bash tools/release-scripts/create-db-archives.sh \
      "$VERSION" \
      "${{ github.sha }}" \
      "${{ github.ref_name }}" \
      "${{ github.repository }}"

# Format release notes
- name: Generate installation instructions
  run: |
    python tools/release-scripts/format-release-notes.py \
      "$VERSION" \
      "${{ github.repository }}" \
      milestone_summary.md
```

---

## Architecture Principles

### Clean Separation of Concerns

**Scripts handle:**
- Git operations
- File system operations
- Building and archiving
- Text formatting

**Workflow handles:**
- GitHub API interactions
- Milestone information
- Release creation and attachment
- Issue/PR management

### Design Decisions

1. **Bash for system operations:** Git commands, file operations, archive creation
2. **Python for text processing:** Complex string formatting, markdown generation
3. **No GitHub dependencies in scripts:** Scripts use only git and standard tools
4. **Test infrastructure independence:** Separate from ragora's test suite
5. **Testable design:** All scripts can be tested in isolation

---

## Benefits of This Approach

1. **Maintainability**: Scripts are easier to test and debug than inline YAML code
2. **Reusability**: Scripts can be used locally or in other workflows
3. **Readability**: Workflow file is ~100 lines shorter and clearer
4. **Testability**: Comprehensive test coverage with automated test runner
5. **Version Control**: Changes to scripts are easier to review and track
6. **Local Development**: Can test release process locally before pushing
7. **Clean Architecture**: Separated concerns, proper error handling

---

## Development Guidelines

### Adding New Scripts

When adding new release scripts:

1. **Choose the right language:**
   - Use bash for system operations, git commands, file operations
   - Use Python for complex text processing, data manipulation
   
2. **Follow the patterns:**
   - Add argument validation at the start
   - Use `set -euo pipefail` for bash scripts
   - Add usage examples in comments
   - Return appropriate exit codes
   
3. **Make it testable:**
   - Avoid hardcoded paths
   - Accept arguments instead of environment variables
   - Print results to stdout for workflow capture
   
4. **Write tests:**
   - Create corresponding test file (test-*.sh or test_*.py)
   - Test success cases, edge cases, error cases
   - Ensure tests clean up after themselves

### Script Conventions

**Bash scripts:**
- Start with `#!/bin/bash`
- Use `set -euo pipefail` for better error handling
- Include usage information in error messages
- Use descriptive variable names in UPPER_CASE
- Add emoji for better output readability (✅, ❌, 📦, 📝)

**Python scripts:**
- Start with `#!/usr/bin/env python3`
- Use argparse for argument parsing
- Include docstrings
- Type hints where appropriate
- Output to stdout for piping

---

## Troubleshooting

### Script not executable

If you get a "Permission denied" error:
```bash
chmod +x tools/release-scripts/*.sh tools/release-scripts/*.py
```

### Script can't find database_server directory

Some scripts look for database_server relative to their location. Ensure the directory structure is correct, or that you're running from the expected location.

### Tests fail locally

1. Ensure you're in the tests directory: `cd tools/release-scripts/tests`
2. Check that scripts are executable: `chmod +x ../*.sh`
3. Run with verbose flag: `bash run_tests.sh -v`

### Python script import errors

The Python test infrastructure is separate from ragora. If you get import errors:
```bash
# Install pytest in your environment
pip install pytest
```

### JSON syntax errors

The scripts use here-documents with proper EOF delimiters. If you modify them, ensure:
- The opening `<<EOF` has no spaces before EOF
- The closing `EOF` is on its own line with no spaces or tabs
- No extra indentation before the closing EOF

