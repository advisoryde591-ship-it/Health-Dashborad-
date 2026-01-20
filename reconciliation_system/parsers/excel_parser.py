import pandas as pd
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class ExcelParser:
    """Parser for Excel files (.xlsx, .xls) from PSPs and banks."""

    def __init__(self):
        self.supported_extensions = ['.xlsx', '.xls']

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in self.supported_extensions

    def parse(self, file_path: Path, sheet_name: int | str = 0) -> Optional[pd.DataFrame]:
        """
        Parse an Excel file and return a DataFrame.

        Args:
            file_path: Path to the Excel file
            sheet_name: Sheet name or index (default: first sheet)

        Returns:
            DataFrame with the parsed data, or None if parsing fails
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            logger.info(f"Successfully parsed {file_path.name}, sheet: {sheet_name}")
            return df
        except Exception as e:
            logger.error(f"Error parsing Excel file {file_path.name}: {str(e)}")
            return None

    def get_sheet_names(self, file_path: Path) -> List[str]:
        """
        Get list of sheet names in the Excel file.

        Args:
            file_path: Path to the Excel file

        Returns:
            List of sheet names
        """
        try:
            xl = pd.ExcelFile(file_path)
            return xl.sheet_names
        except Exception as e:
            logger.error(f"Error reading sheet names from {file_path.name}: {str(e)}")
            return []

    def parse_all_sheets(self, file_path: Path) -> dict[str, pd.DataFrame]:
        """
        Parse all sheets in an Excel file.

        Args:
            file_path: Path to the Excel file

        Returns:
            Dictionary mapping sheet names to DataFrames
        """
        try:
            dfs = pd.read_excel(file_path, sheet_name=None)
            logger.info(f"Successfully parsed all {len(dfs)} sheets from {file_path.name}")
            return dfs
        except Exception as e:
            logger.error(f"Error parsing Excel file {file_path.name}: {str(e)}")
            return {}

    def parse_with_options(
        self,
        file_path: Path,
        sheet_name: int | str = 0,
        skip_rows: int = 0,
        use_cols: Optional[List[str]] = None
    ) -> Optional[pd.DataFrame]:
        """
        Parse an Excel file with custom options.

        Args:
            file_path: Path to the Excel file
            sheet_name: Sheet name or index
            skip_rows: Number of rows to skip at the start
            use_cols: List of column names to read (None = all)

        Returns:
            DataFrame with the parsed data, or None if parsing fails
        """
        try:
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                skiprows=skip_rows,
                usecols=use_cols
            )
            logger.info(f"Successfully parsed {file_path.name}")
            return df
        except Exception as e:
            logger.error(f"Error parsing Excel file {file_path.name}: {str(e)}")
            return None
