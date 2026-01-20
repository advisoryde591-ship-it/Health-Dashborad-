# Sample Files

These are example files showing the expected format for PSP and CRM data.

## To Test the System:

1. Copy sample PSP files to `input/psp_files/`:
   ```bash
   cp sample_psp_stripe.csv ../input/psp_files/stripe_2026-01-20.csv
   cp sample_psp_paypal.csv ../input/psp_files/paypal_2026-01-20.csv
   ```

2. Copy sample CRM file to `input/crm_report/`:
   ```bash
   cp sample_crm_export.csv ../input/crm_report/crm_export_2026-01-20.csv
   ```

3. Run reconciliation:
   ```bash
   cd ..
   python main.py --date 2026-01-20
   ```

## Expected Results with Sample Data:

- **Matched:** txn_001, txn_002, txn_005, PP_101, PP_102
- **Amount Mismatch:** txn_003 (EUR conversion), PP_103 (EUR conversion)
- **PSP Only:** txn_004, PP_104 (not in CRM)
- **CRM Only:** PP_105 (not in PSP files)

## Adding Your Real Files:

Replace these samples with your actual PSP exports and CRM data.
Update `config/psp_mappings.json` if your column names differ.
