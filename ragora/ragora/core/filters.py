"""Filter utilities for Weaviate queries.

This module provides helper functions and builders for constructing
Weaviate Filter objects using domain model semantics, making it easier
to filter search results without needing to know exact Weaviate property names.

The FilterBuilder class maps domain model field names to Weaviate property
names, providing a consistent interface aligned with RetrievalMetadata and
DataChunk models.
"""

from typing import Optional

from weaviate.classes.query import Filter


class FilterBuilder:
    """Helper for building Weaviate filters using domain model semantics.

    This class provides convenience methods for constructing Weaviate Filter
    objects using domain model field names, abstracting away the underlying
    Weaviate property names. This makes filtering more intuitive and reduces
    the chance of errors from using incorrect property names.

    Examples:
        # Filter by chunk type
        filter = FilterBuilder.by_chunk_type("text")

        # Filter by date range
        filter = FilterBuilder.by_date_range(start="2024-01-01", end="2024-12-31")

        # Combine filters
        filter = FilterBuilder.combine_and(
            FilterBuilder.by_chunk_type("text"),
            FilterBuilder.by_source_document("document.pdf")
        )
    """

    @staticmethod
    def by_chunk_type(value: str) -> Filter:
        """Filter by chunk type (e.g., "text", "equation", "citation").

        Args:
            value: Chunk type value to filter by

        Returns:
            Filter: Weaviate Filter object for chunk type
        """
        return Filter.by_property("chunk_type").equal(value)

    @staticmethod
    def by_source_document(value: str) -> Filter:
        """Filter by source document filename.

        Args:
            value: Source document filename to filter by

        Returns:
            Filter: Weaviate Filter object for source document
        """
        return Filter.by_property("source_document").equal(value)

    @staticmethod
    def by_email_sender(value: str) -> Filter:
        """Filter by email sender address.

        Args:
            value: Email sender address to filter by

        Returns:
            Filter: Weaviate Filter object for email sender
        """
        return Filter.by_property("email_sender").equal(value)

    @staticmethod
    def by_email_subject(value: str) -> Filter:
        """Filter by email subject line.

        Args:
            value: Email subject line to filter by (supports partial matches)

        Returns:
            Filter: Weaviate Filter object for email subject
        """
        return Filter.by_property("email_subject").equal(value)

    @staticmethod
    def by_email_folder(value: str) -> Filter:
        """Filter by email folder/path.

        Args:
            value: Email folder path to filter by

        Returns:
            Filter: Weaviate Filter object for email folder
        """
        return Filter.by_property("email_folder").equal(value)

    @staticmethod
    def by_email_recipient(value: str) -> Filter:
        """Filter by email recipient address.

        Args:
            value: Email recipient address to filter by

        Returns:
            Filter: Weaviate Filter object for email recipient
        """
        return Filter.by_property("email_recipient").equal(value)

    @staticmethod
    def by_date_range(
        start: Optional[str] = None, end: Optional[str] = None
    ) -> Optional[Filter]:
        """Filter by date range using created_at timestamp.

        Args:
            start: Start date (ISO format string, e.g., "2024-01-01")
            end: End date (ISO format string, e.g., "2024-12-31")

        Returns:
            Filter: Weaviate Filter object for date range, or None if both
                start and end are None
        """
        if start is None and end is None:
            return None

        filters = []
        if start:
            filters.append(Filter.by_property("created_at").greater_or_equal(start))
        if end:
            filters.append(Filter.by_property("created_at").less_or_equal(end))

        if len(filters) == 1:
            return filters[0]
        return Filter.all_of(filters)

    @staticmethod
    def by_email_date_range(
        start: Optional[str] = None, end: Optional[str] = None
    ) -> Optional[Filter]:
        """Filter by email date range using email_date timestamp.

        Args:
            start: Start date (ISO format string, e.g., "2024-01-01")
            end: End date (ISO format string, e.g., "2024-12-31")

        Returns:
            Filter: Weaviate Filter object for email date range, or None if
                both start and end are None
        """
        if start is None and end is None:
            return None

        filters = []
        if start:
            filters.append(Filter.by_property("email_date").greater_or_equal(start))
        if end:
            filters.append(Filter.by_property("email_date").less_or_equal(end))

        if len(filters) == 1:
            return filters[0]
        return Filter.all_of(filters)

    @staticmethod
    def by_page_number(value: int) -> Filter:
        """Filter by page number in source document.

        Args:
            value: Page number to filter by

        Returns:
            Filter: Weaviate Filter object for page number
        """
        return Filter.by_property("page_number").equal(value)

    @staticmethod
    def by_section_title(value: str) -> Filter:
        """Filter by section or chapter title.

        Args:
            value: Section title to filter by

        Returns:
            Filter: Weaviate Filter object for section title
        """
        return Filter.by_property("section_title").equal(value)

    @staticmethod
    def by_chunk_idx(value: int) -> Filter:
        """Filter by chunk index.

        Args:
            value: Chunk index to filter by

        Returns:
            Filter: Weaviate Filter object for chunk index
        """
        return Filter.by_property("metadata_chunk_idx").equal(value)

    @staticmethod
    def combine_and(*filters: Filter) -> Filter:
        """Combine multiple filters with AND logic.

        All filters must match for a result to be included.

        Args:
            *filters: Variable number of Filter objects to combine

        Returns:
            Filter: Combined filter using AND logic

        Raises:
            ValueError: If no filters are provided
        """
        if not filters:
            raise ValueError("At least one filter must be provided")
        if len(filters) == 1:
            return filters[0]
        return Filter.all_of(list(filters))

    @staticmethod
    def combine_or(*filters: Filter) -> Filter:
        """Combine multiple filters with OR logic.

        Any filter matching will include the result.

        Args:
            *filters: Variable number of Filter objects to combine

        Returns:
            Filter: Combined filter using OR logic

        Raises:
            ValueError: If no filters are provided
        """
        if not filters:
            raise ValueError("At least one filter must be provided")
        if len(filters) == 1:
            return filters[0]
        return Filter.any_of(list(filters))
