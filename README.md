# Capital One → TaxHacker Pipeline

Convert Capital One bank statements (PDF) to TaxHacker-compatible CSV for automated expense tracking.

## Features

- **PDF to CSV conversion** — Extracts transactions from Capital One PDF statements
- **Multi-page support** — Processes all pages, deduplicates transactions
- **Auto-categorization** — Detects categories (food, transport, shopping, etc.)
- **Auto-project assignment** — Routes transactions to correct projects (customizable)
- **Multi-month batch** — Processes multiple statements at once
- **TaxHacker-compatible** — CSV format matches TaxHacker's import schema exactly

## Quick Start

```bash
# Single statement
python3 scripts/capital_one_to_taxhacker.py statement.pdf output.csv

# Multiple statements (batch)
python3 scripts/capital_one_to_taxhacker.py ~/Downloads/capital_one_statements/ output.csv

# Import to TaxHacker
# 1. Go to http://your-taxhacker-server:3000/import/csv
# 2. Upload the output.csv
# 3. Click "Import N transactions"
```

## Workflow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│ Capital One │ ──▶ │ Download PDF │ ──▶ │ Python Script│ ──▶ │  TaxHacker  │
│  (Safari)   │     │   (Manual)   │     │  (Extract)   │     │  (Import)   │
└─────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
```

## Automation (2:00 AM daily)

This project includes a `launchd` configuration for automated processing during off-peak hours.

```bash
# Load the launchd job
launchctl load ~/TaxHacker-docs/plist/com.taxhacker.statement-downloader.plist

# Manual trigger
launchctl start com.taxhacker.statement-downloader
```

## Project Structure

```
TaxHacker-docs/
├── README.md
├── scripts/
│   └── capital_one_to_taxhacker.py
├── plist/
│   └── com.taxhacker.statement-downloader.plist
├── docs/
│   ├── WORKFLOW.md
│   ├── TROUBLESHOOTING.md
│   └── LESSONS_LEARNED.md
└── examples/
    └── sample_output.csv
```

## TaxHacker Bugs Fixed

1. **currencyCode field** — TaxHacker's `calcTotalPerCurrency` requires `currencyCode` to be set. Without it, dashboard shows $0.00.
2. **Year extraction** — Zip codes (90210-1234) were being parsed as years. Fixed by extracting from statement period text first.

## Requirements

- Python 3.9+
- pdfplumber
- Safari with Capital One session (for downloading statements)

## Author

VF-AdminOver
