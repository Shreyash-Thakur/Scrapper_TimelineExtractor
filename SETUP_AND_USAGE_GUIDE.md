# Complete Setup & Usage Guide — Unmatched Kicks Scraper

## Overview

This is a **2-stage iterative scraping system**:
1. **Stage 1**: Initial scrape with `python_scraper_unmatchedkicks.py` → `results.xlsx`
2. **Stage 2**: Validate & fix incomplete entries with `validate_and_rescrape_unmatchedkicks.py` → `results_fixed.xlsx`

---

## Installation

### Step 1: Install Python Dependencies

```bash
pip install requests beautifulsoup4 playwright openpyxl
```

### Step 2: Install Playwright Browser

```bash
playwright install chromium
```

### Step 3: Verify Installation

```bash
python -c "import requests, bs4, playwright, openpyxl; print('✅ All packages installed')"
```

---

## Stage 1: Initial Scraping

### Prepare URLs

Create `urls.txt` in your project folder with one URL per line:

```
https://unmatchedkicks.in/products/sp5der-sp555-tee-black
https://unmatchedkicks.in/products/sp5der-spinner-tee-white
https://unmatchedkicks.in/products/hellstar-breaking-news-t-shirt-white
# Comment lines are ignored
https://unmatchedkicks.in/products/fear-of-god-essentials-hoodie-plum
```

Or use bare product slugs:
```
sp5der-sp555-tee-black
hellstar-breaking-news-t-shirt-white
```

### Run Initial Scrape

**Recommended (Playwright — handles JavaScript):**
```bash
python python_scraper_unmatchedkicks.py --input urls.txt --output results.xlsx --playwright --delay 3
```

**Alternative (Requests — faster but less reliable):**
```bash
python python_scraper_unmatchedkicks.py --input urls.txt --output results.xlsx --workers 2 --delay 2.5
```

### Output

- **results.xlsx** — All products with shipping timeline (column B has clickable URLs in column A)
- **failed_urls.txt** — URLs that failed (will be empty if all succeeded)

---

## Stage 2: Validation & Re-scraping

### Identify Incomplete Entries

The validation script automatically detects:

❌ **Incomplete/Invalid entries:**
- Empty cells
- Size data: "XL", "S", "M", etc.
- Price data: "8999.00", "₹21999"
- "N/A" placeholders

✅ **Valid entries:**
- "Ships In 14 Days"
- "This product will be shipped within 3-5 working days"
- "Same day delivery"
- "Ships In 30 Days"

### Run Re-scraper

```bash
python validate_and_rescrape_unmatchedkicks.py --input results.xlsx --output results_fixed.xlsx --playwright --delay 2.5
```

This will:
1. Read `results.xlsx`
2. Identify incomplete entries
3. Re-scrape those URLs with **enhanced extraction**
4. Write corrected data to `results_fixed.xlsx`

---

## What the Scraper Extracts

The enhanced scraper looks for shipping info in this priority order:

### 1. **JSON-LD Structured Data** (Most reliable)
```json
{
  "@type": "Product",
  "aggregateOffer": {
    "offers": [{
      "shippingDetails": {
        "deliveryTime": {
          "businessDays": "14"
        }
      }
    }]
  }
}
```

### 2. **Button/Form Element**
```html
<button>SHIPS IN 14 DAYS</button>
```

### 3. **Legend + Span (Form Selector)**
```html
<legend class="form__label">
  <span data-selected-value>Ships In 14 Days</span>
</legend>
```

### 4. **Blue Highlighted Box (Common on UK Sites)**
```html
<div style="background: #E3F2FD; padding: 10px;">
  <p>This product will be shipped within 3-5 working days</p>
</div>
```

### 5. **Heading + Content**
```html
<h3>Delivery Timeline</h3>
<p>Ships In 30 Days</p>
```

### 6. **Badges/Labels**
```html
<span class="badge">Same day delivery</span>
<div class="label">Delivers in 7 working days</div>
```

### 7. **Paragraph Text**
```html
<p>This product will be shipped within 3-5 working days</p>
```

---

## Troubleshooting

### Problem: "No URLs loaded"

**Cause**: `urls.txt` is empty or malformed

**Fix**:
```bash
# Check file format
cat urls.txt | head -5
# Should show URLs starting with https://

# Or count valid URLs
grep '^https://' urls.txt | wc -l
```

### Problem: All entries are "N/A"

**Using Requests mode:**
- The site uses JavaScript to render shipping info
- **Solution**: Switch to Playwright mode:
  ```bash
  python python_scraper_unmatchedkicks.py --input urls.txt --output results.xlsx --playwright --delay 3
  ```

**Using Playwright mode:**
- The extraction patterns don't match this product's structure
- **Solution**: Run the validation script to re-scrape:
  ```bash
  python validate_and_rescrape_unmatchedkicks.py --input results.xlsx --output results_fixed.xlsx --playwright
  ```

### Problem: "Rate limited" warnings

**Cause**: Server is throttling requests

**Fix**: Increase `--delay`:
```bash
python python_scraper_unmatchedkicks.py --input urls.txt --output results.xlsx --playwright --delay 5
```

### Problem: Playwright hangs or crashes

**Cause**: Browser process not terminating properly

**Fix**:
```bash
# Kill stray Chromium processes
pkill -f chromium  # macOS/Linux
taskkill /F /IM chrome.exe  # Windows

# Reinstall Playwright
pip install --upgrade playwright
playwright install chromium
```

---

## Iterative Workflow Example

### Iteration 1: Initial Scrape

