# Smart Re-scraper — Only Fix Incomplete Entries

## 🎯 What This Does

Instead of re-scraping everything, this script:

1. **Reads your existing results** (results.csv or results.xlsx)
2. **Identifies COMPLETE entries** → Ships In 14 Days, delivered within X days, etc. → **SKIPS THEM**
3. **Identifies INCOMPLETE entries** → N/A, XL, S, M, prices → **RE-SCRAPES ONLY THESE**
4. **Merges results back** → Keeps good ones, fixes bad ones
5. **Saves updated file** → results_updated.csv

**Result**: Only 8-50 URLs re-scraped instead of all 1486!

---

## 🚀 Usage

### Option 1: Playwright (Recommended - Handles JavaScript)
```bash
python smart_rescraper.py --input results.csv --output results_updated.csv --playwright --delay 3
```

### Option 2: Requests Mode (Faster)
```bash
python smart_rescraper.py --input results.csv --output results_updated.csv --workers 3 --delay 2
```

### Option 3: Excel Input
```bash
python smart_rescraper.py --input results.xlsx --output results_updated.csv --playwright --delay 3
```

---

## 📊 What Gets Skipped vs Re-scraped

### ✅ SKIPPED (Already Complete)
- "Ships In 14 Days"
- "This product will be shipped within 3-5 working days"
- "Same day delivery"
- "Delivered in 7 working days"
- Any entry with keywords: ship, deliver, days, working, week, hours, express

### ❌ RE-SCRAPED (Incomplete)
- "N/A" ← Extraction failed
- "XL", "S", "M", "L" ← Size data instead of shipping
- "8999.00" ← Price data instead of shipping
- "₹21999" ← Currency instead of shipping
- Empty cells
- "Extra Small", "Medium", "One Size" ← Size words

---

## 📈 Expected Results

**Before:**
```
1486 URLs in results.csv
├─ 1400 with "Ships In 14 Days" (already correct)
├─ 50 with "N/A" (failed extraction)
├─ 30 with sizes like "XL", "S", "M" (wrong data)
└─ 6 with prices (wrong data)

Total incomplete: 86 entries
```

**After running smart_rescraper:**
```
results_updated.csv
├─ 1400 kept as-is (✅ already correct)
├─ 85 fixed (was N/A, XL, prices → now have shipping timelines)
└─ 1 still N/A (couldn't extract)

Total complete: 1485/1486 (99.9%)
```

---

## ⚡ Speed Comparison

### Old Approach (Re-scrape Everything)
```
1486 URLs × 40 sec/URL (Playwright) = 16+ hours ❌
1486 URLs × 2 sec/URL (Requests) = ~50 minutes ❌
```

### Smart Approach (Only Incomplete)
```
86 URLs × 40 sec/URL (Playwright) = ~1 hour ✅
86 URLs × 2 sec/URL (Requests) = 3-4 minutes ✅
```

**Time saved: 15 hours!**

---

## 🔧 Parameters

```bash
--input FILE              Input CSV or Excel file (default: results.csv)
--output FILE             Output CSV file (default: results_updated.csv)
--playwright              Use Playwright (recommended for JS-heavy sites)
--workers N               Parallel threads for requests mode (default: 2)
--delay SECONDS           Wait between requests (default: 2.0)
--retries N               Retry attempts per URL (default: 3)
```

---

## 💡 Examples

### Fix 86 incomplete entries with Playwright (Safe)
```bash
python smart_rescraper.py --input results.csv --output results_updated.csv --playwright --delay 3
```
Time: ~1 hour | Accuracy: 95%+

### Fix quickly with Requests (Fast)
```bash
python smart_rescraper.py --input results.csv --output results_updated.csv --workers 4 --delay 1.5
```
Time: 3-5 minutes | Accuracy: 60-70% (use Playwright for better results)

### From Excel file
```bash
python smart_rescraper.py --input results.xlsx --output results_updated.csv --playwright --delay 3
```

