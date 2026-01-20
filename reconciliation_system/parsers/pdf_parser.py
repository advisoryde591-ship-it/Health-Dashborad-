import pandas as pd
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class PDFParser:
    """Parser for PDF files (bank statements) with tabular data."""

    def __init__(self):
        self.supported_extensions = ['.pdf']
        self._pdfplumber_available = False
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if PDF parsing libraries are available."""
        try:
            import pdfplumber
            self._pdfplumber_available = True
        except ImportError:
            logger.warning(
                "pdfplumber not installed. PDF parsing will be limited. "
                "Install with: pip install pdfplumber"
            )

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return (
            file_path.suffix.lower() in self.supported_extensions
            and self._pdfplumber_available
        )

    def parse(self, file_path: Path, pages: Optional[List[int]] = None) -> Optional[pd.DataFrame]:
        """
        Parse a PDF file and extract tabular data.

        Args:
            file_path: Path to the PDF file
            pages: List of page numbers to parse (None = all pages)

        Returns:
            DataFrame with the extracted data, or None if parsing fails
        """
        if not self._pdfplumber_available:
            logger.error("pdfplumber not available. Cannot parse PDF.")
            return None

        try:
            import pdfplumber

            all_tables = []

            with pdfplumber.open(file_path) as pdf:
                pages_to_process = pages if pages else range(len(pdf.pages))

                for page_num in pages_to_process:
                    if page_num >= len(pdf.pages):
                        continue

                    page = pdf.pages[page_num]
                    tables = page.extract_tables()

                    for table in tables:
                        if table and len(table) > 1:
                            # First row is header
                            df = pd.DataFrame(table[1:], columns=table[0])
                            all_tables.append(df)

            if not all_tables:
                logger.warning(f"No tables found in {file_path.name}")
                return None

            # Combine all tables
            result = pd.concat(all_tables, ignore_index=True)
            logger.info(f"Successfully extracted {len(result)} rows from {file_path.name}")
            return result

        except Exception as e:
            logger.error(f"Error parsing PDF file {file_path.name}: {str(e)}")
            return None

    def extract_text(self, file_path: Path) -> Optional[str]:
        """
        Extract raw text from PDF (for debugging or manual processing).

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text, or None if extraction fails
        """
        if not self._pdfplumber_available:
            logger.error("pdfplumber not available. Cannot extract text.")
            return None

        try:
            import pdfplumber

            text_parts = []

            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"Error extracting text from {file_path.name}: {str(e)}")
            return None

    def get_table_count(self, file_path: Path) -> int:
        """
        Count the number of tables in a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Number of tables found
        """
        if not self._pdfplumber_available:
            return 0

        try:
            import pdfplumber

            count = 0
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    count += len(tables)

            return count

        except Exception as e:
            logger.error(f"Error counting tables in {file_path.name}: {str(e)}")
            return 0
