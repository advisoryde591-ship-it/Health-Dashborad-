import pandas as pd
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Normalizer:
    """Normalize transaction data from various PSP formats to a standard format."""

    # Standard output columns
    STANDARD_COLUMNS = [
        'psp_name',
        'date',
        'transaction_id',
        'amount_original',
        'currency_original',
        'amount_usd',
        'name',
        'type',
        'status'
    ]

    def __init__(self, mappings_file: Optional[Path] = None):
        """
        Initialize the normalizer.

        Args:
            mappings_file: Path to JSON file with PSP column mappings
        """
        self.mappings = {}

        if mappings_file and mappings_file.exists():
            self.load_mappings(mappings_file)

    def load_mappings(self, mappings_file: Path) -> bool:
        """
        Load PSP column mappings from a JSON file.

        Args:
            mappings_file: Path to the mappings JSON file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(mappings_file, 'r') as f:
                self.mappings = json.load(f)

            logger.info(f"Loaded mappings for {len(self.mappings)} PSPs")
            return True

        except Exception as e:
            logger.error(f"Error loading PSP mappings: {str(e)}")
            return False

    def add_mapping(self, psp_name: str, mapping: Dict[str, Any]):
        """
        Add or update a PSP mapping.

        Args:
            psp_name: Name of the PSP
            mapping: Column mapping configuration
        """
        self.mappings[psp_name.lower()] = mapping
        logger.info(f"Added mapping for PSP: {psp_name}")

    def detect_psp(self, filename: str) -> Optional[str]:
        """
        Try to detect PSP from filename.

        Args:
            filename: Name of the file

        Returns:
            PSP name if detected, None otherwise
        """
        filename_lower = filename.lower()

        for psp_name, mapping in self.mappings.items():
            file_pattern = mapping.get('file_pattern', '').lower()
            if file_pattern:
                # Simple pattern matching (convert glob to basic check)
                pattern_base = file_pattern.replace('*', '').replace('.csv', '').replace('.xlsx', '')
                if pattern_base in filename_lower:
                    return psp_name

            # Also check if PSP name is in filename
            if psp_name.lower() in filename_lower:
                return psp_name

        return None

    def normalize(
        self,
        df: pd.DataFrame,
        psp_name: str,
        currency_converter=None
    ) -> Optional[pd.DataFrame]:
        """
        Normalize a DataFrame to the standard format.

        Args:
            df: Input DataFrame from a PSP file
            psp_name: Name of the PSP (must have mapping configured)
            currency_converter: Optional CurrencyConverter instance for USD conversion

        Returns:
            Normalized DataFrame, or None if normalization fails
        """
        psp_name_lower = psp_name.lower()

        if psp_name_lower not in self.mappings:
            logger.error(f"No mapping found for PSP: {psp_name}")
            return None

        mapping = self.mappings[psp_name_lower]
        column_mapping = mapping.get('column_mapping', {})

        try:
            normalized = pd.DataFrame()

            # Add PSP name
            normalized['psp_name'] = psp_name

            # Map each required column
            for std_col, src_col in column_mapping.items():
                if src_col in df.columns:
                    normalized[std_col] = df[src_col]
                else:
                    logger.warning(f"Column '{src_col}' not found in {psp_name} data")
                    normalized[std_col] = None

            # Rename amount column
            if 'amount' in normalized.columns:
                normalized['amount_original'] = normalized['amount']
                normalized.drop('amount', axis=1, inplace=True)

            # Rename currency column
            if 'currency' in normalized.columns:
                normalized['currency_original'] = normalized['currency']
                normalized.drop('currency', axis=1, inplace=True)

            # Handle amount divisor (e.g., Stripe uses cents)
            amount_divisor = mapping.get('amount_divisor', 1)
            if amount_divisor != 1 and 'amount_original' in normalized.columns:
                normalized['amount_original'] = normalized['amount_original'] / amount_divisor

            # Parse dates
            date_format = mapping.get('date_format')
            if 'date' in normalized.columns and date_format:
                try:
                    normalized['date'] = pd.to_datetime(
                        normalized['date'],
                        format=date_format,
                        errors='coerce'
                    )
                except Exception:
                    # Try automatic parsing
                    normalized['date'] = pd.to_datetime(
                        normalized['date'],
                        errors='coerce'
                    )

            # Convert to USD if converter provided
            if currency_converter and 'amount_original' in normalized.columns:
                normalized['amount_usd'] = normalized.apply(
                    lambda row: currency_converter.convert_to_usd(
                        row.get('amount_original', 0),
                        row.get('currency_original', 'USD')
                    ),
                    axis=1
                )
            else:
                normalized['amount_usd'] = normalized.get('amount_original')

            # Ensure all standard columns exist
            for col in self.STANDARD_COLUMNS:
                if col not in normalized.columns:
                    normalized[col] = None

            # Reorder columns
            normalized = normalized[self.STANDARD_COLUMNS]

            logger.info(f"Normalized {len(normalized)} transactions from {psp_name}")
            return normalized

        except Exception as e:
            logger.error(f"Error normalizing {psp_name} data: {str(e)}")
            return None

    def normalize_crm(
        self,
        df: pd.DataFrame,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> Optional[pd.DataFrame]:
        """
        Normalize CRM export to standard format.

        Expected CRM columns (configurable):
        - psp_id: The transaction ID from the PSP
        - expected_date: Expected transaction date
        - expected_amount_usd: Expected amount in USD
        - customer_name: Customer name

        Args:
            df: CRM export DataFrame
            column_mapping: Optional custom column mapping

        Returns:
            Normalized CRM DataFrame
        """
        # Default CRM column mapping
        default_mapping = {
            'psp_id': 'psp_id',
            'expected_date': 'expected_date',
            'expected_amount_usd': 'expected_amount_usd',
            'customer_name': 'customer_name',
            'status': 'status'
        }

        mapping = column_mapping or default_mapping

        try:
            normalized = pd.DataFrame()

            for std_col, src_col in mapping.items():
                if src_col in df.columns:
                    normalized[std_col] = df[src_col]
                else:
                    # Try case-insensitive match
                    matching_cols = [c for c in df.columns if c.lower() == src_col.lower()]
                    if matching_cols:
                        normalized[std_col] = df[matching_cols[0]]
                    else:
                        logger.warning(f"CRM column '{src_col}' not found")
                        normalized[std_col] = None

            # Parse dates
            if 'expected_date' in normalized.columns:
                normalized['expected_date'] = pd.to_datetime(
                    normalized['expected_date'],
                    errors='coerce'
                )

            logger.info(f"Normalized {len(normalized)} CRM records")
            return normalized

        except Exception as e:
            logger.error(f"Error normalizing CRM data: {str(e)}")
            return None
