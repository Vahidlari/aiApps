# Ragora Test Suite

This directory contains the comprehensive test suite for Ragora.

## Quick Start

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=ragora --cov-report=html

# Run specific test types
python -m pytest tests/unit/          # Unit tests only
python -m pytest tests/integration/  # Integration tests only
```

## Test Structure

```
tests/
├── unit/          # Unit tests for individual components
├── integration/   # Integration tests for component interactions
├── fixtures/      # Test data and sample files
└── utils/         # Test utilities and helpers
```

## Documentation

For comprehensive testing documentation, including:
- Writing new tests
- Test organization and best practices
- Using fixtures and mocks
- Performance testing
- Debugging tests

See **[docs/testing.md](../docs/testing.md)** for complete details.

## Common Commands

```bash
# Run specific test file
python -m pytest tests/unit/test_data_chunker.py

# Run with verbose output
python -m pytest -v

# Run tests matching pattern
python -m pytest -k "chunker"

# Skip slow tests
python -m pytest -m "not slow"
```

## Contributing

When adding new tests, please follow the guidelines in [docs/contributing.md](../docs/contributing.md).
