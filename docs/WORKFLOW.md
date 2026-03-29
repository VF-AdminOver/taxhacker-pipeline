# Capital One Statement Download & Import Workflow

## Step-by-Step Process

### 1. Download Statements from Capital One (Safari)

1. Open Safari → Navigate to https://myaccounts.capitalone.com/
2. Log in (already authenticated if you have an active session)
3. Click on a bank account to view details
4. Click **"Statements"** tab in the account page
5. This opens a **Document Center** page with all statements listed

**Important:** The "View my statement" button (not the statement link) opens a preview dialog with a Download button.

6. For each statement:
   - Click **"View my statement"** button (not the statement link)
   - A preview dialog opens with the PDF rendered
   - Click **"Download"** button
   - The PDF downloads to `~/Downloads/`
   - Close the dialog with **"Close Dialog"** button
   - Click the next statement's **"View my statement"** button

### 2. Organize Downloaded PDFs

```bash
# Create a dedicated folder
mkdir -p ~/Downloads/capital_one_statements

# Move all bank statement PDFs
mv ~/Downloads/*Bank*statement*.pdf ~/Downloads/capital_one_statements/
```

### 3. Convert to TaxHacker CSV

```bash
# Convert all statements to TaxHacker CSV
python3 ~/.openclaw/workspace/skills/pdf-processing/scripts/capital_one_to_taxhacker.py \
    ~/Downloads/capital_one_statements/ \
    ~/Downloads/capital_one_taxhacker.csv
```

**Output:** `capital_one_taxhacker.csv` with columns:
- `name` — Full transaction description
- `description` — Same as name
- `merchant` — Cleaned merchant name
- `total` — Amount (e.g., "26.40")
- `currencyCode` — "USD"
- `type` — "income" or "expense"
- `categoryCode` — Auto-detected category (transportation, food-and-drinks, etc.)
- `projectCode` — Auto-assigned project (personal, business, investments)
- `issuedAt` — Date in YYYY-MM-DD format
- `note` — Source PDF filename

### 4. Import to TaxHacker

1. Navigate to http://your-taxhacker-server:3000/import/csv
2. Click **"Import from CSV"**
3. Upload the generated CSV file
4. Review the column mappings (should auto-detect correctly)
5. Click **"Import N transactions"**
6. Verify totals on the Dashboard

## Project Auto-Assignment Rules

| Project | Description Keywords |
|---------|---------------------|
| **etsy-shop** | stripe, paypal, invoice |
| **investments** | dividend, brokerage |
| **personal** | Everything else (default) |

To customize, edit `PROJECT_RULES` in the script.

## Category Detection

Categories are auto-detected from description keywords:
- **income** — Direct deposits, transfers in
- **food-and-drinks** — Restaurants, grocery stores
- **shopping** — Amazon, Target, Walmart, Etsy
- **transportation** — Gas stations, ride-sharing
- **entertainment** — Streaming, theaters
- **utilities** — Phone, internet, electric
- **transfers** — Zelle, internal transfers
- **bills** — Loan payments, financing
- **other** — Everything else
