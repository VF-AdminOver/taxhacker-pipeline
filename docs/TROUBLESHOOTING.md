# Troubleshooting

## Common Issues

### Dashboard shows $0.00 despite imported transactions

**Cause:** Missing `currencyCode` field in CSV.

**Fix:** Ensure CSV includes `currencyCode` column with "USD" values. Run the latest version of `capital_one_to_taxhacker.py`.

### Transactions not counted in dashboard totals

**Cause:** Missing or empty `projectCode` field.

**Fix:** Ensure all transactions have a valid `projectCode`. The script now auto-assigns "personal" by default.

### Year shows as 2028 instead of 2026

**Cause:** Zip code (e.g., "XXXXX-XXXX") being parsed as year.

**Fix:** Run latest script with improved year extraction logic.

### PDF extraction returns 0 transactions

**Cause:** Wrong PDF format. The script is designed for Capital One's specific format, not generic PDFs.

**Format expected:**
```
Feb 1 Digital Card Purchase - LYFT RIDE... Debit - $26.40 $8.34
Feb 3 Deposit from 360 Checking... Credit + $4.00 $1.75
```

### Safari download doesn't work

**Cause:** Not clicking the correct button.

**Solution:**
1. Navigate to statements page
2. Click **"View my statement"** button (not the statement link)
3. Wait for preview dialog to open
4. Click **"Download"** button in the dialog
5. Close dialog

### CSV import shows wrong columns

**Cause:** TaxHacker auto-detects columns by name. Column names must match exactly.

**Expected columns:** `name`, `description`, `merchant`, `total`, `currencyCode`, `type`, `categoryCode`, `projectCode`, `issuedAt`, `note`

### Duplicate transactions in import

**Cause:** Same statement processed multiple times.

**Fix:** The script includes deduplication logic. Check if you're importing the same CSV multiple times.

## Debugging

### Check PDF content
```python
import pdfplumber
with pdfplumber.open('statement.pdf') as pdf:
    for page in pdf.pages:
        print(page.extract_text())
```

### Check CSV format
```bash
head -5 output.csv
awk -F, 'NR>1 {print $7, $8}' output.csv | sort | uniq -c
```

### Check TaxHacker database
```sql
-- Check transaction counts
SELECT COUNT(*), type FROM transactions GROUP BY type;

-- Check project distribution
SELECT projectCode, COUNT(*) FROM transactions GROUP BY projectCode;

-- Check currency codes
SELECT DISTINCT currency_code FROM transactions;
```

## Getting Help

- TaxHacker issues: https://github.com/vas3k/TaxHacker/issues
- Capital One support: 1-888-464-0727
