#!/usr/bin/env python3
"""
Automated Reconciliation System
================================
Reconcile PSP/bank transactions against CRM records.

Usage:
    python main.py --date 2026-01-20
    python main.py --input /path/to/files --date 2026-01-20
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

from parsers import CSVParser, ExcelParser, PDFParser, PDF_PARSER_AVAILABLE
from processors import Normalizer, CurrencyConverter, TransactionMatcher
from reporters import ExcelReporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('reconciliation.log')
    ]
)
logger = logging.getLogger(__name__)


class ReconciliationSystem:
    """Main orchestrator for the reconciliation process."""

    def __init__(self, base_path: Path):
        """
        Initialize the reconciliation system.

        Args:
            base_path: Base directory containing input/output/config folders
        """
        self.base_path = base_path
        self.input_path = base_path / 'input'
        self.psp_path = self.input_path / 'psp_files'
        self.crm_path = self.input_path / 'crm_report'
        self.output_path = base_path / 'output'
        self.config_path = base_path / 'config'

        # Initialize components
        self.csv_parser = CSVParser()
        self.excel_parser = ExcelParser()
        self.pdf_parser = PDFParser() if (PDF_PARSER_AVAILABLE and PDFParser) else None

        self.normalizer = Normalizer(self.config_path / 'psp_mappings.json')
        self.currency_converter = CurrencyConverter(self.config_path / 'exchange_rates.json')
        self.matcher = TransactionMatcher(amount_tolerance=0.95)
        self.reporter = ExcelReporter()

    def run(self, report_date: str = None) -> bool:
        """
        Run the full reconciliation process.

        Args:
            report_date: Date for the report (default: today)

        Returns:
            True if successful, False otherwise
        """
        report_date = report_date or datetime.now().strftime('%Y-%m-%d')
        logger.info(f"Starting reconciliation for {report_date}")

        # Step 1: Parse all PSP files
        logger.info("Step 1: Parsing PSP/bank files...")
        psp_transactions = self._parse_psp_files()

        if psp_transactions.empty:
            logger.warning("No PSP transactions found!")

        # Step 2: Parse CRM export
        logger.info("Step 2: Parsing CRM export...")
        crm_records = self._parse_crm_files()

        if crm_records.empty:
            logger.warning("No CRM records found!")

        # Step 3: Run matching
        logger.info("Step 3: Running transaction matching...")
        match_result = self.matcher.match(
            psp_transactions,
            crm_records,
            psp_id_column='transaction_id',
            crm_id_column='psp_id',
            psp_amount_column='amount_usd',
            crm_amount_column='expected_amount_usd'
        )

        # Step 4: Generate report
        logger.info("Step 4: Generating report...")
        output_file = self.output_path / f'reconciliation_report_{report_date}.xlsx'

        success = self.reporter.generate_report(
            match_result,
            psp_transactions,
            crm_records,
            output_file,
            report_date
        )

        if success:
            # Print summary
            print(self.reporter.generate_quick_summary(match_result))
            print(f"\nReport saved to: {output_file}")
            logger.info(f"Reconciliation complete. Report: {output_file}")
        else:
            logger.error("Failed to generate report")

        return success

    def _parse_psp_files(self) -> pd.DataFrame:
        """Parse all PSP/bank files and return normalized transactions."""
        all_transactions = []

        if not self.psp_path.exists():
            logger.warning(f"PSP folder not found: {self.psp_path}")
            return pd.DataFrame()

        # Get all files
        files = list(self.psp_path.glob('*'))
        logger.info(f"Found {len(files)} files in PSP folder")

        for file_path in files:
            if file_path.is_dir():
                continue

            logger.info(f"Processing: {file_path.name}")

            # Parse file based on type
            df = self._parse_file(file_path)

            if df is None or df.empty:
                logger.warning(f"Could not parse: {file_path.name}")
                continue

            # Detect PSP and normalize
            psp_name = self.normalizer.detect_psp(file_path.name)

            if psp_name is None:
                logger.warning(f"Unknown PSP format for: {file_path.name}")
                # Try to use filename as PSP name
                psp_name = file_path.stem.split('_')[0]

            normalized = self.normalizer.normalize(
                df, psp_name, self.currency_converter
            )

            if normalized is not None and not normalized.empty:
                all_transactions.append(normalized)
                logger.info(f"Normalized {len(normalized)} transactions from {file_path.name}")

        if all_transactions:
            return pd.concat(all_transactions, ignore_index=True)

        return pd.DataFrame()

    def _parse_crm_files(self) -> pd.DataFrame:
        """Parse CRM export file(s)."""
        all_records = []

        if not self.crm_path.exists():
            logger.warning(f"CRM folder not found: {self.crm_path}")
            return pd.DataFrame()

        files = list(self.crm_path.glob('*'))
        logger.info(f"Found {len(files)} files in CRM folder")

        for file_path in files:
            if file_path.is_dir():
                continue

            logger.info(f"Processing CRM file: {file_path.name}")

            df = self._parse_file(file_path)

            if df is None or df.empty:
                logger.warning(f"Could not parse CRM file: {file_path.name}")
                continue

            # Load CRM mapping if exists
            crm_mapping_file = self.config_path / 'crm_mapping.json'
            crm_mapping = None

            if crm_mapping_file.exists():
                import json
                with open(crm_mapping_file, 'r') as f:
                    crm_config = json.load(f)
                    crm_mapping = crm_config.get('column_mapping')

            normalized = self.normalizer.normalize_crm(df, crm_mapping)

            if normalized is not None and not normalized.empty:
                all_records.append(normalized)
                logger.info(f"Loaded {len(normalized)} CRM records")

        if all_records:
            return pd.concat(all_records, ignore_index=True)

        return pd.DataFrame()

    def _parse_file(self, file_path: Path) -> pd.DataFrame:
        """Parse a file using the appropriate parser."""
        suffix = file_path.suffix.lower()

        if suffix == '.csv':
            return self.csv_parser.parse(file_path)
        elif suffix in ['.xlsx', '.xls']:
            return self.excel_parser.parse(file_path)
        elif suffix == '.pdf':
            if self.pdf_parser:
                return self.pdf_parser.parse(file_path)
            else:
                logger.warning("PDF parsing not available. Install pdfplumber.")
                return None
        else:
            logger.warning(f"Unsupported file type: {suffix}")
            return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Automated Reconciliation System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py --date 2026-01-20
    python main.py --input /custom/path --date 2026-01-20

Folder Structure:
    input/
        psp_files/      <- Drop PSP/bank files here
        crm_report/     <- Drop CRM export here
    output/             <- Reports will be saved here
    config/             <- PSP mappings and exchange rates
        """
    )

    parser.add_argument(
        '--date', '-d',
        type=str,
        default=datetime.now().strftime('%Y-%m-%d'),
        help='Report date (default: today)'
    )

    parser.add_argument(
        '--input', '-i',
        type=str,
        default=None,
        help='Base input directory (default: current directory)'
    )

    args = parser.parse_args()

    # Determine base path
    if args.input:
        base_path = Path(args.input)
    else:
        base_path = Path(__file__).parent

    # Verify folders exist
    required_folders = ['input/psp_files', 'input/crm_report', 'output', 'config']
    for folder in required_folders:
        folder_path = base_path / folder
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created folder: {folder_path}")

    # Run reconciliation
    system = ReconciliationSystem(base_path)
    success = system.run(args.date)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
