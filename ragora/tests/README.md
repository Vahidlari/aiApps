# RAG System Test Suite

This directory contains comprehensive tests for the RAG system, organized into unit tests, integration tests, and test utilities.

## Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and shared fixtures
├── run_tests.py                   # Test runner script
├── unit/                          # Unit tests for individual components
│   ├── test_dataclasses.py       # Tests for data structures
│   ├── test_latex_parser.py      # Tests for LaTeX parser
│   └── test_config.py            # Tests for configuration management
├── integration/                   # Integration tests
│   └── test_document_parsing.py  # End-to-end document processing tests
├── fixtures/                      # Test data and sample files
│   ├── sample_latex.tex          # Sample LaTeX document
│   ├── sample_bibliography.bib   # Sample bibliography
│   └── expected_outputs/         # Expected parsing results
└── utils/                         # Test utilities and helpers
    └── test_helpers.py           # Helper functions for testing
```

## Running Tests

### Quick Start

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=ragora --cov-report=html

# Run specific test types
python -m pytest -m unit          # Unit tests only
python -m pytest -m integration   # Integration tests only
python -m pytest -m "not slow"    # Skip slow tests
```

### Using the Test Runner Script

```bash
# Run all tests
python tests/run_tests.py

# Run unit tests only
python tests/run_tests.py --type unit

# Run with coverage report
python tests/run_tests.py --coverage

# Run with HTML coverage report
python tests/run_tests.py --html-coverage

# Run tests in parallel (requires pytest-xdist)
python tests/run_tests.py --parallel 4

# Skip slow tests
python tests/run_tests.py --fast
```

### Test Categories

#### Unit Tests (`-m unit`)
- **Data Classes**: Test all dataclass structures (Citation, LatexParagraph, etc.)
- **LaTeX Parser**: Test individual parsing methods and functions
- **Configuration**: Test config loading, validation, and defaults

#### Integration Tests (`-m integration`)
- **Document Parsing**: End-to-end document processing workflows
- **Error Recovery**: Handling of malformed or incomplete documents
- **Performance**: Processing time and memory usage tests

#### Slow Tests (`-m slow`)
- **Large Documents**: Processing of very large LaTeX files
- **Performance Benchmarks**: Detailed performance analysis
- **Stress Tests**: Processing multiple documents simultaneously

## Test Data

### Sample Files
- `sample_latex.tex`: Complete LaTeX document with various structures
- `sample_bibliography.bib`: Bibliography file with multiple entry types
- `expected_outputs/`: JSON files with expected parsing results

### Fixtures
The `conftest.py` file provides pytest fixtures for:
- Sample LaTeX content
- Sample bibliography content
- Temporary file creation
- Mock objects and data structures

## Writing New Tests

### Unit Test Example

```python
def test_parse_single_section():
    """Test parsing a single section."""
    parser = LatexParser()
    section_text = """
\\section{Test Section}
This is the content of the test section.
"""
    section = parser._parse_single_section(section_text)
    
    assert section is not None
    assert section.title == "Test Section"
    assert len(section.paragraphs) > 0
```

### Integration Test Example

```python
def test_parse_complete_document_with_bibliography():
    """Test parsing a complete document with bibliography."""
    parser = LatexParser(
        document_path="sample.tex",
        bibliography_path="sample.bib"
    )
    
    document = parser.document
    assert document is not None
    assert document.title == "Sample Document"
    assert len(document.sections) > 0
```

### Using Fixtures

```python
def test_parser_with_sample_content(sample_latex_content, latex_parser):
    """Test parser with sample content."""
    document = latex_parser.parse_document_text(sample_latex_content)
    assert document is not None
    assert document.title == "Sample Document"
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Test discovery patterns
- Output formatting
- Markers for test categorization
- Timeout settings
- Warning filters

### Coverage Configuration
- Source code coverage tracking
- HTML and terminal reports
- Minimum coverage thresholds

## Best Practices

### Test Organization
1. **One test file per module**: Mirror the source code structure
2. **Descriptive test names**: Use clear, descriptive function names
3. **Group related tests**: Use classes to group related test methods
4. **Use fixtures**: Leverage pytest fixtures for common setup

### Test Quality
1. **Test edge cases**: Include tests for error conditions and edge cases
2. **Mock external dependencies**: Use mocks for file I/O, network calls, etc.
3. **Assert specific conditions**: Make specific assertions rather than generic ones
4. **Clean up resources**: Ensure temporary files and resources are cleaned up

### Performance
1. **Mark slow tests**: Use `@pytest.mark.slow` for tests that take >1 second
2. **Use parallel execution**: Run independent tests in parallel when possible
3. **Optimize test data**: Use minimal test data that still covers the functionality

## Continuous Integration

The test suite is designed to work with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    python -m pytest --cov=ragora --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the RAG system package is installed or in PYTHONPATH
2. **File Not Found**: Check that test fixtures exist in the correct locations
3. **Timeout Errors**: Increase timeout in pytest.ini for slow tests
4. **Coverage Issues**: Ensure all source files are included in coverage analysis

### Debug Mode

```bash
# Run tests with debug output
python -m pytest -vvv --tb=long

# Run specific test with debug
python -m pytest -vvv tests/unit/test_latex_parser.py::TestLatexParser::test_parse_document -s
```

## Contributing

When adding new tests:

1. Follow the existing naming conventions
2. Add appropriate markers (`@pytest.mark.unit`, `@pytest.mark.integration`, etc.)
3. Update this README if adding new test categories
4. Ensure tests pass in both local and CI environments
5. Add test data to fixtures if needed
