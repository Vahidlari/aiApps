"""Unit tests for FilterBuilder class.

This module contains comprehensive unit tests for the FilterBuilder class,
testing all helper methods for constructing Weaviate filters.
"""

import pytest
from weaviate.classes.query import Filter

from ragora.core.filters import FilterBuilder


def _is_filter_compatible(obj):
    """Check if object is compatible with Weaviate Filter API."""
    # Weaviate v4 returns internal filter classes that are compatible
    # but not direct Filter instances. Check for filter-like objects.
    if obj is None:
        return False
    # Check if it's a filter-like object (has filter attributes or is a filter type)
    filter_types = (
        "_FilterValue",
        "_FilterAnd",
        "_FilterOr",
        "Filter",
    )
    class_name = type(obj).__name__
    return any(ft in class_name for ft in filter_types)


class TestFilterBuilder:
    """Test suite for FilterBuilder class."""

    def test_by_chunk_type(self):
        """Test filtering by chunk type."""
        filter_obj = FilterBuilder.by_chunk_type("text")
        assert filter_obj is not None
        # Weaviate v4 Filter objects are not direct Filter instances
        # but are compatible filter objects

    def test_by_source_document(self):
        """Test filtering by source document."""
        filter_obj = FilterBuilder.by_source_document("document.pdf")
        assert _is_filter_compatible(filter_obj)

    def test_by_email_sender(self):
        """Test filtering by email sender."""
        filter_obj = FilterBuilder.by_email_sender("sender@example.com")
        assert _is_filter_compatible(filter_obj)

    def test_by_email_subject(self):
        """Test filtering by email subject."""
        filter_obj = FilterBuilder.by_email_subject("Test Subject")
        assert _is_filter_compatible(filter_obj)

    def test_by_email_folder(self):
        """Test filtering by email folder."""
        filter_obj = FilterBuilder.by_email_folder("Inbox")
        assert _is_filter_compatible(filter_obj)

    def test_by_email_recipient(self):
        """Test filtering by email recipient."""
        filter_obj = FilterBuilder.by_email_recipient("recipient@example.com")
        assert _is_filter_compatible(filter_obj)

    def test_by_date_range_start_only(self):
        """Test filtering by date range with start date only."""
        filter_obj = FilterBuilder.by_date_range(start="2024-01-01")
        assert _is_filter_compatible(filter_obj)
        assert filter_obj is not None

    def test_by_date_range_end_only(self):
        """Test filtering by date range with end date only."""
        filter_obj = FilterBuilder.by_date_range(end="2024-12-31")
        assert _is_filter_compatible(filter_obj)
        assert filter_obj is not None

    def test_by_date_range_both(self):
        """Test filtering by date range with both start and end dates."""
        filter_obj = FilterBuilder.by_date_range(start="2024-01-01", end="2024-12-31")
        assert _is_filter_compatible(filter_obj)
        assert filter_obj is not None

    def test_by_date_range_none(self):
        """Test filtering by date range with no dates."""
        filter_obj = FilterBuilder.by_date_range()
        assert filter_obj is None

    def test_by_email_date_range_start_only(self):
        """Test filtering by email date range with start date only."""
        filter_obj = FilterBuilder.by_email_date_range(start="2024-01-01")
        assert _is_filter_compatible(filter_obj)
        assert filter_obj is not None

    def test_by_email_date_range_end_only(self):
        """Test filtering by email date range with end date only."""
        filter_obj = FilterBuilder.by_email_date_range(end="2024-12-31")
        assert _is_filter_compatible(filter_obj)
        assert filter_obj is not None

    def test_by_email_date_range_both(self):
        """Test filtering by email date range with both start and end dates."""
        filter_obj = FilterBuilder.by_email_date_range(
            start="2024-01-01", end="2024-12-31"
        )
        assert _is_filter_compatible(filter_obj)
        assert filter_obj is not None

    def test_by_email_date_range_none(self):
        """Test filtering by email date range with no dates."""
        filter_obj = FilterBuilder.by_email_date_range()
        assert filter_obj is None

    def test_by_page_number(self):
        """Test filtering by page number."""
        filter_obj = FilterBuilder.by_page_number(5)
        assert _is_filter_compatible(filter_obj)

    def test_by_section_title(self):
        """Test filtering by section title."""
        filter_obj = FilterBuilder.by_section_title("Introduction")
        assert _is_filter_compatible(filter_obj)

    def test_by_chunk_idx(self):
        """Test filtering by chunk index."""
        filter_obj = FilterBuilder.by_chunk_idx(10)
        assert _is_filter_compatible(filter_obj)

    def test_combine_and_single_filter(self):
        """Test combining filters with AND logic (single filter)."""
        filter1 = FilterBuilder.by_chunk_type("text")
        combined = FilterBuilder.combine_and(filter1)
        assert _is_filter_compatible(combined)
        assert combined == filter1

    def test_combine_and_multiple_filters(self):
        """Test combining multiple filters with AND logic."""
        filter1 = FilterBuilder.by_chunk_type("text")
        filter2 = FilterBuilder.by_source_document("document.pdf")
        combined = FilterBuilder.combine_and(filter1, filter2)
        assert _is_filter_compatible(combined)

    def test_combine_and_empty(self):
        """Test combining filters with AND logic (no filters)."""
        with pytest.raises(ValueError, match="At least one filter must be provided"):
            FilterBuilder.combine_and()

    def test_combine_or_single_filter(self):
        """Test combining filters with OR logic (single filter)."""
        filter1 = FilterBuilder.by_chunk_type("text")
        combined = FilterBuilder.combine_or(filter1)
        assert _is_filter_compatible(combined)
        assert combined == filter1

    def test_combine_or_multiple_filters(self):
        """Test combining multiple filters with OR logic."""
        filter1 = FilterBuilder.by_chunk_type("text")
        filter2 = FilterBuilder.by_chunk_type("equation")
        combined = FilterBuilder.combine_or(filter1, filter2)
        assert _is_filter_compatible(combined)

    def test_combine_or_empty(self):
        """Test combining filters with OR logic (no filters)."""
        with pytest.raises(ValueError, match="At least one filter must be provided"):
            FilterBuilder.combine_or()

    def test_complex_filter_combination(self):
        """Test combining multiple filters in a complex scenario."""
        # Create multiple filters
        type_filter = FilterBuilder.by_chunk_type("text")
        doc_filter = FilterBuilder.by_source_document("document.pdf")
        date_filter = FilterBuilder.by_date_range(start="2024-01-01", end="2024-12-31")

        # Combine with AND
        combined = FilterBuilder.combine_and(type_filter, doc_filter, date_filter)
        assert _is_filter_compatible(combined)

    def test_filter_builder_returns_weaviate_filter(self):
        """Test that FilterBuilder methods return Weaviate Filter objects."""
        filters = [
            FilterBuilder.by_chunk_type("text"),
            FilterBuilder.by_source_document("doc.pdf"),
            FilterBuilder.by_email_sender("test@example.com"),
            FilterBuilder.by_page_number(1),
        ]

        for filter_obj in filters:
            assert _is_filter_compatible(filter_obj)
