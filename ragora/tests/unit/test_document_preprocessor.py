"""
Unit tests for DocumentPreprocessor in the RAG system.
"""

from unittest.mock import Mock, patch

import pytest

from ragora import DataChunk, DataChunker, DocumentPreprocessor
from ragora.utils.latex_parser import (
    LatexChapter,
    LatexDocument,
    LatexParagraph,
    LatexSection,
    LatexTable,
)


class TestDocumentPreprocessor:
    """Test DocumentPreprocessor class."""

    def test_init_default_parameters(self):
        """Test DocumentPreprocessor initialization with default parameters."""
        preprocessor = DocumentPreprocessor()

        assert preprocessor.chunker is not None
        assert isinstance(preprocessor.chunker, DataChunker)
        assert preprocessor.chunker.default_strategy.chunk_size == 768
        assert preprocessor.chunker.default_strategy.overlap_size == 100
        assert preprocessor.latex_parser is not None

    def test_init_custom_parameters(self):
        """Test DocumentPreprocessor initialization with custom parameters."""
        from ragora import TextChunkingStrategy

        custom_strategy = TextChunkingStrategy(chunk_size=512, overlap_size=50)
        custom_chunker = DataChunker(default_strategy=custom_strategy)
        preprocessor = DocumentPreprocessor(chunker=custom_chunker)

        assert preprocessor.chunker is custom_chunker
        assert preprocessor.chunker.default_strategy.chunk_size == 512
        assert preprocessor.chunker.default_strategy.overlap_size == 50
        assert preprocessor.latex_parser is not None

    def test_init_custom_chunker_only(self):
        """Test DocumentPreprocessor initialization with custom chunker."""
        from ragora import TextChunkingStrategy

        custom_strategy = TextChunkingStrategy(chunk_size=256, overlap_size=25)
        custom_chunker = DataChunker(default_strategy=custom_strategy)
        preprocessor = DocumentPreprocessor(chunker=custom_chunker)

        assert preprocessor.chunker is custom_chunker
        assert preprocessor.chunker.default_strategy.chunk_size == 256
        assert preprocessor.chunker.default_strategy.overlap_size == 25

    @patch("ragora.core.document_preprocessor.LatexParser")
    def test_preprocess_document_success(self, mock_latex_parser_class):
        """Test preprocess_document method with successful parsing."""
        # Setup mocks
        mock_parser = Mock()
        mock_latex_parser_class.return_value = mock_parser

        # Create mock document
        mock_document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            paragraphs=[LatexParagraph(content="Test content")],
        )
        mock_parser.parse_document.return_value = mock_document

        # Create mock chunks
        expected_chunks = [
            DataChunk(
                text="Test content",
                start_idx=0,
                end_idx=12,
                chunk_id="document:test_doc:0:0000",
                metadata={"source": "test.tex"},
            )
        ]

        # Mock the chunker
        mock_chunker = Mock()
        mock_chunker.chunk.return_value = expected_chunks

        # Create preprocessor with mocked chunker
        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        preprocessor.latex_parser = mock_parser

        # Test
        result = preprocessor.preprocess_document("test.tex")

        # Assertions
        mock_parser.parse_document.assert_called_once_with("test.tex")
        mock_chunker.chunk.assert_called_once()
        assert result == expected_chunks

    @patch("ragora.core.document_preprocessor.LatexParser")
    def test_preprocess_document_file_not_found(self, mock_latex_parser_class):
        """Test preprocess_document method with file not found."""
        # Setup mocks
        mock_parser = Mock()
        mock_latex_parser_class.return_value = mock_parser
        mock_parser.parse_document.return_value = None

        mock_chunker = Mock()
        mock_chunker.chunk.return_value = []

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        preprocessor.latex_parser = mock_parser

        # Test - this should raise a ValueError since None document is not allowed
        with pytest.raises(ValueError, match="Document cannot be None"):
            preprocessor.preprocess_document("nonexistent.tex")

    @patch("ragora.core.document_preprocessor.LatexParser")
    def test_preprocess_documents_success(self, mock_latex_parser_class):
        """Test preprocess_documents method with multiple files."""
        # Setup mocks
        mock_parser = Mock()
        mock_latex_parser_class.return_value = mock_parser

        # Create mock documents
        mock_doc1 = LatexDocument(
            title="Document 1",
            author="Author 1",
            year="2024",
            doi="10.1000/doc1",
            source_document="doc1.tex",
            page_reference="1-5",
            paragraphs=[LatexParagraph(content="Doc 1 content")],
        )
        mock_doc2 = LatexDocument(
            title="Document 2",
            author="Author 2",
            year="2024",
            doi="10.1000/doc2",
            source_document="doc2.tex",
            page_reference="6-10",
            paragraphs=[LatexParagraph(content="Doc 2 content")],
        )
        mock_parser.parse_document.side_effect = [mock_doc1, mock_doc2]

        # Create mock chunks
        chunk1 = [
            DataChunk(
                text="Doc 1 content",
                start_idx=0,
                end_idx=16,
                chunk_id="document:doc1:0:0000",
                metadata={"source": "doc1"},
            )
        ]
        chunk2 = [
            DataChunk(
                text="Doc 2 content",
                start_idx=0,
                end_idx=16,
                chunk_id="document:doc2:0:0000",
                metadata={"source": "doc2"},
            )
        ]

        mock_chunker = Mock()
        mock_chunker.chunk.side_effect = [chunk1, chunk2]

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        preprocessor.latex_parser = mock_parser

        # Test
        file_paths = ["doc1.tex", "doc2.tex"]
        result = preprocessor.preprocess_documents(file_paths)

        # Assertions
        assert mock_parser.parse_document.call_count == 2
        mock_parser.parse_document.assert_any_call("doc1.tex")
        mock_parser.parse_document.assert_any_call("doc2.tex")
        assert mock_chunker.chunk.call_count == 2
        assert result == chunk1 + chunk2

    @patch("ragora.core.document_preprocessor.LatexParser")
    def test_preprocess_documents_empty_list(self, mock_latex_parser_class):
        """Test preprocess_documents method with empty file list."""
        mock_parser = Mock()
        mock_latex_parser_class.return_value = mock_parser

        mock_chunker = Mock()
        mock_chunker.chunk.return_value = []

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        preprocessor.latex_parser = mock_parser

        # Test
        result = preprocessor.preprocess_documents([])

        # Assertions
        mock_parser.parse_document.assert_not_called()
        mock_chunker.chunk.assert_not_called()
        assert result == []

    @patch("os.listdir")
    @patch("os.path.join")
    @patch("ragora.core.document_preprocessor.LatexParser")
    def test_preprocess_document_folder_success(
        self, mock_latex_parser_class, mock_join, mock_listdir
    ):
        """Test preprocess_document_folder method with valid folder."""
        # Setup mocks
        mock_listdir.return_value = ["doc1.tex", "doc2.tex"]
        mock_join.side_effect = lambda folder, file: f"{folder}/{file}"

        mock_parser = Mock()
        mock_latex_parser_class.return_value = mock_parser

        mock_doc1 = LatexDocument(
            title="Document 1",
            author="Author 1",
            year="2024",
            doi="10.1000/doc1",
            source_document="doc1.tex",
            page_reference="1-5",
            paragraphs=[LatexParagraph(content="Folder doc 1 content")],
        )
        mock_doc2 = LatexDocument(
            title="Document 2",
            author="Author 2",
            year="2024",
            doi="10.1000/doc2",
            source_document="doc2.tex",
            page_reference="6-10",
            paragraphs=[LatexParagraph(content="Folder doc 2 content")],
        )
        mock_parser.parse_document.side_effect = [mock_doc1, mock_doc2]

        chunk1 = [
            DataChunk(
                text="Folder doc 1 content",
                start_idx=0,
                end_idx=20,
                chunk_id="document:folder1:0:0000",
                metadata={"source": "folder1"},
            )
        ]
        chunk2 = [
            DataChunk(
                text="Folder doc 2 content",
                start_idx=0,
                end_idx=20,
                chunk_id="document:folder2:0:0000",
                metadata={"source": "folder2"},
            )
        ]

        mock_chunker = Mock()
        mock_chunker.chunk.side_effect = [chunk1, chunk2]

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        preprocessor.latex_parser = mock_parser

        # Test
        result = preprocessor.preprocess_document_folder("/test/folder")

        # Assertions
        mock_listdir.assert_called_once_with("/test/folder")
        assert mock_join.call_count == 2
        mock_join.assert_any_call("/test/folder", "doc1.tex")
        mock_join.assert_any_call("/test/folder", "doc2.tex")
        assert mock_parser.parse_document.call_count == 2
        assert mock_chunker.chunk.call_count == 2
        assert result == chunk1 + chunk2

    @patch("os.listdir")
    def test_preprocess_document_folder_not_found(self, mock_listdir):
        """Test preprocess_document_folder method with non-existent folder."""
        mock_listdir.side_effect = FileNotFoundError("Folder not found")

        preprocessor = DocumentPreprocessor()

        # Test
        with pytest.raises(FileNotFoundError):
            preprocessor.preprocess_document_folder("/nonexistent/folder")

    def test_extract_document_text_with_chapters(self):
        """Test _extract_document_text method with chapters."""
        # Create mock document with chapters
        chapter1 = LatexChapter(
            title="Chapter 1",
            label="ch1",
            paragraphs=[
                LatexParagraph(content="Chapter 1 paragraph 1"),
                LatexParagraph(content="Chapter 1 paragraph 2"),
            ],
            sections=[
                LatexSection(
                    title="Section 1.1",
                    label="sec1.1",
                    paragraphs=[LatexParagraph(content="Section 1.1 paragraph")],
                )
            ],
        )

        chapter2 = LatexChapter(
            title="Chapter 2",
            label="ch2",
            paragraphs=[LatexParagraph(content="Chapter 2 paragraph")],
        )

        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            chapters=[chapter1, chapter2],
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([document])

        expected = (
            "# Chapter 1\n\n"
            "Chapter 1 paragraph 1\n\n"
            "Chapter 1 paragraph 2\n\n"
            "## Section 1.1\n\n"
            "Section 1.1 paragraph\n\n"
            "# Chapter 2\n\n"
            "Chapter 2 paragraph"
        )

        assert result == expected

    def test_extract_document_text_with_sections(self):
        """Test _extract_document_text method with standalone sections."""
        section1 = LatexSection(
            title="Section 1",
            label="sec1",
            paragraphs=[
                LatexParagraph(content="Section 1 paragraph 1"),
                LatexParagraph(content="Section 1 paragraph 2"),
            ],
        )

        section2 = LatexSection(
            title="Section 2",
            label="sec2",
            paragraphs=[LatexParagraph(content="Section 2 paragraph")],
        )

        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            sections=[section1, section2],
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([document])

        expected = (
            "## Section 1\n\n"
            "Section 1 paragraph 1\n\n"
            "Section 1 paragraph 2\n\n"
            "## Section 2\n\n"
            "Section 2 paragraph"
        )

        assert result == expected

    def test_extract_document_text_with_paragraphs(self):
        """Test _extract_document_text method with standalone paragraphs."""
        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            paragraphs=[
                LatexParagraph(content="Standalone paragraph 1"),
                LatexParagraph(content="Standalone paragraph 2"),
            ],
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([document])

        expected = "Standalone paragraph 1\n\nStandalone paragraph 2"

        assert result == expected

    def test_extract_document_text_with_tables(self):
        """Test _extract_document_text method with tables."""
        table1 = LatexTable(
            caption="Table 1",
            label="tab1",
            headers=["Header 1", "Header 2"],
            rows=[["Row 1 Col 1", "Row 1 Col 2"], ["Row 2 Col 1", "Row 2 Col 2"]],
        )

        table2 = LatexTable(
            caption="Table 2", label="tab2", headers=["A", "B"], rows=[["1", "2"]]
        )

        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            tables=[table1, table2],
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([document])

        expected = (
            "Table: Table 1\n"
            "Header 1 | Header 2\n"
            "-------- | --------\n"
            "Row 1 Col 1 | Row 1 Col 2\n"
            "Row 2 Col 1 | Row 2 Col 2\n\n\n"
            "Table: Table 2\n"
            "A | B\n"
            "- | -\n"
            "1 | 2\n"
        )

        assert result == expected

    def test_extract_document_text_empty_document(self):
        """Test _extract_document_text method with empty document."""
        document = LatexDocument(
            title="Empty Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="empty.tex",
            page_reference="1",
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([document])

        assert result == ""

    def test_extract_document_text_multiple_documents(self):
        """Test _extract_document_text method with multiple documents."""
        doc1 = LatexDocument(
            title="Document 1",
            author="Author 1",
            year="2024",
            doi="10.1000/doc1",
            source_document="doc1.tex",
            page_reference="1-5",
            paragraphs=[LatexParagraph(content="Doc 1 content")],
        )

        doc2 = LatexDocument(
            title="Document 2",
            author="Author 2",
            year="2024",
            doi="10.1000/doc2",
            source_document="doc2.tex",
            page_reference="6-10",
            paragraphs=[LatexParagraph(content="Doc 2 content")],
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([doc1, doc2])

        expected = "Doc 1 content\n\nDoc 2 content"

        assert result == expected

    def test_extract_document_text_mixed_content(self):
        """Test _extract_document_text method with mixed content types."""
        # Create document with chapters, sections, paragraphs, and tables
        chapter = LatexChapter(
            title="Main Chapter",
            label="main",
            paragraphs=[LatexParagraph(content="Chapter paragraph")],
            sections=[
                LatexSection(
                    title="Chapter Section",
                    label="chsec",
                    paragraphs=[LatexParagraph(content="Chapter section paragraph")],
                )
            ],
        )

        standalone_section = LatexSection(
            title="Standalone Section",
            label="standalone",
            paragraphs=[LatexParagraph(content="Standalone section paragraph")],
        )

        standalone_paragraph = LatexParagraph(content="Standalone paragraph")

        table = LatexTable(
            caption="Data Table",
            label="data",
            headers=["X", "Y"],
            rows=[["1", "2"], ["3", "4"]],
        )

        document = LatexDocument(
            title="Mixed Document",
            author="Test Author",
            year="2024",
            doi="10.1000/mixed",
            source_document="mixed.tex",
            page_reference="1-20",
            chapters=[chapter],
            sections=[standalone_section],
            paragraphs=[standalone_paragraph],
            tables=[table],
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([document])

        expected = (
            "# Main Chapter\n\n"
            "Chapter paragraph\n\n"
            "## Chapter Section\n\n"
            "Chapter section paragraph\n\n"
            "## Standalone Section\n\n"
            "Standalone section paragraph\n\n"
            "Standalone paragraph\n\n"
            "Table: Data Table\n"
            "X | Y\n"
            "- | -\n"
            "1 | 2\n"
            "3 | 4\n"
        )

        assert result == expected

    def test_chunk_document_none_document(self):
        """Test _chunk_document method with None document."""
        preprocessor = DocumentPreprocessor()

        with pytest.raises(ValueError, match="Document cannot be None"):
            preprocessor._chunk_document(None)

    def test_chunk_document_with_paragraphs_only(self):
        """Test _chunk_document method with document containing only paragraphs."""
        # Create mock document with paragraphs
        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            paragraphs=[
                LatexParagraph(content="First paragraph content"),
                LatexParagraph(content="Second paragraph content"),
            ],
        )

        # Create mock chunks
        expected_chunks = [
            DataChunk(
                text="First paragraph contentSecond paragraph content",
                start_idx=0,
                end_idx=47,
                chunk_id="document:test_doc:0:0000",
                metadata={"chunk_idx": 1, "chunk_size": 768, "total_chunks": 1},
            )
        ]

        # Mock the chunker
        mock_chunker = Mock()
        mock_chunker.chunk.return_value = expected_chunks

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        result = preprocessor._chunk_document(document)

        # Verify chunker was called correctly
        mock_chunker.chunk.assert_called_once()
        call_args = mock_chunker.chunk.call_args
        assert call_args[0][0] == "First paragraph contentSecond paragraph content"
        context = call_args[0][1]
        assert context.chunk_type == "document"
        assert context.source_document == "test.tex"
        assert context.section_title == "Test Document"
        assert result == expected_chunks

    def test_chunk_document_with_chapters_only(self):
        """Test _chunk_document method with document containing only chapters."""
        # Create mock document with chapters
        chapter1 = LatexChapter(
            title="Chapter 1",
            label="ch1",
            paragraphs=[
                LatexParagraph(content="Chapter 1 paragraph 1"),
                LatexParagraph(content="Chapter 1 paragraph 2"),
            ],
        )

        chapter2 = LatexChapter(
            title="Chapter 2",
            label="ch2",
            paragraphs=[LatexParagraph(content="Chapter 2 paragraph")],
        )

        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            chapters=[chapter1, chapter2],
        )

        # Create mock chunks
        expected_chunks = [
            DataChunk(
                text="# Chapter 1Chapter 1 paragraph 1Chapter 1 paragraph 2",
                start_idx=0,
                end_idx=58,
                chunk_id="document:test_doc:0:0000",
                metadata={"chunk_idx": 1, "chunk_size": 768, "total_chunks": 2},
            ),
            DataChunk(
                text="# Chapter 2Chapter 2 paragraph",
                start_idx=0,
                end_idx=30,
                chunk_id="document:test_doc:0:0001",
                metadata={"chunk_idx": 2, "chunk_size": 768, "total_chunks": 2},
            ),
        ]

        # Mock the chunker
        mock_chunker = Mock()
        mock_chunker.chunk.side_effect = [[chunk] for chunk in expected_chunks]

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        result = preprocessor._chunk_document(document)

        # Verify chunker was called for each chapter
        assert mock_chunker.chunk.call_count == 2

        # Check first call
        first_call = mock_chunker.chunk.call_args_list[0]
        assert (
            first_call[0][0] == "# Chapter 1Chapter 1 paragraph 1Chapter 1 paragraph 2"
        )
        context1 = first_call[0][1]
        assert context1.chunk_type == "document"
        assert context1.source_document == "test.tex"
        assert context1.section_title == "Chapter 1"

        # Check second call
        second_call = mock_chunker.chunk.call_args_list[1]
        assert second_call[0][0] == "# Chapter 2Chapter 2 paragraph"
        context2 = second_call[0][1]
        assert context2.chunk_type == "document"
        assert context2.source_document == "test.tex"
        assert context2.section_title == "Chapter 2"
        assert result == expected_chunks

    def test_chunk_document_with_chapters_and_sections(self):
        """Test _chunk_document method with chapters containing sections."""
        # Create mock document with chapter containing sections
        section1 = LatexSection(
            title="Section 1.1",
            label="sec1.1",
            paragraphs=[
                LatexParagraph(content="Section 1.1 paragraph 1"),
                LatexParagraph(content="Section 1.1 paragraph 2"),
            ],
        )

        section2 = LatexSection(
            title="Section 1.2",
            label="sec1.2",
            paragraphs=[LatexParagraph(content="Section 1.2 paragraph")],
        )

        chapter = LatexChapter(
            title="Chapter 1",
            label="ch1",
            paragraphs=[LatexParagraph(content="Chapter paragraph")],
            sections=[section1, section2],
        )

        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            chapters=[chapter],
        )

        # Create mock chunks
        expected_chunks = [
            DataChunk(
                text="# Chapter 1Chapter paragraph",
                start_idx=0,
                end_idx=27,
                chunk_id="document:test_doc:0:0000",
                metadata={"chunk_idx": 1, "chunk_size": 768, "total_chunks": 3},
            ),
            DataChunk(
                text="## Section 1.1Section 1.1 paragraph 1Section 1.1 paragraph 2",
                start_idx=0,
                end_idx=59,
                chunk_id="document:test_doc:0:0001",
                metadata={"chunk_idx": 2, "chunk_size": 768, "total_chunks": 3},
            ),
            DataChunk(
                text="## Section 1.2Section 1.2 paragraph",
                start_idx=0,
                end_idx=33,
                chunk_id="document:test_doc:0:0002",
                metadata={"chunk_idx": 3, "chunk_size": 768, "total_chunks": 3},
            ),
        ]

        # Mock the chunker
        mock_chunker = Mock()
        mock_chunker.chunk.side_effect = [[chunk] for chunk in expected_chunks]

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        result = preprocessor._chunk_document(document)

        # Verify chunker was called for chapter and each section
        assert mock_chunker.chunk.call_count == 3

        # Check chapter call
        chapter_call = mock_chunker.chunk.call_args_list[0]
        assert chapter_call[0][0] == "# Chapter 1Chapter paragraph"
        context1 = chapter_call[0][1]
        assert context1.chunk_type == "document"
        assert context1.source_document == "test.tex"
        assert context1.section_title == "Chapter 1"

        # Check section calls
        section1_call = mock_chunker.chunk.call_args_list[1]
        assert (
            section1_call[0][0]
            == "## Section 1.1Section 1.1 paragraph 1Section 1.1 paragraph 2"
        )
        context2 = section1_call[0][1]
        assert context2.section_title == "Section 1.1"

        section2_call = mock_chunker.chunk.call_args_list[2]
        assert section2_call[0][0] == "## Section 1.2Section 1.2 paragraph"
        context3 = section2_call[0][1]
        assert context3.section_title == "Section 1.2"
        assert result == expected_chunks

    def test_chunk_document_with_standalone_sections(self):
        """Test _chunk_document method with standalone sections."""
        # Create mock document with standalone sections
        section1 = LatexSection(
            title="Standalone Section 1",
            label="standalone1",
            paragraphs=[
                LatexParagraph(content="Standalone section 1 paragraph 1"),
                LatexParagraph(content="Standalone section 1 paragraph 2"),
            ],
        )

        section2 = LatexSection(
            title="Standalone Section 2",
            label="standalone2",
            paragraphs=[LatexParagraph(content="Standalone section 2 paragraph")],
        )

        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            sections=[section1, section2],
        )

        # Create mock chunks
        expected_chunks = [
            DataChunk(
                text="## Standalone Section 1Standalone section 1 paragraph 1Standalone section 1 paragraph 2",
                start_idx=0,
                end_idx=78,
                chunk_id="document:test_doc:0:0000",
                metadata={"chunk_idx": 1, "chunk_size": 768, "total_chunks": 2},
            ),
            DataChunk(
                text="## Standalone Section 2Standalone section 2 paragraph",
                start_idx=0,
                end_idx=47,
                chunk_id="document:test_doc:0:0001",
                metadata={"chunk_idx": 2, "chunk_size": 768, "total_chunks": 2},
            ),
        ]

        # Mock the chunker
        mock_chunker = Mock()
        mock_chunker.chunk.side_effect = [[chunk] for chunk in expected_chunks]

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        result = preprocessor._chunk_document(document)

        # Verify chunker was called for each standalone section
        assert mock_chunker.chunk.call_count == 2

        # Check first section call
        first_call = mock_chunker.chunk.call_args_list[0]
        assert (
            first_call[0][0]
            == "## Standalone Section 1Standalone section 1 paragraph 1Standalone section 1 paragraph 2"
        )
        context1 = first_call[0][1]
        assert context1.chunk_type == "document"
        assert context1.source_document == "test.tex"
        assert context1.section_title == "Standalone Section 1"

        # Check second section call
        second_call = mock_chunker.chunk.call_args_list[1]
        assert (
            second_call[0][0] == "## Standalone Section 2Standalone section 2 paragraph"
        )
        context2 = second_call[0][1]
        assert context2.section_title == "Standalone Section 2"
        assert result == expected_chunks

    def test_chunk_document_with_tables(self):
        """Test _chunk_document method with tables."""
        # Create mock document with tables
        table1 = LatexTable(
            caption="Table 1",
            label="tab1",
            headers=["Header 1", "Header 2"],
            rows=[["Row 1 Col 1", "Row 1 Col 2"], ["Row 2 Col 1", "Row 2 Col 2"]],
        )

        table2 = LatexTable(
            caption="Table 2",
            label="tab2",
            headers=["A", "B"],
            rows=[["1", "2"]],
        )

        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            tables=[table1, table2],
        )

        # Mock the to_plain_text method for tables
        table1.to_plain_text = Mock(
            return_value="Table: Table 1\nHeader 1 | Header 2\nRow 1 Col 1 | Row 1 Col 2"
        )
        table2.to_plain_text = Mock(return_value="Table: Table 2\nA | B\n1 | 2")

        # Create mock chunks
        expected_chunks = [
            DataChunk(
                text="Table: Table 1\nHeader 1 | Header 2\nRow 1 Col 1 | Row 1 Col 2",
                start_idx=0,
                end_idx=60,
                chunk_id="document:test_doc:0:0000",
                metadata={"chunk_idx": 1, "chunk_size": 768, "total_chunks": 2},
            ),
            DataChunk(
                text="Table: Table 2\nA | B\n1 | 2",
                start_idx=0,
                end_idx=25,
                chunk_id="document:test_doc:0:0001",
                metadata={"chunk_idx": 2, "chunk_size": 768, "total_chunks": 2},
            ),
        ]

        # Mock the chunker
        mock_chunker = Mock()
        mock_chunker.chunk.side_effect = [[chunk] for chunk in expected_chunks]

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        result = preprocessor._chunk_document(document)

        # Verify chunker was called for each table
        assert mock_chunker.chunk.call_count == 2

        # Check first table call
        first_call = mock_chunker.chunk.call_args_list[0]
        assert (
            first_call[0][0]
            == "Table: Table 1\nHeader 1 | Header 2\nRow 1 Col 1 | Row 1 Col 2"
        )
        context1 = first_call[0][1]
        assert context1.chunk_type == "document"
        assert context1.source_document == "test.tex"
        assert context1.section_title == "Test Document"

        # Check second table call
        second_call = mock_chunker.chunk.call_args_list[1]
        assert second_call[0][0] == "Table: Table 2\nA | B\n1 | 2"
        context2 = second_call[0][1]
        assert context2.section_title == "Test Document"
        assert result == expected_chunks

    def test_chunk_document_with_all_content_types(self):
        """Test _chunk_document method with all content types (paragraphs, chapters, sections, tables)."""
        # Create comprehensive document
        chapter = LatexChapter(
            title="Main Chapter",
            label="main",
            paragraphs=[LatexParagraph(content="Chapter paragraph")],
            sections=[
                LatexSection(
                    title="Chapter Section",
                    label="chsec",
                    paragraphs=[LatexParagraph(content="Chapter section paragraph")],
                )
            ],
        )

        standalone_section = LatexSection(
            title="Standalone Section",
            label="standalone",
            paragraphs=[LatexParagraph(content="Standalone section paragraph")],
        )

        standalone_paragraph = LatexParagraph(content="Standalone paragraph")

        table = LatexTable(
            caption="Data Table",
            label="data",
            headers=["X", "Y"],
            rows=[["1", "2"], ["3", "4"]],
        )

        document = LatexDocument(
            title="Comprehensive Document",
            author="Test Author",
            year="2024",
            doi="10.1000/comprehensive",
            source_document="comprehensive.tex",
            page_reference="1-20",
            chapters=[chapter],
            sections=[standalone_section],
            paragraphs=[standalone_paragraph],
            tables=[table],
        )

        # Mock the to_plain_text method for table
        table.to_plain_text = Mock(
            return_value="Table: Data Table\nX | Y\n1 | 2\n3 | 4"
        )

        # Create mock chunks
        expected_chunks = [
            DataChunk(
                text="Standalone paragraph",
                start_idx=0,
                end_idx=19,
                chunk_id="document:test_doc:0:0000",
                metadata={},
            ),
            DataChunk(
                text="# Main ChapterChapter paragraph",
                start_idx=0,
                end_idx=32,
                chunk_id="document:test_doc:0:0001",
                metadata={},
            ),
            DataChunk(
                text="## Chapter SectionChapter section paragraph",
                start_idx=0,
                end_idx=42,
                chunk_id="document:test_doc:0:0002",
                metadata={},
            ),
            DataChunk(
                text="## Standalone SectionStandalone section paragraph",
                start_idx=0,
                end_idx=51,
                chunk_id="document:test_doc:0:0003",
                metadata={},
            ),
            DataChunk(
                text="Table: Data Table\nX | Y\n1 | 2\n3 | 4",
                start_idx=0,
                end_idx=35,
                chunk_id="document:test_doc:0:0004",
                metadata={},
            ),
        ]

        # Mock the chunker
        mock_chunker = Mock()
        mock_chunker.chunk.side_effect = [[chunk] for chunk in expected_chunks]

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        result = preprocessor._chunk_document(document)

        # Verify chunker was called for all content types
        assert mock_chunker.chunk.call_count == 5

        # Verify calls with correct parameters
        calls = mock_chunker.chunk.call_args_list
        assert calls[0][0][0] == "Standalone paragraph"
        assert calls[1][0][0] == "# Main ChapterChapter paragraph"
        assert calls[2][0][0] == "## Chapter SectionChapter section paragraph"
        assert calls[3][0][0] == "## Standalone SectionStandalone section paragraph"
        assert calls[4][0][0] == "Table: Data Table\nX | Y\n1 | 2\n3 | 4"

        assert result == expected_chunks

    def test_chunk_document_empty_chapter_without_paragraphs(self):
        """Test _chunk_document method with empty chapter (no paragraphs)."""
        # Create chapter without paragraphs
        chapter = LatexChapter(
            title="Empty Chapter",
            label="empty",
            paragraphs=[],
        )

        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            chapters=[chapter],
        )

        # Mock the chunker
        mock_chunker = Mock()
        mock_chunker.chunk.return_value = []

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        result = preprocessor._chunk_document(document)

        # Verify no chunks were created for empty chapter
        mock_chunker.chunk.assert_not_called()
        assert result == []

    def test_chunk_document_empty_section_without_paragraphs(self):
        """Test _chunk_document method with empty section (no paragraphs)."""
        # Create section without paragraphs
        section = LatexSection(
            title="Empty Section",
            label="empty",
            paragraphs=[],
        )

        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            sections=[section],
        )

        # Mock the chunker
        mock_chunker = Mock()
        mock_chunker.chunk.return_value = []

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        result = preprocessor._chunk_document(document)

        # Verify no chunks were created for empty section
        mock_chunker.chunk.assert_not_called()
        assert result == []

    def test_chunk_document_empty_document(self):
        """Test _chunk_document method with completely empty document."""
        document = LatexDocument(
            title="Empty Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="empty.tex",
            page_reference="1",
        )

        # Mock the chunker
        mock_chunker = Mock()
        mock_chunker.chunk.return_value = []

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        result = preprocessor._chunk_document(document)

        # Verify no chunks were created
        mock_chunker.chunk.assert_not_called()
        assert result == []
