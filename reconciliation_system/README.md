# Automated Reconciliation System

Automatically match PSP/bank transactions against CRM records and generate discrepancy reports.

## Quick Start

### 1. Install Dependencies
```bash
cd reconciliation_system
pip install -r requirements.txt
```

### 2. Add Your Files

**PSP/Bank files:** Drop into `input/psp_files/`
```
input/psp_files/
├── stripe_2026-01-20.csv
├── paypal_2026-01-20.xlsx
└── bank_statement.pdf
```

**CRM export:** Drop into `input/crm_report/`
```
input/crm_report/
└── crm_export_2026-01-20.csv
```

### 3. Run Reconciliation
```bash
python main.py --date 2026-01-20
```

### 4. Get Your Report
Output will be in `output/reconciliation_report_2026-01-20.xlsx`

---

## Configuration

### Adding a New PSP

Edit `config/psp_mappings.json`:

```json
{
  "my_new_psp": {
    "psp_name": "My New PSP",
    "file_pattern": "mynewpsp*.csv",
    "date_format": "%Y-%m-%d",
    "column_mapping": {
      "date": "transaction_date",
      "transaction_id": "txn_id",
      "amount": "amount",
      "currency": "currency",
      "name": "customer",
      "type": "type",
      "status": "status"
    },
    "amount_divisor": 1
  }
}
```

### Updating Exchange Rates

Edit `config/exchange_rates.json`:

```json
{
  "date": "2026-01-20",
  "rates": {
    "EUR": 1.08,
    "GBP": 1.27,
    "ILS": 0.27
  }
}
```

### CRM Column Mapping

If your CRM export has different column names, edit `config/crm_mapping.json`:

```json
{
  "column_mapping": {
    "psp_id": "your_psp_id_column",
    "expected_date": "your_date_column",
    "expected_amount_usd": "your_amount_column",
    "customer_name": "your_customer_column"
  }
}
```

---

## Output Report

The Excel report contains 5 tabs:

| Tab | Description |
|-----|-------------|
| **Summary** | Overview statistics and match rate |
| **Matched** | Successfully reconciled transactions |
| **Discrepancies** | All issues: amount mismatches, unexpected, missing |
| **All PSP Transactions** | Complete normalized PSP data |
| **All CRM Records** | Complete CRM export data |

### Discrepancy Types

| Type | Meaning | Action |
|------|---------|--------|
| `AMOUNT_MISMATCH` | IDs match but amounts differ >5% | Investigate fees/FX |
| `PSP_ONLY` | In PSP but not in CRM | Unexpected payment |
| `CRM_ONLY` | In CRM but not in PSP | Missing payment |

---

## Folder Structure

```
reconciliation_system/
├── main.py                 # Run this!
├── requirements.txt        # Dependencies
├── input/
│   ├── psp_files/          # <- Your PSP/bank files
│   └── crm_report/         # <- Your CRM export
├── output/                 # <- Reports generated here
├── config/
│   ├── psp_mappings.json   # PSP column configurations
│   ├── exchange_rates.json # Daily FX rates
│   └── crm_mapping.json    # CRM column mapping
├── parsers/
│   ├── csv_parser.py
│   ├── excel_parser.py
│   └── pdf_parser.py
├── processors/
│   ├── normalizer.py
│   ├── currency_converter.py
│   └── matcher.py
└── reporters/
    └── excel_reporter.py
```

---

## Troubleshooting

**"No PSP transactions found"**
- Check that files are in `input/psp_files/`
- Verify file names match patterns in `psp_mappings.json`

**"Unknown PSP format"**
- Add a new mapping in `config/psp_mappings.json`

**"No exchange rate found"**
- Add the currency to `config/exchange_rates.json`

**PDF parsing issues**
- Ensure `pdfplumber` is installed: `pip install pdfplumber`
- Some PDFs may not have parseable tables