```bash
$ python python_scraper_unmatchedkicks.py --input urls.txt --output results.xlsx --playwright --delay 3
20:22:38 [INFO] Loaded 50 URLs from urls.txt
20:22:38 [INFO] Starting Playwright mode | 50 URLs | delay=3.0s
20:22:44 [INFO] [PW] https://unmatchedkicks.in/products/sp5der-sp555-tee-black → Ships In 14 Days
...
20:25:16 [INFO] ✅ Done. 50 scraped | 0 failed
```

### Iteration 2: Validate & Check for Incomplete Entries

```bash
$ python validate_and_rescrape_unmatchedkicks.py --input results.xlsx --output results_fixed.xlsx --playwright
20:25:20 [INFO] Reading results.xlsx…
20:25:21 [INFO] Found 8 incomplete entries to re-scrape
20:25:21 [INFO] Using Playwright mode
20:25:22 [INFO] Re-scraping: https://unmatchedkicks.in/products/fear-of-god-essentials-hoodie-plum (was: XL)
20:25:26 [INFO]   → Result: This product will be shipped within 3-5 working days
...
20:25:43 [INFO] ✅ Done!
20:25:43 [INFO] Saved 8 corrected entries
```

### Iteration 3 (if needed): Re-validate

```bash
$ python validate_and_rescrape_unmatchedkicks.py --input results_fixed.xlsx --output results_final.xlsx
20:25:45 [INFO] Reading results_fixed.xlsx…
20:25:45 [INFO] ✅ All entries are valid! No re-scraping needed.
```

---

## Command Reference

### Main Scraper

```bash
python python_scraper_unmatchedkicks.py \
  --input urls.txt \
  --output results.xlsx \
  --failed failed_urls.txt \
  --playwright \
  --delay 3 \
  --retries 3
```

**Options:**
- `--input` — Text file with URLs (one per line)
- `--output` — Excel file to write results (default: results.xlsx)
- `--failed` — Text file for failed URLs (default: failed_urls.txt)
- `--playwright` — Use Playwright (recommended)
- `--workers` — Concurrent threads for requests mode (default: 2)
- `--delay` — Seconds between requests (default: 2.5)
- `--retries` — Retry attempts per URL (default: 3)

### Validation & Re-scraper

```bash
python validate_and_rescrape_unmatchedkicks.py \
  --input results.xlsx \
  --output results_fixed.xlsx \
  --playwright \
  --delay 2.5 \
  --workers 2
```

**Options:**
- `--input` — Excel file to validate (default: results.xlsx)
- `--output` — Excel file with corrected data (default: results_fixed.xlsx)
- `--playwright` — Use Playwright for re-scraping
- `--delay` — Seconds between requests (default: 2.0)
- `--workers` — Concurrent threads (default: 2)

---

## Performance Tips

1. **Playwright is 3x slower but 90% more reliable** — use for first pass
2. **Increase `--delay` if rate-limited** — sites block fast sequential requests
3. **Run validation immediately after initial scrape** — catch incomplete entries early
4. **Use `--workers 1` if server is aggressive** — single-threaded mode is safer

### Typical Timeline

- **100 URLs with Playwright** — ~10-15 minutes
- **100 URLs with Requests** — ~5-7 minutes (but expect 30-40% "N/A")
- **50 re-scrapes with validation** — ~8-10 minutes

---

## File Structure

```
Scrapper_TimelineExtractor/
├── urls.txt                              # Input URLs (one per line)
├── results.xlsx                          # Initial scrape output
├── results_fixed.xlsx                    # Final validated/corrected output
├── failed_urls.txt                       # URLs that failed
│
├── python_scraper_unmatchedkicks.py      # Main scraper
├── validate_and_rescrape_unmatchedkicks.py  # Validation & re-scraper
└── test_load.py                          # (optional) Test URL loading
```

---

## What Gets Extracted

**Column A**: Product URL (clickable hyperlink)
**Column B**: Shipping Timeline

### Example Output

| Product URL | Shipping Timeline |
|---|---|
| https://unmatchedkicks.in/products/sp5der-sp555-tee-black | Ships In 14 Days |
| https://unmatchedkicks.in/products/fear-of-god-essentials-hoodie-plum | This product will be shipped within 3-5 working days |
| https://unmatchedkicks.in/products/hellstar-breaking-news-t-shirt-white | Same day delivery |
| https://unmatchedkicks.in/products/247-dna-hoodie-jet-black | Ships In 14 Days |

---

## Important Notes

⚠️ **Run on your local machine** — The site blocks cloud/datacenter IPs. Residential/home IPs work fine.

⚠️ **Be respectful** — Add delays between requests (minimum 2 seconds). The site is small and won't appreciate aggressive scraping.

⚠️ **Check robots.txt** — Always verify scraping is allowed before deploying to production.

✅ **For testing** — Start with 5-10 URLs to verify everything works before running 100+.

---

## Getting Help

### Check Logs

The scripts print detailed logs with timestamps. Look for:
- `[INFO]` — Normal progress
- `[ERROR]` — Failed URL or critical issue
- `[WARNING]` — Rate limit, timeout, or extraction issue

### Run a Single URL for Testing

```bash
echo "https://unmatchedkicks.in/products/sp5der-sp555-tee-black" > test.txt
python python_scraper_unmatchedkicks.py --input test.txt --output test_out.xlsx --playwright --delay 1
```

### Enable Debug Logging

```python
# Edit the script and change:
logging.basicConfig(level=logging.DEBUG)  # instead of INFO
```

---

## Next Steps

1. Prepare your `urls.txt` with product URLs
2. Run the main scraper with Playwright
3. Run validation to catch incomplete entries
4. Re-scrape any failures
5. Check `results_fixed.xlsx` for final data
6. Export to CSV if needed (Excel has "Save As" option)

Happy scraping! 🎉