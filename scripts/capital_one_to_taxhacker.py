#!/usr/bin/env python3
"""
Capital One Bank Statement PDF → TaxHacker CSV converter.
Handles real Capital One statement format.
"""

import sys
import csv
import pdfplumber
import re
from datetime import datetime
from pathlib import Path

TAXHACKER_HEADERS = ['name', 'description', 'merchant', 'total', 'currencyCode', 'type', 'categoryCode', 'projectCode', 'issuedAt', 'note']
DEFAULT_PROJECT = 'personal'
DEFAULT_CURRENCY = 'USD'

# Project auto-assignment rules based on description patterns
# Customize these keywords to match YOUR projects and transactions
PROJECT_RULES = {
    'business': ['stripe', 'paypal', 'invoice', 'client'],   # Business income
    'investments': ['dividend', 'brokerage', 'stock'],        # Investment activity
    # Everything else → personal (default)
}

def detect_project(description: str, category: str) -> str:
    """Auto-assign project based on description and category."""
    desc_lower = description.lower()
    for project, patterns in PROJECT_RULES.items():
        if any(pattern in desc_lower for pattern in patterns):
            return project
    return DEFAULT_PROJECT

# Category detection patterns
CATEGORY_PATTERNS = {
    'income': ['direct deposit', 'deposit from', 'transfer from', 'interest', 'payment received'],
    'food-and-drinks': ['grocery', 'restaurant', 'cafe', 'coffee', 'food', 'dining', 'pizza', 'takeout'],
    'shopping': ['amazon', 'target', 'walmart', 'costco', 'best buy', 'online', 'store', 'shop'],
    'transportation': ['gas station', 'fuel', 'ride', 'taxi', 'parking', 'toll', 'transit'],
    'entertainment': ['streaming', 'theater', 'cinema', 'gaming', 'music', 'movie'],
    'utilities': ['phone', 'internet', 'electric', 'water', 'gas bill', 'cable'],
    'health': ['pharmacy', 'doctor', 'medical', 'dental', 'vision', 'hospital'],
    'subscriptions': ['subscription', 'monthly', 'annual', 'membership'],
    'transfers': ['transfer', 'withdrawal', 'deposit from', 'zelle', 'venmo'],
    'bills': ['payment to', 'financing', 'loan', 'mortgage', 'rent'],
}

def detect_category(description: str) -> str:
    """Auto-detect category from transaction description."""
    desc_lower = description.lower()
    for category, patterns in CATEGORY_PATTERNS.items():
        if any(pattern in desc_lower for pattern in patterns):
            return category
    return 'other'

def clean_merchant(description: str) -> str:
    """Extract merchant name from description."""
    desc = description.strip()
    # Remove common prefixes
    for prefix in ['Digital Card Purchase - ', 'Debit Card Purchase - ', 'Credit Card Purchase - ',
                   'Direct Deposit - ', 'Deposit from ', 'Withdrawal to ', 'Transfer to ', 'Transfer from ',
                   'Zelle money sent to ', 'Electronic Payment to ', 'Savings GOAL - ']:
        if desc.startswith(prefix):
            desc = desc[len(prefix):]
    # Remove trailing numbers and location codes
    desc = re.sub(r'\s+\d{7,}.*$', '', desc)  # Remove phone/reference numbers
    desc = re.sub(r'\s+[A-Z]{2}\s*\d{5}.*$', '', desc)  # Remove city/state/zip
    desc = re.sub(r'\s+[A-Z]{2}\s*$', '', desc)  # Remove state abbreviation
    return desc.strip()[:50]

def normalize_date(date_str: str, statement_year: int = None) -> str:
    """Convert 'Feb 1' to YYYY-MM-DD."""
    months = {'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
              'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'}
    
    # Match patterns like "Feb 1", "Feb 1", "02/01", "02/01/2026"
    match = re.match(r'(\w+)\s+(\d{1,2})', date_str)
    if match:
        month_name = match.group(1).lower()[:3]
        day = match.group(2)
        month = months.get(month_name, '01')
        year = statement_year or datetime.now().year
        return f"{year}-{month}-{day.zfill(2)}"
    
    match = re.match(r'(\d{1,2})/(\d{1,2})(?:/(\d{4}))?', date_str)
    if match:
        month = match.group(1).zfill(2)
        day = match.group(2).zfill(2)
        year = int(match.group(3)) if match.group(3) else statement_year or datetime.now().year
        return f"{year}-{month}-{day}"
    
    return date_str

def parse_amount(amount_str: str) -> tuple:
    """Parse amount string and determine type.
    Handles: 'Debit - $26.40', 'Credit + $21.00', 'Debit - $26.40', '+$100.00', '-$50.00'
    """
    amount_str = amount_str.strip()
    
    # Determine type from Debit/Credit prefix
    is_debit = 'debit' in amount_str.lower()
    is_credit = 'credit' in amount_str.lower()
    
    if is_credit:
        txn_type = 'income'
    elif is_debit:
        txn_type = 'expense'
    else:
        # Fall back to +/- sign
        if '+' in amount_str:
            txn_type = 'income'
        elif '-' in amount_str:
            txn_type = 'expense'
        else:
            txn_type = 'expense'
    
    # Extract numeric value
    amount_str = re.sub(r'[^\d.]', '', amount_str)
    
    try:
        amount = float(amount_str)
    except ValueError:
        amount = 0.0
    
    return amount, txn_type

