# Tools Scripts

This directory contains utility scripts for the AI Apps project.

## Available Scripts

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
