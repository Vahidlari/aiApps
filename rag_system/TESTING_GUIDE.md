# 🧪 Pytest Testing Guide for RAG System

This guide covers all the ways to run and debug pytest tests in Cursor with fine-grained control.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Debugging Options](#debugging-options)
- [Execution Methods](#execution-methods)
- [Configuration Files](#configuration-files)
- [Helper Scripts](#helper-scripts)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### 1. Using the Test Explorer (Recommended)
- Open the **Test Explorer** panel in Cursor (View → Test Explorer)
- Tests are automatically discovered and organized by file/class
- Click the play button next to any test to run it
- Click the debug button to debug a specific test

### 2. Using Command Palette
- Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
- Type "Python: Run Test" or "Python: Debug Test"
- Select the test you want to run/debug

### 3. Using CodeLens (Inline)
- Open any test file (e.g., `test_dataclasses.py`)
- You'll see "Run Test" and "Debug Test" links above each test function
- Click these links to run/debug individual tests

## 🐛 Debugging Options

### Launch Configurations (F5)

Press `F5` or go to Run → Start Debugging to access these configurations:

#### 1. **Debug Current Test**
- Runs the specific test function you're currently viewing
- Prompts for test function name if not in a test file
- **Use case**: Debug a specific failing test

#### 2. **Debug Current Test File**
- Runs all tests in the currently open test file
- **Use case**: Debug all tests in a specific file

#### 3. **Debug Test Class**
- Runs all tests in a specific test class
- Prompts for class name
- **Use case**: Debug all tests in a class (e.g., `TestCitation`)

#### 4. **Debug All Unit Tests**
- Runs all tests marked with `@pytest.mark.unit`
- **Use case**: Debug all unit tests

#### 5. **Debug All Integration Tests**
- Runs all tests marked with `@pytest.mark.integration`
- **Use case**: Debug all integration tests

#### 6. **Debug Tests by Pattern**
- Runs tests matching a pattern (e.g., `test_citation*`)
- Prompts for pattern
- **Use case**: Debug tests with similar names

#### 7. **Debug Failed Tests Only**
- Runs only tests that failed in the last run
- **Use case**: Re-run and debug failing tests

#### 8. **Debug with Coverage**
- Runs tests with coverage reporting
- **Use case**: Debug while checking code coverage

### Debugging Features
- **Breakpoints**: Click in the gutter to set breakpoints
- **Step Through**: Use F10 (step over), F11 (step into), Shift+F11 (step out)
- **Variables**: Inspect variables in the Debug Console
- **Call Stack**: View the call stack in the Debug panel
- **Watch**: Add expressions to watch in the Debug panel

## ⚡ Execution Methods

### 1. Tasks (Ctrl+Shift+P → "Tasks: Run Task")

#### Available Tasks:
- **Run Current Test File**: Run tests in the current file
- **Run All Unit Tests**: Run all unit tests
- **Run All Integration Tests**: Run all integration tests
- **Run All Tests**: Run all tests
- **Run Tests with Coverage**: Run with coverage report
- **Run Failed Tests Only**: Run only failed tests
- **Run Tests by Pattern**: Run tests matching a pattern
- **Run Slow Tests**: Run tests marked as slow
- **Run Performance Tests**: Run performance tests
- **Clean Test Cache**: Clear pytest cache
- **Install Test Dependencies**: Install required packages

### 2. Terminal Commands

#### Basic pytest commands:
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/unit/test_dataclasses.py -v

# Run specific test function
python -m pytest tests/unit/test_dataclasses.py::TestCitation::test_citation_creation -v

# Run tests by pattern
python -m pytest -k "test_citation" -v

# Run with coverage
python -m pytest tests/ --cov=rag_system --cov-report=html

# Run failed tests only
python -m pytest --lf -v

# Run in parallel (requires pytest-xdist)
python -m pytest tests/ -n 4
```

### 3. Test Environment Verification

#### Verify Test Setup:
```bash
# Verify that the test environment is working correctly
python ../../tools/scripts/verify_test_setup.py
```

This script helps diagnose test environment issues and verifies that VS Code/Cursor Test Explorer is working properly.

## ⚙️ Configuration Files

### 1. `.vscode/launch.json`
Contains debug configurations for different test scenarios.

### 2. `.vscode/settings.json`
Configures Python testing, linting, and editor settings.

### 3. `.vscode/tasks.json`
Defines automated tasks for common test operations.

### 4. `pytest.ini`
Main pytest configuration with markers, options, and settings.

## 🛠️ Helper Scripts

### `tools/scripts/verify_test_setup.py`
Test environment verification script:
- Verifies pytest can discover tests
- Checks test execution capabilities
- Validates import paths
- Confirms VS Code/Cursor Test Explorer setup
- Provides clear success/failure feedback

## 🎯 Best Practices

### 1. Test Organization
- Use descriptive test names
- Group related tests in classes
- Use appropriate markers (`@pytest.mark.unit`, `@pytest.mark.integration`)
- Keep tests focused and independent

### 2. Debugging Workflow
1. **Start with Test Explorer**: Use the visual interface for quick test runs
2. **Use CodeLens**: Click "Debug Test" above individual tests
3. **Set Breakpoints**: Place breakpoints in test code or source code
4. **Use Debug Console**: Inspect variables and run expressions
5. **Step Through Code**: Use F10/F11 to step through execution

### 3. Performance Tips
- Use `--lf` to run only failed tests during development
- Use `-k` pattern matching for focused testing
- Use parallel execution (`-n`) for large test suites
- Use `--tb=short` for cleaner output

### 4. Coverage Analysis
- Run coverage regularly: `python -m pytest --cov=rag_system --cov-report=html`
- Check HTML reports in `htmlcov/index.html`
- Aim for high coverage but focus on critical paths
- Use `--cov-report=term-missing` to see uncovered lines

## 🔧 Troubleshooting

### Common Issues:

#### 1. Tests Not Discovered
- Check `pytest.ini` configuration
- Ensure test files follow naming convention (`test_*.py`)
- Verify test functions start with `test_`
- Check `PYTHONPATH` is set correctly

#### 2. Import Errors
- Ensure virtual environment is activated
- Check `PYTHONPATH` includes the project root
- Verify all dependencies are installed

#### 3. Debugger Not Working
- Check `justMyCode: false` in launch configurations
- Ensure breakpoints are set in the correct files
- Try restarting the debugger

#### 4. Slow Test Execution
- Use `--lf` to run only failed tests
- Use parallel execution with `-n`
- Profile tests to identify bottlenecks
- Consider using `@pytest.mark.slow` for long-running tests

### Getting Help:
- Check pytest documentation: https://docs.pytest.org/
- Use `python -m pytest --help` for all options
- Check the Test Explorer panel for test discovery issues
- Use the Debug Console for interactive debugging

## 📊 Test Markers

The project uses these pytest markers:

- `@pytest.mark.unit`: Unit tests for individual components
- `@pytest.mark.integration`: Integration tests for end-to-end workflows
- `@pytest.mark.slow`: Tests that take a long time to run
- `@pytest.mark.performance`: Performance and benchmark tests
- `@pytest.mark.regression`: Regression tests for bug fixes

Use these markers to run specific types of tests:
```bash
python -m pytest -m unit
python -m pytest -m "not slow"
python -m pytest -m "unit or integration"
```

---

Happy Testing! 🎉
