"""Tests for version parsing and handling."""

import pytest

from ragora.version import __version__, __version_info__


class TestVersionParsing:
    """Tests for version parsing functionality."""

    def test_version_is_string(self):
        """Test that __version__ is a string."""
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_version_info_is_tuple(self):
        """Test that __version_info__ is a tuple."""
        assert isinstance(__version_info__, tuple)
        assert len(__version_info__) >= 3

    def test_version_info_has_numeric_parts(self):
        """Test that version_info has at least 3 numeric parts."""
        assert all(isinstance(part, int) for part in __version_info__[:3])

    def test_stable_version_format(self):
        """Test that stable versions are parsed correctly."""
        # This test will pass if the version is stable (e.g., 1.1.0)
        # For stable versions, version_info should be (major, minor, patch)
        if len(__version_info__) == 3:
            major, minor, patch = __version_info__
            assert isinstance(major, int)
            assert isinstance(minor, int)
            assert isinstance(patch, int)
            # Verify version string matches
            expected_version = f"{major}.{minor}.{patch}"
            assert __version__.startswith(expected_version)

    def test_prerelease_version_format(self):
        """Test that prerelease versions are parsed correctly."""
        # This test will pass if the version is a prerelease (e.g., 1.2.0-rc1)
        # For prerelease versions, version_info should be (major, minor, patch, prerelease)
        if len(__version_info__) == 4:
            major, minor, patch, prerelease = __version_info__
            assert isinstance(major, int)
            assert isinstance(minor, int)
            assert isinstance(patch, int)
            assert isinstance(prerelease, str)
            # Verify prerelease identifier is valid
            assert prerelease.startswith(("rc", "alpha", "beta", "dev"))
            # Verify version string contains prerelease info
            assert "-" in __version__ or any(
                marker in __version__ for marker in ["rc", "alpha", "beta", "dev"]
            )


class TestVersionParsingLogic:
    """Tests for version parsing logic with various formats."""

    def test_parse_stable_version(self):
        """Test parsing a stable version string."""
        # Import the parsing function from _version if available
        try:
            from ragora._version import _parse_version

            result = _parse_version("1.2.0")
            assert result == (1, 2, 0)
        except ImportError:
            # Skip if _version.py is not available (development mode)
            pytest.skip("_version.py not available in development mode")

    def test_parse_prerelease_with_hyphen(self):
        """Test parsing a prerelease version with hyphen (e.g., 1.2.0-rc1)."""
        try:
            from ragora._version import _parse_version

            result = _parse_version("1.2.0-rc1")
            assert result == (1, 2, 0, "rc1")
        except ImportError:
            pytest.skip("_version.py not available in development mode")

    def test_parse_prerelease_without_separator(self):
        """Test parsing a prerelease version without separator (e.g., 1.2.0rc1)."""
        try:
            from ragora._version import _parse_version

            result = _parse_version("1.2.0rc1")
            assert result == (1, 2, 0, "rc1")
        except ImportError:
            pytest.skip("_version.py not available in development mode")

    def test_parse_alpha_version(self):
        """Test parsing an alpha version."""
        try:
            from ragora._version import _parse_version

            result = _parse_version("1.2.0-alpha1")
            assert result == (1, 2, 0, "alpha1")

            result2 = _parse_version("1.2.0a1")
            assert result2 == (1, 2, 0, "alpha1")
        except ImportError:
            pytest.skip("_version.py not available in development mode")

    def test_parse_beta_version(self):
        """Test parsing a beta version."""
        try:
            from ragora._version import _parse_version

            result = _parse_version("1.2.0-beta1")
            assert result == (1, 2, 0, "beta1")

            result2 = _parse_version("1.2.0b1")
            assert result2 == (1, 2, 0, "beta1")
        except ImportError:
            pytest.skip("_version.py not available in development mode")

    def test_parse_dev_version(self):
        """Test parsing a development version."""
        try:
            from ragora._version import _parse_version

            result = _parse_version("1.2.0.dev1")
            assert result == (1, 2, 0, "dev1")
        except ImportError:
            pytest.skip("_version.py not available in development mode")

    def test_parse_multiple_prerelease_numbers(self):
        """Test parsing versions with multiple digit prerelease numbers."""
        try:
            from ragora._version import _parse_version

            result = _parse_version("1.2.0-rc10")
            assert result == (1, 2, 0, "rc10")
        except ImportError:
            pytest.skip("_version.py not available in development mode")
