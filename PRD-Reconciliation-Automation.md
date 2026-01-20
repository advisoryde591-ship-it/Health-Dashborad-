# Product Requirements Document (PRD)
# Automated Reconciliation System

**Version:** 1.0
**Date:** January 2026
**Status:** Draft

---

## 1. Executive Summary

### Problem Statement
The reconciliation team (1 person) manually downloads files from 50 banks/PSPs daily, reformats them into a standardized Excel sheet, and matches ~150 transactions against CRM records. The most time-consuming part is **matching transactions** to identify discrepancies.

### Solution
Build an automated reconciliation system that:
1. Reads files from a local folder (PSP/bank exports + CRM report)
2. Normalizes all formats into a standard structure
3. Converts amounts to USD using daily exchange rates
4. Automatically matches transactions and flags discrepancies
5. Generates a reconciliation report

### Success Metrics
- Reduce manual matching time by 80%+
- Zero missed discrepancies
- Single consolidated report instead of manual Excel work

---

## 2. Scope

### Phase 1 (MVP) - Current Scope
| In Scope | Out of Scope (Phase 2) |
|----------|------------------------|
| Read files from local folder | API connections to PSPs/banks |
| Parse CSV, Excel, PDF formats | Direct CRM database connection |
| Normalize to standard format | Automated file downloads |
| Currency conversion (USD) | Email/Slack notifications |
| Transaction matching | User authentication |
| Discrepancy report generation | Historical trend analysis |

---

## 3. User Stories

### Primary User: Reconciliation Team Member

1. **As a** reconciliation team member, **I want to** drop all downloaded PSP/bank files into a folder **so that** the system processes them automatically.

2. **As a** reconciliation team member, **I want to** see a clear report of matched vs unmatched transactions **so that** I can focus only on investigating problems.

3. **As a** reconciliation team member, **I want** amounts converted to USD automatically **so that** I don't have to do manual currency conversion.

4. **As a** reconciliation team member, **I want to** know which transactions have amount mismatches **so that** I can investigate fee discrepancies or errors.

---

## 4. Functional Requirements

### 4.1 File Input

#### Supported Sources
- **PSP/Bank files:** CSV, Excel (.xlsx, .xls), PDF (structured bank statements)
- **CRM report:** CSV or Excel export

#### Folder Structure
```
/reconciliation/
├── /input/
│   ├── /psp_files/           # Drop PSP/bank files here
│   │   ├── stripe_2026-01-20.csv
│   │   ├── paypal_2026-01-20.xlsx
│   │   └── bank_statement.pdf
│   └── /crm_report/          # Drop CRM export here
│       └── crm_export_2026-01-20.csv
├── /output/
│   └── reconciliation_report_2026-01-20.xlsx
└── /config/
    ├── psp_mappings.json     # Column mappings per PSP
    └── exchange_rates.json   # Daily exchange rates
```

### 4.2 File Parsing & Normalization

#### Standard Output Format (per transaction)
| Field | Description | Source |
|-------|-------------|--------|
| `psp_name` | Name of PSP/bank | Derived from filename or config |
| `date` | Transaction date | Mapped from source |
| `transaction_id` | Unique PSP transaction ID | Mapped from source |
| `amount_original` | Original amount | Mapped from source |
| `currency_original` | Original currency | Mapped from source |
| `amount_usd` | Converted to USD | Calculated |
| `name` | Customer/counterparty name | Mapped from source |
| `type` | Transaction type | Mapped from source |
| `status` | Transaction status | Mapped from source |

#### PSP Column Mapping (Configurable)
Each PSP has different column names. System uses a mapping config:

```json
{
  "stripe": {
    "date": "created_at",
    "transaction_id": "payment_id",
    "amount": "amount",
    "currency": "currency",
    "name": "customer_name",
    "type": "type",
    "status": "status"
  },
  "paypal": {
    "date": "Date",
    "transaction_id": "Transaction ID",
    "amount": "Gross",
    "currency": "Currency",
    "name": "Name",
    "type": "Type",
    "status": "Status"
  }
}
```

### 4.3 Currency Conversion

- Convert all amounts to USD
- Use daily exchange rates (configurable JSON file or API)
- Store both original and converted amounts

```json
// exchange_rates.json
{
  "date": "2026-01-20",
  "rates": {
    "EUR": 1.08,
    "GBP": 1.27,
    "ILS": 0.27
  }
}
```

### 4.4 Transaction Matching

