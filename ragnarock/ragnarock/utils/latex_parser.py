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

    def to_text(self, citation_command: str) -> str:
        """Convert the citation to a text string."""
        if citation_command == "\\cite":
            return f"[{self.author}, {self.year}, {self.citation_label}]"
        elif citation_command == "\\citep":
            return f"[{self.author}, {self.year}, {self.citation_label}]"
        elif citation_command == "\\citet":
            return f"[{self.author}, {self.year}, {self.citation_label}]"
        elif citation_command == "\\citeauthor":
            return self.author
        elif citation_command == "\\citeyear":
            return self.year
        else:
            return f"[{self.author}, {self.year}, {self.citation_label}]"


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
    paragraphs: Optional[List[LatexParagraph]] = None


@dataclass
class LatexSubsection:
    """A LaTeX subsection."""

    title: str
    label: str
    paragraphs: Optional[List[LatexParagraph]] = None
    subsubsections: Optional[List[LatexSubsubsection]] = None


@dataclass
class LatexSection:
    """A LaTeX section."""

    title: str
    label: str
    paragraphs: Optional[List[LatexParagraph]] = None
    # subsections: Optional[List[LatexSubsection]] = None


@dataclass
class LatexChapter:
    """A LaTeX chapter."""

    title: str
    label: str
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
            if (self.bibliography_path or self.document_path)
            else {}
        )
        # If document path is provided, parse the document
        # otherwise, set document to None
        self.document = self.parse_document(document_path) if document_path else None

    def parse_bibliography(self, bibliography_path: str):
        """Parse the bibliography."""
        self.bibliography_path = bibliography_path
        self.bibliography_entries = self._load_bibliography()

    def get_bibliography_entries(self) -> Dict[str, Citation]:
        """Get the bibliography entries."""
        return self.bibliography_entries

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
            if not self.document_path:
                self.document_path = document_path
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

        cleaned_text = self._remove_document_preamble(document_text)

        # Parse tables and figures FIRST (to remove them from text)
        tables, cleaned_text = self._parse_tables(cleaned_text)
        figures, cleaned_text = self._parse_figures(cleaned_text)

        # Parse chapters hierarchically from cleaned text
        chapters, cleaned_text = self._parse_chapters(cleaned_text)

        # Parse sections hierarchically from cleaned text
        sections, cleaned_text = self._parse_sections(cleaned_text)

        # Parse paragraphs from remaining text
        paragraphs = self._parse_paragraphs(cleaned_text)

        return LatexDocument(
            title=title,
            author=author,
            year=year,
            doi=doi,
            source_document=self.document_path,
            page_reference="1",
            chapters=chapters,
            sections=sections,
            paragraphs=paragraphs,
            tables=tables,
            figures=figures,
        )

    def _remove_document_preamble(self, text: str) -> str:
        """Remove document preamble from text."""
        return re.sub(r"\\begin\{document\}|\\end\{document\}", "", text)

    def _extract_title(self, text: str) -> str:
        """Extract document title from LaTeX text."""
        title_match = re.search(r"\\title\{([^}]+)\}", text)
        return title_match.group(1) if title_match else ""

    def _extract_author(self, text: str) -> str:
        """Extract document author from LaTeX text."""
        author_match = re.search(r"\\author\{([^}]+)\}", text)
        return author_match.group(1) if author_match else ""

    def _extract_year(self, text: str) -> str:
        """Extract document year from LaTeX text."""
        year_match = re.search(r"\\date\{([^}]+)\}", text)
        if year_match:
            year_text = year_match.group(1)
            year_match = re.search(r"\b(\d{4})\b", year_text)
            return year_match.group(1) if year_match else year_text
        return ""

    def _extract_label(self, text: str) -> str:
        """Extract label from LaTeX text."""
        label_match = re.search(r"\\label\{([^}]+)\}", text)
        return label_match.group(1) if label_match else ""

    def _extract_doi(self, text: str) -> str:
        """Extract DOI from LaTeX text."""
        doi_match = re.search(r"\\doi\{([^}]+)\}", text)
        return doi_match.group(1) if doi_match else ""

    def _parse_chapters(self, text: str) -> tuple[List[LatexChapter], str]:
        """Parse chapters hierarchically from LaTeX text."""
        chapters = []
        remaining_text = text
        # Split text into chapter blocks
        chapter_blocks = self._split_into_chapters(text)

        for block in chapter_blocks:
            if block.strip():
                chapter = self._parse_single_chapter(block)
                if chapter:
                    chapters.append(chapter)
                    remaining_text = remaining_text.replace(block, "", 1)

        return chapters, remaining_text

    def _split_into_chapters(self, text: str) -> List[str]:
        """Split LaTeX text into chapter blocks."""
        # Use re.finditer to match chapter command and its content together
        chapter_pattern = r"(\\chapter\*?\{[^}]+\}.*?)(?=(\\chapter\*?\{[^}]+\})|$)"
        matches = re.finditer(chapter_pattern, text, re.DOTALL)
        return [m.group(1) for m in matches]

    def _parse_single_chapter(self, chapter_text: str) -> Optional[LatexChapter]:
        """Parse a single chapter block into a LatexChapter object."""
        title_match = re.search(r"\\chapter\*?\{([^}]+)\}", chapter_text)
        chapter_text_after_title = re.sub(r"\\chapter\*?\{[^}]+\}", "", chapter_text)
        if not title_match:
            return None

        title = title_match.group(1)
        label = self._extract_label(chapter_text)
        chapter_text_after_label = re.sub(
            r"\\label\{[^}]+\}", "", chapter_text_after_title, count=1
        )

        # capture sections
        sections, remaining_text = self._parse_sections(chapter_text_after_label)

        # capture paragraphs
        paragraphs = self._parse_paragraphs(remaining_text)

        return LatexChapter(
            title=title, label=label, paragraphs=paragraphs, sections=sections
        )

    def _parse_sections(self, text: str) -> tuple[List[LatexSection], str]:
        """Parse sections hierarchically from LaTeX text.
        Returns:
            List[LatexSection]: List of sections
            str: Remaining text after sections are parsed and removed
        """
        sections = []
        remaining_text = text
        # Split text into section blocks
        section_blocks = self._split_into_sections(text)

        for block in section_blocks:
            if block.strip():
                section = self._parse_single_section(block)
                if section:
                    remaining_text = remaining_text.replace(block, "", 1)
                    sections.append(section)

        return sections, remaining_text

    def _split_into_sections(self, text: str) -> List[str]:
        """Split LaTeX text into section blocks which start with section, subsection, or subsubsection.
        Any other text not part of a section command is ignored.
        Returns:
            List[str]: List of section blocks
        """

        # Split by section, subsection, or subsubsection commands
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
            elif i > 0:
                current_section += part

        if current_section:
            sections.append(current_section)

        return sections

    def _parse_single_section(self, section_text: str) -> Optional[LatexSection]:
        """Parse a single section block into a LatexSection object."""

        regular_expression = r"\\section\*?\{([^}]+)\}|\\subsection\*?\{([^}]+)\}|\\subsubsection\*?\{([^}]+)\}"

        # Extract section title
        title_match = re.search(
            regular_expression,
            section_text,
        )
        if not title_match:
            return None

        title = (
            title_match.group(1)
            if title_match.group(1)
            else title_match.group(2) if title_match.group(2) else title_match.group(3)
        )

        # Remove the section command
        section_text = re.sub(regular_expression, "", section_text)

        # capture label
        label = self._extract_label(section_text)
        section_text_after_label = re.sub(
            r"\\label\{[^}]+\}", "", section_text, count=1
        )

        # Extract paragraphs
        paragraphs = self._parse_paragraphs(section_text_after_label)

        return LatexSection(title=title, label=label, paragraphs=paragraphs)

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
                replacement = citation.to_text(command)
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

    def _parse_tables(self, text: str) -> tuple[List[LatexTable], str]:
        """Parse tables from LaTeX text."""
        tables = []
        remaining_text = text

        # Find table environments
        table_pattern = r"\\begin\{table\}.*?\\end\{table\}"
        table_matches = re.finditer(table_pattern, text, re.DOTALL)

        for match in table_matches:
            table_text = match.group(0)
            table = self._parse_single_table(table_text)
            if table:
                tables.append(table)
                # remove the table text from the text
                remaining_text = remaining_text.replace(table_text, "", 1)

        return tables, remaining_text

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

    def _parse_figures(self, text: str) -> tuple[List[LatexFigure], str]:
        """Parse figures from LaTeX text."""
        figures = []
        remaining_text = text
        # Find figure environments
        figure_pattern = r"\\begin\{figure\}.*?\\end\{figure\}"
        figure_matches = re.finditer(figure_pattern, text, re.DOTALL)

        for match in figure_matches:
            figure_text = match.group(0)
            figure = self._parse_single_figure(figure_text)
            if figure:
                figures.append(figure)
                # remove the figure text from the text
                remaining_text = remaining_text.replace(figure_text, "", 1)

        return figures, remaining_text

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
