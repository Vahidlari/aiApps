import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Citation information for a document."""

    author: str
    year: str
    title: str
    doi: str
    source_document: str
    page_reference: str
    citation_label: str
    citation_hash: str


@dataclass
class LatexParagraph:
    """A LaTeX paragraph."""

    content: str
    citations: Optional[List[Citation]] = None


@dataclass
class LatexTable:
    """A LaTeX table."""

    caption: str
    label: str
    headers: List[str]
    rows: List[List[str]]
    footnotes: Optional[List[str]] = None

    def to_markdown(self) -> str:
        """Convert the table to a Markdown table."""
        if not self.headers and not self.rows:
            return f"**Table: {self.caption}**\n\n"

            # Build markdown table
        md_lines = []
        if self.caption:
            md_lines.append(f"**Table: {self.caption}**\n")

        # Headers
        if self.headers:
            md_lines.append("| " + " | ".join(self.headers) + " |")
            md_lines.append("|" + "|".join(["---"] * len(self.headers)) + "|")

        # Rows
        for row in self.rows:
            md_lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

        return "\n".join(md_lines) + "\n"

    def to_plain_text(self) -> str:
        """Convert the table to a plain text table."""
        if not self.headers and not self.rows:
            return f"Table: {self.caption}\n\n"

        lines = []
        if self.caption:
            lines.append(f"Table: {self.caption}")

        # Headers
        if self.headers:
            lines.append(" | ".join(self.headers))
            lines.append(" | ".join(["-" * len(header) for header in self.headers]))

        # Rows
        for row in self.rows:
            lines.append(" | ".join(str(cell) for cell in row))

        return "\n".join(lines) + "\n"


@dataclass
class LatexFigure:
    """A LaTeX figure."""

    caption: str
    label: str
    image_path: str


@dataclass
class LatexSubsubsection:
    """A LaTeX subsubsection."""

    title: str
    label: str
    number: str
    paragraphs: Optional[List[LatexParagraph]] = None


@dataclass
class LatexSubsection:
    """A LaTeX subsection."""

    title: str
    label: str
    number: str
    paragraphs: Optional[List[LatexParagraph]] = None
    subsubsections: Optional[List[LatexSubsubsection]] = None


@dataclass
class LatexSection:
    """A LaTeX section."""

    title: str
    label: str
    number: str
    paragraphs: Optional[List[LatexParagraph]] = None
    subsections: Optional[List[LatexSubsection]] = None


@dataclass
class LatexChapter:
    """A LaTeX chapter."""

    title: str
    label: str
    number: str
    paragraphs: Optional[List[LatexParagraph]] = None
    sections: Optional[List[LatexSection]] = None


@dataclass
class LatexDocument:
    """A LaTeX document."""

    title: str
    author: str
    year: str
    doi: str
    source_document: str
    page_reference: str
    chapters: Optional[List[LatexChapter]] = None
    sections: Optional[List[LatexSection]] = None
    subsections: Optional[List[LatexSubsection]] = None
    subsubsections: Optional[List[LatexSubsubsection]] = None
    paragraphs: Optional[List[LatexParagraph]] = None
    tables: Optional[List[LatexTable]] = None
    figures: Optional[List[LatexFigure]] = None


class LatexParser:
    """A helper class to parse Latex documents hierarchically.

    Args:
        document_path: The path to the Latex document.
        bibliography_path: Optional path to .bib file for enhanced citation parsing.
    """

    def __init__(self, document_path: str = None, bibliography_path: str = None):
        self.document_path = document_path
        self.bibliography_path = bibliography_path
        # If bibliography or document path is provided, load bibliography entries
        # otherwise, set bibliography entries to an empty dictionary
        self.bibliography_entries = (
            self._load_bibliography()
            if (self.bibliography_path or document_path)
            else {}
        )
        # If document path is provided, parse the document
        # otherwise, set document to None
        self.document = self.parse_document(document_path) if document_path else None

    def _load_bibliography(self) -> Dict[str, Citation]:
        """Load bibliography entries from bibliography_path file or document_path file."""
        if not (self.bibliography_path or self.document_path):
            return {}
        actual_path = self.bibliography_path or self.document_path
        try:
            with open(actual_path, "r", encoding="utf-8") as file:
                bib_content = file.read()
            return self._parse_bibtex(bib_content)
        except Exception as e:
            logger.warning(f"Could not load bibliography file: {e}")
            return {}

    def _parse_bibtex(self, bib_content: str) -> Dict[str, Citation]:
        """Parse BibTeX content into Citation objects."""
        entries = {}

        # Split into individual entries
        bib_entries = re.split(r"\n\s*\n", bib_content)

        for entry in bib_entries:
            if not entry.strip():
                continue

            # Extract entry type and key
            type_match = re.search(r"@(\w+)\{([^,]+),", entry)
            if not type_match:
                continue

            entry_type = type_match.group(1)
            entry_key = type_match.group(2)

            # Only process article, book, inproceedings, etc.
            if entry_type.lower() not in [
                "article",
                "book",
                "inproceedings",
                "conference",
                "techreport",
            ]:
                continue

            # Extract fields
            author = self._extract_bib_field(entry, "author", "Unknown")
            year = self._extract_bib_field(entry, "year", "Unknown")
            title = self._extract_bib_field(entry, "title", "Unknown")
            doi = self._extract_bib_field(entry, "doi", "")

            citation = Citation(
                author=author,
                year=year,
                title=title,
                doi=doi,
                source_document=self.bibliography_path or "unknown",
                page_reference="",
                citation_label=entry_key,
                citation_hash=hash(entry_key),
            )

            entries[entry_key] = citation

        return entries

    def _extract_bib_field(self, entry: str, field: str, default: str) -> str:
        """Extract a specific field from a BibTeX entry."""
        pattern = rf"{field}\s*=\s*{{([^}}]+)}}"
        match = re.search(pattern, entry, re.IGNORECASE)
        return match.group(1).strip() if match else default

    def parse_document(self, document_path: str) -> LatexDocument:
        """Parse a Latex file into a LatexDocument object."""
        try:
            with open(document_path, "r", encoding="utf-8") as file:
                document_text = file.read()
            return self.parse_document_text(document_text)
        except Exception as e:
            logger.error(f"Error parsing document: {e}")
            return None

    def parse_document_text(self, document_text: str) -> LatexDocument:
        """Parse a LaTeX document text into a LatexDocument object."""
        # Extract document metadata
        title = self._extract_title(document_text)
        author = self._extract_author(document_text)
        year = self._extract_year(document_text)
        doi = self._extract_doi(document_text)

        # Parse tables and figures FIRST (to remove them from text)
        tables = self._parse_tables(document_text)
        figures = self._parse_figures(document_text)

        # Clean document text by removing table/figure environments
        cleaned_text = self._remove_table_figure_environments(document_text)

        # Parse chapters hierarchically from cleaned text
        chapters = self._parse_chapters(cleaned_text)

        # Parse sections hierarchically from cleaned text
        sections = self._parse_sections(cleaned_text)

        return LatexDocument(
            title=title,
            author=author,
            year=year,
            doi=doi,
            source_document=self.document_path or "unknown",
            page_reference="1",
            sections=sections,
            tables=tables,
            figures=figures,
        )

    def _remove_table_figure_environments(self, text: str) -> str:
        """Remove table and figure environments from text to clean paragraphs."""
        # Remove table environments
        text = re.sub(r"\\begin\{table\}.*?\\end\{table\}", "", text, flags=re.DOTALL)

        # Remove figure environments
        text = re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", "", text, flags=re.DOTALL)

        # Remove any remaining table/figure related commands
        text = re.sub(r"\\caption\{[^}]*\}", "", text)
        text = re.sub(r"\\label\{[^}]*\}", "", text)
        text = re.sub(r"\\includegraphics\{[^}]*\}", "", text)

        # Clean up extra whitespace
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)

        return text

    def _extract_title(self, text: str) -> str:
        """Extract document title from LaTeX text."""
        title_match = re.search(r"\\title\{([^}]+)\}", text)
        return title_match.group(1) if title_match else "Untitled"

    def _extract_author(self, text: str) -> str:
        """Extract document author from LaTeX text."""
        author_match = re.search(r"\\author\{([^}]+)\}", text)
        return author_match.group(1) if author_match else "Unknown Author"

    def _extract_year(self, text: str) -> str:
        """Extract document year from LaTeX text."""
        year_match = re.search(r"\\date\{([^}]+)\}", text)
        if year_match:
            year_text = year_match.group(1)
            year_match = re.search(r"\b(\d{4})\b", year_text)
            return year_match.group(1) if year_match else year_text
        return "Unknown Year"

    def _extract_doi(self, text: str) -> str:
        """Extract DOI from LaTeX text."""
        doi_match = re.search(r"\\doi\{([^}]+)\}", text)
        return doi_match.group(1) if doi_match else ""

    def _parse_chapters(self, text: str) -> List[LatexChapter]:
        """Parse chapters hierarchically from LaTeX text."""
        chapters = []

        # Split text into chapter blocks
        chapter_blocks = self._split_into_chapters(text)

        for block in chapter_blocks:
            if block.strip():
                chapter = self._parse_single_chapter(block)
                if chapter:
                    chapters.append(chapter)

        return chapters

    def _split_into_chapters(self, text: str) -> List[str]:
        """Split LaTeX text into chapter blocks."""
        chapter_pattern = r"(\\chapter\*?\{[^}]+\}|\\section\*?\{[^}]+\}|\\subsection\*?\{[^}]+\}|\\subsubsection\*?\{[^}]+\})"
        return re.split(chapter_pattern, text)

    def _parse_single_chapter(self, chapter_text: str) -> Optional[LatexChapter]:
        """Parse a single chapter block into a LatexChapter object."""
        title_match = re.search(r"\\chapter\*?\{([^}]+)\}", chapter_text)
        chapter_text_after_title = re.sub(r"\\chapter\*?\{[^}]+\}", "", chapter_text)
        if not title_match:
            return None

        title = title_match.group(1)
        # Capture paragraphs before sections
        paragraphs = self._parse_paragraphs(chapter_text_after_title)

        sections = self._parse_sections(chapter_text)

        return LatexChapter(title=title, paragraphs=paragraphs)

    def _parse_sections(self, text: str) -> List[LatexSection]:
        """Parse sections hierarchically from LaTeX text."""
        sections = []

        # Split text into section blocks
        section_blocks = self._split_into_sections(text)

        for block in section_blocks:
            if block.strip():
                section = self._parse_single_section(block)
                if section:
                    sections.append(section)

        return sections

    def _split_into_sections(self, text: str) -> List[str]:
        """Split LaTeX text into section blocks."""
        # Remove document preamble
        text = re.sub(
            r"\\begin\{document\}.*?\\end\{document\}",
            r"\\end{document}",
            text,
            flags=re.DOTALL,
        )

        # Split by section commands
        section_pattern = r"(\\section\*?\{[^}]+\}|\\subsection\*?\{[^}]+\}|\\subsubsection\*?\{[^}]+\})"
        parts = re.split(section_pattern, text)

        # Group section commands with their content
        sections = []
        current_section = ""

        for i, part in enumerate(parts):
            if (
                part.startswith("\\section")
                or part.startswith("\\subsection")
                or part.startswith("\\subsubsection")
            ):
                if current_section:
                    sections.append(current_section)
                current_section = part
            else:
                current_section += part

        if current_section:
            sections.append(current_section)

        return sections

    def _parse_single_section(self, section_text: str) -> Optional[LatexSection]:
        """Parse a single section block into a LatexSection object."""
        # Extract section title
        title_match = re.search(r"\\section\*?\{([^}]+)\}", section_text)
        if not title_match:
            return None

        title = title_match.group(1)

        # Extract paragraphs
        paragraphs = self._parse_paragraphs(section_text)

        return LatexSection(title=title, paragraphs=paragraphs)

    def _parse_paragraphs(self, text: str) -> List[LatexParagraph]:
        """Parse paragraphs from section text."""
        paragraphs = []

        # Split by paragraph breaks (double newlines or \par commands)
        para_blocks = re.split(r"\n\s*\n|\s*\\par\s*", text)

        for block in para_blocks:
            block = block.strip()
            if block and not block.startswith("\\"):
                # Extract citations and embed them in text
                clean_content, citations = self._process_citations_in_text(block)

                if clean_content.strip():
                    paragraphs.append(
                        LatexParagraph(content=clean_content, citations=citations)
                    )

        return paragraphs

    def _process_citations_in_text(self, text: str) -> tuple[str, List[Citation]]:
        """Process citations in text, embedding them and creating Citation objects."""
        citations = []
        processed_text = text

        # Find all citation commands
        cite_patterns = [
            (r"\\cite\{([^}]+)\}", "\\cite"),
            (r"\\citep\{([^}]+)\}", "\\citep"),
            (r"\\citet\{([^}]+)\}", "\\citet"),
            (r"\\citeauthor\{([^}]+)\}", "\\citeauthor"),
            (r"\\citeyear\{([^}]+)\}", "\\citeyear"),
        ]

        for pattern, command in cite_patterns:
            matches = list(re.finditer(pattern, processed_text))

            for match in reversed(matches):  # Process in reverse to maintain indices
                citation_key = match.group(1)
                citation = self._get_or_create_citation(citation_key)
                citations.append(citation)

                # Replace citation command with embedded text
                replacement = self._format_citation_embedding(citation, command)
                start, end = match.span()
                processed_text = (
                    processed_text[:start] + replacement + processed_text[end:]
                )

        return processed_text, citations

    def _get_or_create_citation(self, citation_key: str) -> Citation:
        """Get existing citation from bibliography or create a new one."""
        if citation_key in self.bibliography_entries:
            return self.bibliography_entries[citation_key]

        # Create placeholder citation
        return Citation(
            author="Unknown",
            year="Unknown",
            title="Unknown",
            doi="",
            source_document=self.document_path or "unknown",
            page_reference="",
            citation_label=citation_key,
            citation_hash=hash(citation_key),
        )

    def _format_citation_embedding(self, citation: Citation, command: str) -> str:
        """Format citation embedding based on the citation command used."""
        if command == "\\cite":
            return f"[{citation.author}, {citation.year}, {citation.citation_label}]"
        elif command == "\\citep":
            return f"[{citation.author}, {citation.year}, {citation.citation_label}]"
        elif command == "\\citet":
            return f"[{citation.author}, {citation.year}, {citation.citation_label}]"
        elif command == "\\citeauthor":
            return citation.author
        elif command == "\\citeyear":
            return citation.year
        else:
            return f"[{citation.author}, {citation.year}, {citation.citation_label}]"

    def _parse_tables(self, text: str) -> List[LatexTable]:
        """Parse tables from LaTeX text."""
        tables = []

        # Find table environments
        table_pattern = r"\\begin\{table\}.*?\\end\{table\}"
        table_matches = re.finditer(table_pattern, text, re.DOTALL)

        for match in table_matches:
            table_text = match.group(0)
            table = self._parse_single_table(table_text)
            if table:
                tables.append(table)

        return tables

    def _parse_single_table(self, table_text: str) -> Optional[LatexTable]:
        """Parse a single table environment."""
        # Extract caption
        caption_match = re.search(r"\\caption\{([^}]+)\}", table_text)
        caption = caption_match.group(1) if caption_match else ""

        # Extract label
        label_match = re.search(r"\\label\{([^}]+)\}", table_text)
        label = label_match.group(1) if label_match else ""

        # Parse tabular content
        headers, rows = self._parse_tabular_content(table_text)

        return (
            LatexTable(caption=caption, label=label, headers=headers, rows=rows)
            if headers or rows
            else None
        )

    def _parse_tabular_content(
        self, table_text: str
    ) -> tuple[List[str], List[List[str]]]:
        """Parse tabular content from table text."""
        # Find tabular environment
        tabular_match = re.search(
            r"\\begin\{tabular\}.*?\\end\{tabular\}", table_text, re.DOTALL
        )
        if not tabular_match:
            return [], []

        tabular_text = tabular_match.group(0)

        # Remove the tabular commands and only keep the content
        tabular_text = re.sub(r"\\begin\{tabular\}", "", tabular_text)
        tabular_text = re.sub(r"\\end\{tabular\}", "", tabular_text)
        tabular_text = tabular_text.strip()

        # Remove column formatting like {|c|c|} at the start of tabular
        tabular_text = re.sub(r"^\s*\{[^\}]*\}\s*", "", tabular_text)
        tabular_text = tabular_text.strip()
        # Split into rows
        rows = []
        for line in tabular_text.split("\\\\"):
            if "&" in line:
                # Split by & and clean up
                cells = [
                    cell.strip().replace("\\hline", "").strip()
                    for cell in line.split("&")
                ]
                cells = [cell for cell in cells if cell]
                if cells:
                    rows.append(cells)

        # First row is headers
        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []

        return headers, data_rows

    def _parse_figures(self, text: str) -> List[LatexFigure]:
        """Parse figures from LaTeX text."""
        figures = []

        # Find figure environments
        figure_pattern = r"\\begin\{figure\}.*?\\end\{figure\}"
        figure_matches = re.finditer(figure_pattern, text, re.DOTALL)

        for match in figure_matches:
            figure_text = match.group(0)
            figure = self._parse_single_figure(figure_text)
            if figure:
                figures.append(figure)

        return figures

    def _parse_single_figure(self, figure_text: str) -> Optional[LatexFigure]:
        """Parse a single figure environment."""
        # Extract caption
        caption_match = re.search(r"\\caption\{([^}]+)\}", figure_text)
        caption = caption_match.group(1) if caption_match else ""

        # Extract label
        label_match = re.search(r"\\label\{([^}]+)\}", figure_text)
        label = label_match.group(1) if label_match else ""

        # Extract image path
        includegraphics_match = re.search(r"\\includegraphics\{([^}]+)\}", figure_text)
        image_path = includegraphics_match.group(1) if includegraphics_match else ""

        return LatexFigure(caption=caption, label=label, image_path=image_path)