#### Matching Logic
1. **Primary Key:** PSP `transaction_id` matches CRM `psp_id`
2. **Amount Validation:** Amounts must match within **95%** tolerance (accounts for fees, FX differences)

#### Match Categories

| Category | Condition | Action Required |
|----------|-----------|-----------------|
| **MATCHED** | ID matches + Amount within 95% | None |
| **AMOUNT_MISMATCH** | ID matches + Amount differs >5% | Investigate |
| **PSP_ONLY** | Transaction in PSP, not in CRM | Investigate - unexpected payment |
| **CRM_ONLY** | Transaction in CRM, not in PSP | Investigate - missing payment |

#### Matching Algorithm
```
For each PSP transaction:
  1. Look for CRM record where crm.psp_id == psp.transaction_id
  2. If found:
     - Calculate: match_percentage = min(psp_amount, crm_amount) / max(psp_amount, crm_amount)
     - If match_percentage >= 0.95: Status = MATCHED
     - Else: Status = AMOUNT_MISMATCH
  3. If not found:
     - Status = PSP_ONLY

For each CRM transaction not yet matched:
  - Status = CRM_ONLY
```

### 4.5 Output Report

#### Excel Report Structure

**Tab 1: Summary**
| Metric | Count | Amount (USD) |
|--------|-------|--------------|
| Total PSP Transactions | 150 | $45,000 |
| Total CRM Expected | 148 | $44,500 |
| Matched | 140 | $42,000 |
| Amount Mismatch | 3 | $1,500 |
| PSP Only (Unexpected) | 7 | $1,500 |
| CRM Only (Missing) | 5 | $1,000 |

**Tab 2: Matched Transactions**
All successfully reconciled transactions.

**Tab 3: Discrepancies (PRIORITY)**
| PSP | Date | Txn ID | PSP Amount | CRM Amount | Difference | Status | Notes |
|-----|------|--------|------------|------------|------------|--------|-------|
| Stripe | 2026-01-20 | txn_123 | $100 | $92 | $8 (8%) | AMOUNT_MISMATCH | |
| PayPal | 2026-01-20 | PP_456 | $250 | - | $250 | PSP_ONLY | |
| - | 2026-01-20 | - | - | $180 | $180 | CRM_ONLY | psp_id: xyz_789 |

**Tab 4: All PSP Transactions**
Complete normalized list from all PSP/bank files.

**Tab 5: All CRM Transactions**
Complete list from CRM export.

---

## 5. Technical Architecture

### 5.1 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     RECONCILIATION SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  FILE        │    │  PARSER      │    │  NORMALIZER  │       │
│  │  WATCHER     │───▶│  (CSV/XLS/   │───▶│  (Standard   │       │
│  │              │    │   PDF)       │    │   Format)    │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                 │                │
│                                                 ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  REPORT      │◀───│  MATCHER     │◀───│  CURRENCY    │       │
│  │  GENERATOR   │    │  ENGINE      │    │  CONVERTER   │       │
│  │  (Excel)     │    │              │    │              │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │  OUTPUT      │                                               │
│  │  FOLDER      │                                               │
│  └──────────────┘                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Technology Stack (Recommended)

| Component | Technology | Reason |
|-----------|------------|--------|
| Language | Python 3.11+ | Best for data processing, file parsing |
| CSV/Excel Parsing | pandas, openpyxl | Industry standard |
| PDF Parsing | pdfplumber or camelot | Good for tabular PDFs |
| Excel Output | openpyxl or xlsxwriter | Native Excel generation |
| Config | JSON files | Simple, editable |
| UI (Optional) | Streamlit or simple CLI | Quick to build |

### 5.3 Module Breakdown

```
/reconciliation_system/
├── main.py                    # Entry point
├── /parsers/
│   ├── csv_parser.py
│   ├── excel_parser.py
│   └── pdf_parser.py
├── /processors/
│   ├── normalizer.py          # Apply column mappings
│   ├── currency_converter.py  # FX conversion
│   └── matcher.py             # Matching engine
├── /reporters/
│   └── excel_reporter.py      # Generate output
├── /config/
│   ├── psp_mappings.json
│   └── exchange_rates.json
└── /tests/
    └── test_matcher.py
```

---

## 6. Configuration Requirements

### 6.1 PSP Mapping File
For each of the 50 PSPs, define:
- Column name mappings
- Date format
- Amount format (decimal places, thousands separator)
- File type expected

