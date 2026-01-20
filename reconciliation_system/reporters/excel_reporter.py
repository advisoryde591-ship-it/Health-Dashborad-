import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ExcelReporter:
    """Generate Excel reconciliation reports."""

    def __init__(self):
        self.writer = None

    def generate_report(
        self,
        match_result,
        all_psp_transactions: pd.DataFrame,
        all_crm_records: pd.DataFrame,
        output_path: Path,
        report_date: Optional[str] = None
    ) -> bool:
        """
        Generate a complete reconciliation report in Excel format.

        Creates an Excel file with the following tabs:
        1. Summary - Overview statistics
        2. Matched - Successfully reconciled transactions
        3. Discrepancies - All issues requiring investigation
        4. All PSP Transactions - Complete list from PSP/bank files
        5. All CRM Records - Complete list from CRM export

        Args:
            match_result: MatchResult from TransactionMatcher
            all_psp_transactions: All normalized PSP transactions
            all_crm_records: All normalized CRM records
            output_path: Path for the output Excel file
            report_date: Date for the report (default: today)

        Returns:
            True if report generated successfully, False otherwise
        """
        report_date = report_date or datetime.now().strftime('%Y-%m-%d')

        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Tab 1: Summary
                self._write_summary_sheet(writer, match_result.summary, report_date)

                # Tab 2: Matched Transactions
                self._write_data_sheet(
                    writer,
                    match_result.matched,
                    'Matched',
                    'Successfully reconciled transactions'
                )

                # Tab 3: Discrepancies (combined)
                self._write_discrepancies_sheet(writer, match_result)

                # Tab 4: All PSP Transactions
                self._write_data_sheet(
                    writer,
                    all_psp_transactions,
                    'All PSP Transactions',
                    'All transactions from PSP/bank files'
                )

                # Tab 5: All CRM Records
                self._write_data_sheet(
                    writer,
                    all_crm_records,
                    'All CRM Records',
                    'All expected transactions from CRM'
                )

            logger.info(f"Report generated successfully: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return False

    def _write_summary_sheet(self, writer, summary: dict, report_date: str):
        """Write the summary statistics sheet."""
        summary_data = [
            ['Reconciliation Report', ''],
            ['Report Date', report_date],
            ['Generated At', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['', ''],
            ['SUMMARY', ''],
            ['', ''],
            ['Metric', 'Count', 'Amount (USD)'],
            ['Total PSP Transactions', summary['total_psp_transactions'], f"${summary.get('matched_amount', 0) + summary.get('mismatch_amount', 0) + summary.get('psp_only_amount', 0):,.2f}"],
            ['Total CRM Expected', summary['total_crm_records'], f"${summary.get('matched_amount', 0) + summary.get('mismatch_amount', 0) + summary.get('crm_only_amount', 0):,.2f}"],
            ['', '', ''],
            ['RESULTS', '', ''],
            ['Matched', summary['matched_count'], f"${summary.get('matched_amount', 0):,.2f}"],
            ['Amount Mismatch', summary['mismatch_count'], f"${summary.get('mismatch_amount', 0):,.2f}"],
            ['PSP Only (Unexpected)', summary['psp_only_count'], f"${summary.get('psp_only_amount', 0):,.2f}"],
            ['CRM Only (Missing)', summary['crm_only_count'], f"${summary.get('crm_only_amount', 0):,.2f}"],
            ['', '', ''],
            ['Match Rate', f"{summary.get('match_rate', 0):.1f}%", ''],
        ]

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False, header=False)

        # Format the sheet
        worksheet = writer.sheets['Summary']
        worksheet.column_dimensions['A'].width = 25
        worksheet.column_dimensions['B'].width = 20
        worksheet.column_dimensions['C'].width = 20

    def _write_discrepancies_sheet(self, writer, match_result):
        """Write the combined discrepancies sheet."""
        discrepancy_frames = []

        # Add amount mismatches
        if not match_result.amount_mismatch.empty:
            df = match_result.amount_mismatch.copy()
            df['issue_type'] = 'AMOUNT_MISMATCH'
            discrepancy_frames.append(df)

        # Add PSP-only transactions
        if not match_result.psp_only.empty:
            df = match_result.psp_only.copy()
            df['issue_type'] = 'PSP_ONLY (Unexpected)'
            discrepancy_frames.append(df)

        # Add CRM-only records
        if not match_result.crm_only.empty:
            df = match_result.crm_only.copy()
            df['issue_type'] = 'CRM_ONLY (Missing)'
            discrepancy_frames.append(df)

        if discrepancy_frames:
            combined = pd.concat(discrepancy_frames, ignore_index=True)

            # Reorder columns for clarity
            priority_cols = ['issue_type', 'psp_name', 'date', 'transaction_id',
                           'amount_usd', 'crm_amount', 'amount_difference', 'match_percentage']
            other_cols = [c for c in combined.columns if c not in priority_cols]
            final_cols = [c for c in priority_cols if c in combined.columns] + other_cols

            combined = combined[final_cols]
            combined.to_excel(writer, sheet_name='Discrepancies', index=False)

            # Adjust column widths
            worksheet = writer.sheets['Discrepancies']
            for i, col in enumerate(combined.columns):
                worksheet.column_dimensions[chr(65 + i)].width = 15
        else:
            # No discrepancies - write empty sheet with message
            pd.DataFrame({'Message': ['No discrepancies found!']}).to_excel(
                writer, sheet_name='Discrepancies', index=False
            )

    def _write_data_sheet(
        self,
        writer,
        df: pd.DataFrame,
        sheet_name: str,
        description: str
    ):
        """Write a data sheet with the given DataFrame."""
        if df.empty:
            pd.DataFrame({'Message': [f'No data - {description}']}).to_excel(
                writer, sheet_name=sheet_name, index=False
            )
            return

        df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Adjust column widths
        worksheet = writer.sheets[sheet_name]
        for i, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).apply(len).max() if len(df) > 0 else 0,
                len(str(col))
            )
            worksheet.column_dimensions[chr(65 + i % 26)].width = min(max_len + 2, 30)

    def generate_quick_summary(self, match_result) -> str:
        """
        Generate a text summary of the match results.

        Args:
            match_result: MatchResult from TransactionMatcher

        Returns:
            Formatted text summary
        """
        s = match_result.summary

        return f"""
========================================
       RECONCILIATION SUMMARY
========================================

Total PSP Transactions:  {s['total_psp_transactions']:,}
Total CRM Records:       {s['total_crm_records']:,}

RESULTS:
  Matched:               {s['matched_count']:,} (${s.get('matched_amount', 0):,.2f})
  Amount Mismatch:       {s['mismatch_count']:,} (${s.get('mismatch_amount', 0):,.2f})
  PSP Only (Unexpected): {s['psp_only_count']:,} (${s.get('psp_only_amount', 0):,.2f})
  CRM Only (Missing):    {s['crm_only_count']:,} (${s.get('crm_only_amount', 0):,.2f})

Match Rate: {s.get('match_rate', 0):.1f}%
========================================
"""
