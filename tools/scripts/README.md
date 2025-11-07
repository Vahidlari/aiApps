# Tools Scripts

This directory contains utility scripts for the AI Apps project.

## Available Scripts

### `build-docs.sh`

Builds the MkDocs documentation site into the published `docs/` directory.

**Usage:**
```bash
# From repository root
./tools/scripts/build-docs.sh
```

**Prerequisites:**
- Install documentation dependencies: `pip install -e "ragora[docs]"`

**What it does:**
- Runs `mkdocs build` using the configuration at the repo root
- Outputs the static site to `docs/` for GitHub Pages serving

### `verify_test_setup.py`

Verifies that the test environment is working correctly for the RAG system.

**Usage:**
```bash
# From the rag_system directory
python ../../tools/scripts/verify_test_setup.py

# Or from anywhere in the project
python /workspaces/aiApps/tools/scripts/verify_test_setup.py
```

**What it does:**
- Verifies pytest can discover tests
- Checks test execution capabilities  
- Validates import paths
- Confirms VS Code/Cursor Test Explorer setup
- Provides clear success/failure feedback

**When to use:**
- Setting up a new development environment
- Troubleshooting test discovery issues
- Verifying Test Explorer functionality
- Debugging import path problems