### 6.2 Exchange Rates
- Manual: JSON file updated daily
- Future: API integration (e.g., Open Exchange Rates, Fixer.io)

---

## 7. User Interface

### Phase 1: Command Line Interface (CLI)
```bash
# Run reconciliation for today
python main.py --date 2026-01-20

# Run with custom input folder
python main.py --input /path/to/files --date 2026-01-20
```

### Phase 1 Alternative: Simple Web UI (Streamlit)
- Upload files via browser
- Click "Run Reconciliation"
- Download report

---

## 8. Edge Cases & Error Handling

| Scenario | Handling |
|----------|----------|
| Unknown PSP file format | Log warning, skip file, continue |
| Missing column in file | Log error with filename, skip file |
| Invalid date format | Attempt multiple formats, log if unparseable |
| PDF parsing failure | Log error, suggest manual review |
| Duplicate transaction IDs | Flag in report, include both |
| Missing exchange rate | Use most recent available, flag in report |

---

## 9. Future Enhancements (Phase 2+)

| Feature | Description | Priority |
|---------|-------------|----------|
| API Integrations | Connect directly to Stripe, PayPal, etc. | High |
| CRM Database Connection | Query CRM directly instead of file export | High |
| Scheduled Runs | Auto-run daily at specified time | Medium |
| Email Reports | Send summary via email | Medium |
| Historical Dashboard | Track discrepancy trends over time | Low |
| Multi-user Support | Login, permissions, audit trail | Low |

---

## 10. Implementation Plan

### Week 1: Foundation
- [ ] Set up project structure
- [ ] Build CSV parser with normalization
- [ ] Build Excel parser with normalization
- [ ] Create PSP mapping config for 5 pilot PSPs

### Week 2: Core Logic
- [ ] Build currency converter
- [ ] Build matching engine
- [ ] Build Excel report generator
- [ ] Test with sample data

### Week 3: PDF & Polish
- [ ] Add PDF parser for bank statements
- [ ] Add remaining PSP mappings
- [ ] Error handling & logging
- [ ] User documentation

### Week 4: Testing & Deployment
- [ ] Test with real production files
- [ ] Refine matching logic based on feedback
- [ ] Deploy to team
- [ ] Training

---

## 11. Acceptance Criteria

### MVP is complete when:
1. ✅ System reads CSV, Excel, PDF files from input folder
2. ✅ System normalizes data using configurable PSP mappings
3. ✅ System converts all amounts to USD
4. ✅ System matches PSP transactions to CRM records
5. ✅ System generates Excel report with:
   - Summary tab
   - Matched transactions
   - Discrepancies (AMOUNT_MISMATCH, PSP_ONLY, CRM_ONLY)
6. ✅ At least 10 PSP mappings configured
7. ✅ Process completes in under 5 minutes for 150 transactions

---

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| PDF parsing unreliable | Some bank statements can't be parsed | Provide manual entry option, prioritize CSV/Excel sources |
| PSP changes file format | Parser breaks | Version mappings, alert on parse failures |
| Exchange rate not updated | Incorrect USD amounts | Default to previous day, warn in report |
| Large file volumes | Slow processing | Batch processing, progress indicator |

---

## 13. Open Questions

1. **CRM Export Format:** What columns are in the CRM export? Need sample file.
2. **PDF Samples:** Need sample bank statement PDFs to test parsing.
3. **PSP File Samples:** Need sample files from top 10 PSPs to build initial mappings.
4. **Amount Tolerance:** Is 95% the right threshold? Should it be configurable?
5. **Historical Data:** Do we need to reprocess historical reconciliations?

---

## 14. Appendix

### A. Sample PSP Mapping Configuration
```json
{
  "psp_name": "stripe",
  "file_pattern": "stripe*.csv",
  "date_format": "%Y-%m-%d",
  "column_mapping": {
    "date": "created",
    "transaction_id": "id",
    "amount": "amount",
    "currency": "currency",
    "name": "customer_email",
    "type": "type",
    "status": "status"
  },
  "amount_divisor": 100,
  "notes": "Stripe amounts are in cents"
}
```

### B. Sample CRM Export Expected Format
```csv
psp_id,expected_date,expected_amount_usd,customer_name,status
txn_abc123,2026-01-20,100.00,John Doe,pending
txn_def456,2026-01-20,250.50,Jane Smith,pending
```

---

**Document Owner:** Reconciliation Team
**Last Updated:** January 2026
**Next Review:** After Phase 1 completion
