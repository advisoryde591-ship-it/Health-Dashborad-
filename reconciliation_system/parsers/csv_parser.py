import pandas as pd
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CSVParser:
    """Parser for CSV files from PSPs and banks."""

    def __init__(self):
        self.supported_extensions = ['.csv']

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in self.supported_extensions

    def parse(self, file_path: Path, encoding: str = 'utf-8') -> Optional[pd.DataFrame]:
        """
        Parse a CSV file and return a DataFrame.

        Args:
            file_path: Path to the CSV file
            encoding: File encoding (default: utf-8)

        Returns:
            DataFrame with the parsed data, or None if parsing fails
        """
        try:
            # Try different encodings if utf-8 fails
            encodings_to_try = [encoding, 'utf-8', 'latin-1', 'cp1252']

            for enc in encodings_to_try:
                try:
                    df = pd.read_csv(file_path, encoding=enc)
                    logger.info(f"Successfully parsed {file_path.name} with encoding {enc}")
                    return df
                except UnicodeDecodeError:
                    continue

            logger.error(f"Failed to parse {file_path.name} with any encoding")
            return None

        except Exception as e:
            logger.error(f"Error parsing CSV file {file_path.name}: {str(e)}")
            return None

    def parse_with_options(
        self,
        file_path: Path,
        delimiter: str = ',',
        skip_rows: int = 0,
        encoding: str = 'utf-8'
    ) -> Optional[pd.DataFrame]:
        """
        Parse a CSV file with custom options.

        Args:
            file_path: Path to the CSV file
            delimiter: Column delimiter (default: comma)
            skip_rows: Number of rows to skip at the start
            encoding: File encoding

        Returns:
            DataFrame with the parsed data, or None if parsing fails
        """
        try:
            df = pd.read_csv(
                file_path,
                delimiter=delimiter,
                skiprows=skip_rows,
                encoding=encoding
            )
            logger.info(f"Successfully parsed {file_path.name}")
            return df
        except Exception as e:
            logger.error(f"Error parsing CSV file {file_path.name}: {str(e)}")
            return None
