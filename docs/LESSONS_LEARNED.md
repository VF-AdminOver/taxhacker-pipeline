# Lessons Learned

## Key Takeaways from Building the Capital One → TaxHacker Pipeline

### 1. Always Verify Search Results

**Problem:** I initially said Capital One offers CSV download based on third-party search snippets. Capital One actually only offers BAI, Quicken (.qfx), and QuickBooks (.qbo) export formats.

**Lesson:** Search results often come from third-party tools, not the actual service. Always verify on the official website.

### 2. Safari Automation Has Limits

**Problem:** The Capital One website uses complex JavaScript navigation that breaks automation. Clicking statement links navigates away instead of opening a preview.

**What worked:**
- **"View my statement"** button opens a preview dialog with Download button
- After download, close dialog (not page navigation)

**What didn't work:**
- Clicking statement links directly (triggers page navigation)
- JavaScript batch downloading (dialog state management is fragile)

**Lesson:** For complex SPAs, inspect the DOM structure before writing automation. The "View my statement" button is the correct target, not the statement links.

### 3. Capital One Downloads Duplicates

**Problem:** Each statement downloaded twice (e.g., `-5.pdf` and `-6.pdf`).

**Cause:** The download button triggered a double-click or the dialog re-opened.

**Fix:** Wait 3+ seconds between Download and Close Dialog. Check `~/Downloads/` for duplicates.

### 4. TaxHacker Requires `currencyCode`

**Bug:** Dashboard showed $0.00 for all totals despite 11 imported transactions.

**Root Cause:** TaxHacker's `calcTotalPerCurrency` function skips transactions without `currencyCode`.

**Fix:** Added `currencyCode: "USD"` to CSV output.

### 5. Year Extraction Bug from Zip Codes

**Bug:** Transactions dated "2028" instead of "2026".

**Root Cause:** Address line "XXXXX-XXXX" contained a 4-digit number that matched the year regex.

**Fix:** Extract year from statement period text ("Feb 1 - Feb 28, 2026") first, then fall back to other patterns.

### 6. TaxHacker Stores Amounts in Cents

**Note:** TaxHacker stores amounts as integers in cents. The import function multiplies by 100. So providing "26.40" becomes 2640 cents internally.

**Implication:** When debugging, remember that 2640 in the database = $26.40 on screen.

### 7. Safari MCP Tool Behavior

**Findings:**
- `safari_snapshot` gives accessibility tree (preferred for finding refs)
- `safari_click` can use refs from previous snapshot (refs expire after navigation)
- `safari_wait` is important after navigation to avoid stale refs
- `safari_network` captures resource loads, not JavaScript-triggered downloads
- `safari_start_network_capture` is needed before clicking to capture requests

**Lesson:** Always take a fresh snapshot after any navigation or dialog change. Refs are only valid for the immediate snapshot.

### 8. Selenium vs Safari MCP

**Comparison:**
- **Selenium:** Requires Chrome install, credential management, 2FA handling
- **Safari MCP:** Uses existing login session, simpler setup

**Decision:** Safari MCP is better for personal use where you're already logged in. Selenium is better for headless automation on servers.

### 9. TaxHacker CSV Import vs Unsorted Upload

**Finding:** CSV files uploaded via JavaScript DataTransfer are treated as "unsorted files" (like receipts), not as CSV imports. They require AI analysis to extract transactions.

**Correct flow:** Use the dedicated `#csv-file` input field on the Import page, or upload via the "Upload New File" button on the Import page.

### 10. Project Assignment Matters for Dashboard

**Bug:** Dashboard showed 11 transactions but only counted 1 in totals.

**Root Cause:** Transactions without `projectCode` weren't counted in dashboard calculations.

**Fix:** Set `projectCode` to "personal" for all transactions.

---

## Summary

The biggest lesson: **always verify assumptions by testing on the actual service**. I made multiple incorrect claims about Capital One's capabilities that were disproven by actually navigating the website and trying the automation.