def extract_statement_year(text: str) -> int:
    """Extract the year from the statement period text, not from zip codes."""
    # First try: find year from statement period text (e.g., "Feb 1 - Feb 28, 2026")
    # Look for "STATEMENT PERIOD" or month names followed by year
    period_match = re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d+\s*(?:-|to)\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d+,\s*(\d{4})', text)
    if period_match and period_match.group(1):
        return int(period_match.group(1))
    
    # Fallback: find year in "Your February 2026 bank statement" or similar
    stmt_match = re.search(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', text)
    if stmt_match:
        return int(stmt_match.group(1))
    
    # Last resort: find first 4-digit year (avoid zip codes)
    year_match = re.search(r'(?:^|\s)(202[0-9])\s', text)
    if year_match:
        return int(year_match.group(1))
    
    return 2026  # Default

def extract_transactions_from_pdf(pdf_path: str) -> list:
    """Extract all transactions from a Capital One PDF statement."""
    transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        # Extract statement year
        statement_year = extract_statement_year(full_text)
        
        # Split into lines and parse
        lines = full_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match Capital One real format: "Feb 1 Digital Card Purchase - LYFT RIDE..."
            # Pattern: Month Day DESCRIPTION Debit/Credit +/- $AMOUNT BALANCE
            match = re.match(r'^(\w+\s+\d{1,2})\s+(.*?)\s+(Debit|Credit)\s*([\+\-]?\s*\$[\d,]+\.\d{2})(?:\s+\$[\d,]+\.\d{2})?$', line)
            if not match:
                # Try alternate format: "Feb 1 Opening Balance $34.74"
                alt_match = re.match(r'^(\w+\s+\d{1,2})\s+(Opening Balance|Closing Balance)\s+\$([\d,]+\.\d{2})', line)
                if alt_match:
                    continue  # Skip opening/closing balance lines
                continue
            
            date_str = match.group(1)
            description = match.group(2).strip()
            debit_credit = match.group(3)
            amount_str = match.group(4)
            
            # Parse amount
            amount, txn_type = parse_amount(f"{debit_credit} {amount_str}")
            
            if amount == 0:
                continue
            
            # Clean description
            description = re.sub(r'\s+', ' ', description)
            
            # Build transaction
            merchant = clean_merchant(description)
            category = detect_category(description)
            project = detect_project(description, category)
            date = normalize_date(date_str, statement_year)
            
            transaction = {
                'name': description[:100],
                'description': description,
                'merchant': merchant,
                'total': f"{amount:.2f}",
                'currencyCode': DEFAULT_CURRENCY,
                'type': txn_type,
                'categoryCode': category,
                'projectCode': project,
                'issuedAt': date,
                'note': f"Source: {Path(pdf_path).name}",
            }
            transactions.append(transaction)
    
    return transactions

def write_taxhacker_csv(transactions: list, output_path: str) -> int:
    """Write transactions to TaxHacker-compatible CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=TAXHACKER_HEADERS)
        writer.writeheader()
        writer.writerows(transactions)
    return len(transactions)

def process_batch(pdf_folder: str, output_csv: str) -> int:
    """Process all PDFs in a folder and combine into one CSV."""
    all_transactions = []
    pdf_files = sorted(Path(pdf_folder).glob("*.pdf"))
    
    print(f"Found {len(pdf_files)} PDF files")
    for pdf_path in pdf_files:
        print(f"  Processing: {pdf_path.name}")
        transactions = extract_transactions_from_pdf(str(pdf_path))
        print(f"    Found {len(transactions)} transactions")
        all_transactions.extend(transactions)
    
    # Deduplicate
    seen = set()
    unique_transactions = []
    for t in all_transactions:
        key = (t['issuedAt'], t['total'], t['name'])
        if key not in seen:
            seen.add(key)
            unique_transactions.append(t)
    
    duplicates_removed = len(all_transactions) - len(unique_transactions)
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed} duplicate transactions")
    
    return write_taxhacker_csv(unique_transactions, output_csv)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Capital One → TaxHacker CSV')
    parser.add_argument('input', help='PDF file or folder')
    parser.add_argument('output', nargs='?', default='taxhacker_import.csv', help='Output CSV')
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if input_path.is_dir():
        count = process_batch(args.input, args.output)
    elif input_path.suffix.lower() == '.pdf':
        transactions = extract_transactions_from_pdf(args.input)
        count = write_taxhacker_csv(transactions, args.output)
    else:
        print("Input must be a PDF file or folder")
        sys.exit(1)
    
    print(f"\n✅ Extracted {count} transactions to {args.output}")
    print(f"📁 Import at: http://localhost:7331/import/csv")
