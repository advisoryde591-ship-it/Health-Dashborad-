import pandas as pd
from enum import Enum
from typing import Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class MatchStatus(Enum):
    """Status categories for transaction matching."""
    MATCHED = "MATCHED"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    PSP_ONLY = "PSP_ONLY"
    CRM_ONLY = "CRM_ONLY"


@dataclass
class MatchResult:
    """Result of the matching process."""
    matched: pd.DataFrame
    amount_mismatch: pd.DataFrame
    psp_only: pd.DataFrame
    crm_only: pd.DataFrame
    summary: dict


class TransactionMatcher:
    """Match PSP transactions against CRM records."""

    def __init__(self, amount_tolerance: float = 0.95):
        """
        Initialize the matcher.

        Args:
            amount_tolerance: Minimum ratio for amount match (default: 95%)
        """
        self.amount_tolerance = amount_tolerance

    def calculate_match_percentage(self, amount1: float, amount2: float) -> float:
        """
        Calculate the match percentage between two amounts.

        Args:
            amount1: First amount
            amount2: Second amount

        Returns:
            Match percentage (0.0 to 1.0)
        """
        if amount1 == 0 and amount2 == 0:
            return 1.0
        if amount1 == 0 or amount2 == 0:
            return 0.0

        return min(amount1, amount2) / max(amount1, amount2)

    def match(
        self,
        psp_transactions: pd.DataFrame,
        crm_records: pd.DataFrame,
        psp_id_column: str = 'transaction_id',
        crm_id_column: str = 'psp_id',
        psp_amount_column: str = 'amount_usd',
        crm_amount_column: str = 'expected_amount_usd'
    ) -> MatchResult:
        """
        Match PSP transactions against CRM records.

        Matching logic:
        1. Match on transaction ID (PSP transaction_id = CRM psp_id)
        2. Validate amount within tolerance (default 95%)

        Args:
            psp_transactions: Normalized PSP transactions DataFrame
            crm_records: Normalized CRM records DataFrame
            psp_id_column: Column name for transaction ID in PSP data
            crm_id_column: Column name for PSP ID in CRM data
            psp_amount_column: Column name for amount in PSP data
            crm_amount_column: Column name for amount in CRM data

        Returns:
            MatchResult containing categorized transactions
        """
        logger.info(f"Matching {len(psp_transactions)} PSP transactions against {len(crm_records)} CRM records")

        # Initialize result containers
        matched_rows = []
        mismatch_rows = []
        psp_only_rows = []

        # Track which CRM records have been matched
        matched_crm_ids = set()

        # Process each PSP transaction
        for _, psp_row in psp_transactions.iterrows():
            psp_id = psp_row.get(psp_id_column)
            psp_amount = psp_row.get(psp_amount_column, 0) or 0

            # Find matching CRM record
            crm_match = crm_records[crm_records[crm_id_column] == psp_id]

            if len(crm_match) == 0:
                # No CRM record found - PSP_ONLY
                row_data = psp_row.to_dict()
                row_data['match_status'] = MatchStatus.PSP_ONLY.value
                row_data['crm_amount'] = None
                row_data['amount_difference'] = psp_amount
                row_data['match_percentage'] = 0
                psp_only_rows.append(row_data)

            else:
                # Found CRM record - check amount
                crm_row = crm_match.iloc[0]
                crm_amount = crm_row.get(crm_amount_column, 0) or 0
                crm_id_value = crm_row.get(crm_id_column)

                match_pct = self.calculate_match_percentage(psp_amount, crm_amount)
                difference = abs(psp_amount - crm_amount)

                row_data = psp_row.to_dict()
                row_data['crm_amount'] = crm_amount
                row_data['amount_difference'] = difference
                row_data['match_percentage'] = round(match_pct * 100, 2)

                if match_pct >= self.amount_tolerance:
                    # Good match
                    row_data['match_status'] = MatchStatus.MATCHED.value
                    matched_rows.append(row_data)
                else:
                    # Amount mismatch
                    row_data['match_status'] = MatchStatus.AMOUNT_MISMATCH.value
                    mismatch_rows.append(row_data)

                matched_crm_ids.add(crm_id_value)

        # Find CRM records not matched (CRM_ONLY)
        crm_only_rows = []
        for _, crm_row in crm_records.iterrows():
            crm_id = crm_row.get(crm_id_column)
            if crm_id not in matched_crm_ids:
                row_data = crm_row.to_dict()
                row_data['match_status'] = MatchStatus.CRM_ONLY.value
                row_data['psp_amount'] = None
                row_data['amount_difference'] = crm_row.get(crm_amount_column, 0)
                crm_only_rows.append(row_data)

        # Create DataFrames
        matched_df = pd.DataFrame(matched_rows) if matched_rows else pd.DataFrame()
        mismatch_df = pd.DataFrame(mismatch_rows) if mismatch_rows else pd.DataFrame()
        psp_only_df = pd.DataFrame(psp_only_rows) if psp_only_rows else pd.DataFrame()
        crm_only_df = pd.DataFrame(crm_only_rows) if crm_only_rows else pd.DataFrame()

        # Calculate summary
        summary = self._calculate_summary(
            matched_df, mismatch_df, psp_only_df, crm_only_df,
            psp_amount_column, crm_amount_column
        )

        logger.info(f"Matching complete: {summary['matched_count']} matched, "
                   f"{summary['mismatch_count']} mismatches, "
                   f"{summary['psp_only_count']} PSP-only, "
                   f"{summary['crm_only_count']} CRM-only")

        return MatchResult(
            matched=matched_df,
            amount_mismatch=mismatch_df,
            psp_only=psp_only_df,
            crm_only=crm_only_df,
            summary=summary
        )

    def _calculate_summary(
        self,
        matched: pd.DataFrame,
        mismatch: pd.DataFrame,
        psp_only: pd.DataFrame,
        crm_only: pd.DataFrame,
        psp_amount_col: str,
        crm_amount_col: str
    ) -> dict:
        """Calculate summary statistics for the match result."""

        def safe_sum(df: pd.DataFrame, col: str) -> float:
            if df.empty or col not in df.columns:
                return 0.0
            return df[col].fillna(0).sum()

        return {
            'matched_count': len(matched),
            'matched_amount': safe_sum(matched, psp_amount_col),
            'mismatch_count': len(mismatch),
            'mismatch_amount': safe_sum(mismatch, psp_amount_col),
            'psp_only_count': len(psp_only),
            'psp_only_amount': safe_sum(psp_only, psp_amount_col),
            'crm_only_count': len(crm_only),
            'crm_only_amount': safe_sum(crm_only, crm_amount_col),
            'total_psp_transactions': len(matched) + len(mismatch) + len(psp_only),
            'total_crm_records': len(matched) + len(mismatch) + len(crm_only),
            'match_rate': (
                len(matched) / (len(matched) + len(mismatch) + len(psp_only))
                if (len(matched) + len(mismatch) + len(psp_only)) > 0
                else 0
            ) * 100
        }