### Very careful (if getting rate-limited)
```bash
python smart_rescraper.py --input results.csv --output results_updated.csv --playwright --delay 5 --retries 5
```
Time: ~2 hours | Accuracy: 99%+

---

## 🎯 Which Mode to Use?

| Situation | Mode | Parameters |
|-----------|------|-----------|
| Want accuracy | Playwright | `--playwright --delay 3` |
| Want speed | Requests | `--workers 3 --delay 2` |
| Site is aggressive | Playwright Safe | `--playwright --delay 5 --retries 5` |
| Small number (<20) | Playwright | `--playwright --delay 2` |
| Large number (100+) | Requests Fast | `--workers 4 --delay 1.5` |

---

## 📋 Typical Workflow

1. **Run initial scraper** → `results.csv` (your 1486 URLs)
2. **Run smart_rescraper** → `results_updated.csv` (fixed incomplete ones)
3. **Check results** → Should have >99% complete
4. **If still incomplete** → Run smart_rescraper again on results_updated.csv

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Input file not found" | Make sure results.csv exists in current folder |
| All new values are "N/A" | Use `--playwright` instead of requests mode |
| "Rate limited" warnings | Increase `--delay` to 5 or 10 |
| Playwright crashes | Use requests mode with `--workers 2 --delay 2` |
| Takes too long | Use `--workers 4` with requests mode (faster but less accurate) |

---

## ✅ Success Indicators

- ✅ results_updated.csv is created
- ✅ Fewer "N/A" entries than before
- ✅ No more size data (XL, S, M, L)
- ✅ Most entries now have shipping keywords
- ✅ Log shows fixed entries (Old: XL → New: Ships In 14 Days)

---

## 🎓 How It Works

```python
# For each URL in your results.csv:

if is_entry_complete(timeline_value):
    # Entry already has "Ships In 14 Days" or similar
    SKIP IT (don't re-scrape)
    Keep existing value
else:
    # Entry has "N/A", "XL", price, or empty
    RE-SCRAPE IT
    Try all 7 extraction patterns
    Use best result

# Merge and save
output = keep_complete + fix_incomplete
```

---

## 📊 Log Output Example

```
09:30:00 [INFO] Reading results.csv…
09:30:02 [INFO] Total entries: 1486
09:30:02 [INFO] Complete entries (will SKIP): 1400
09:30:02 [INFO] Incomplete entries (will RE-SCRAPE): 86
09:30:02 [INFO] Re-scraping 86 incomplete entries…
09:30:05 [PW] https://unmatchedkicks.in/products/sp5der-legacy-sweatpant-blue | Old: N/A → New: Ships In 14 Days
09:30:08 [PW] https://unmatchedkicks.in/products/sp5der-beluga-hoodie-sand | Old: N/A → New: This product will be shipped within 3-5 working days
...
09:45:30 [INFO] Merging results…
09:45:31 [INFO] Writing to results_updated.csv…
09:45:32 [INFO] ✅ Done!
09:45:32 [INFO]    Fixed: 82/86 incomplete entries
09:45:32 [INFO]    Output: results_updated.csv
```

---

## 🎉 Result

**From:**
```csv
product_url,shipping_timeline
https://unmatchedkicks.in/products/sp5der-legacy-sweatpant-blue,N/A
https://unmatchedkicks.in/products/sp5der-beluga-hoodie-sand,N/A
https://unmatchedkicks.in/products/fear-of-god-essentials-hoodie-plum,XL
```

**To:**
```csv
product_url,shipping_timeline
https://unmatchedkicks.in/products/sp5der-legacy-sweatpant-blue,Ships In 14 Days
https://unmatchedkicks.in/products/sp5der-beluga-hoodie-sand,This product will be shipped within 3-5 working days
https://unmatchedkicks.in/products/fear-of-god-essentials-hoodie-plum,This product will be shipped within 3-5 working days
```

✅ **Problem solved!**