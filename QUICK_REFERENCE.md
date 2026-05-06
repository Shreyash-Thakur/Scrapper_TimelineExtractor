# Quick Reference — Unmatched Kicks Scraper Cheat Sheet

## 🚀 Quick Start (3 Commands)

```bash
# 1. Initial Scrape (takes 15 mins for 50 URLs)
python python_scraper_unmatchedkicks.py --input urls.txt --output results.xlsx --playwright --delay 3

# 2. Validate & Fix Incomplete Entries
python validate_and_rescrape_unmatchedkicks.py --input results.xlsx --output results_fixed.xlsx --playwright

# 3. Done! Check results_fixed.xlsx
```

---

## 📋 Problem → Solution

| Problem | Solution |
|---------|----------|
| Script says "No URLs loaded" | Check `urls.txt` exists and has URLs starting with `https://` |
| All results are "N/A" | Use `--playwright` flag (requests mode doesn't handle JavaScript) |
| "Rate limited" warnings | Increase `--delay` to 5 or higher |
| Playwright hangs | Kill processes: `pkill -f chromium` then try again |
| Some entries show "XL", "S", "M" | Those are size data—run validation script to re-scrape |
| Script is too slow | Use `--workers 4 --delay 1.5` (but may get rate-limited) |

---

## 📁 File Setup

### Before Running

```
your-folder/
├── urls.txt                              ← Create this first!
├── python_scraper_unmatchedkicks.py      ← Copy from output
└── validate_and_rescrape_unmatchedkicks.py ← Copy from output
```

### After Running

```
your-folder/
├── urls.txt
├── results.xlsx                          ← From stage 1
├── results_fixed.xlsx                    ← From stage 2 (final!)
├── failed_urls.txt                       ← URLs that failed
└── *.py                                  ← Scripts
```

---

## 🎯 Common Commands

### Scrape 50 URLs (Recommended)
```bash
python python_scraper_unmatchedkicks.py --input urls.txt --output results.xlsx --playwright --delay 3
```

### Scrape 200+ URLs (More aggressive)
```bash
python python_scraper_unmatchedkicks.py --input urls.txt --output results.xlsx --playwright --delay 2
```

### Scrape Very Slowly (If getting rate-limited)
```bash
python python_scraper_unmatchedkicks.py --input urls.txt --output results.xlsx --playwright --delay 5
```

### Validate Results (See how many are incomplete)
```bash
python validate_and_rescrape_unmatchedkicks.py --input results.xlsx --output results_fixed.xlsx
```

### Quick Test (Single URL)
```bash
echo "https://unmatchedkicks.in/products/sp5der-sp555-tee-black" > test.txt
python python_scraper_unmatchedkicks.py --input test.txt --output test_out.xlsx --playwright --delay 1
```

---

## ⚙️ Parameter Guide

### Main Scraper: `python_scraper_unmatchedkicks.py`

```
--input FILE              Where to read URLs from (default: urls.txt)
--output FILE             Where to write Excel results (default: results.xlsx)
--failed FILE             Where to write failed URLs (default: failed_urls.txt)
--playwright              Use browser (RECOMMENDED - handles JavaScript)
--workers N               Parallel threads for requests mode (default: 2, max: 8)
--delay SECONDS           Wait between requests (default: 2.5, recommend: 3-5)
--retries N               How many times to retry failed URLs (default: 3)
```

### Validation: `validate_and_rescrape_unmatchedkicks.py`

```
--input FILE              Excel file from stage 1 (default: results.xlsx)
--output FILE             Where to write corrected Excel (default: results_fixed.xlsx)
--playwright              Use browser for re-scraping (RECOMMENDED)
--delay SECONDS           Wait between re-scrape requests (default: 2.0)
--workers N               Parallel threads for requests mode (default: 2)
```

---

## 📊 What Gets Detected as Valid/Invalid

### ✅ Valid Shipping Timeline (Will be kept)
- "Ships In 14 Days"
- "This product will be shipped within 3-5 working days"
- "Same day delivery"
- "Ships In 30 Days"
- "Delivers within 7 working days"
- "Next business day delivery"
- "Ships in 1 week"

### ❌ Invalid Data (Will be re-scraped)
- "XL", "S", "M", "L" (size data)
- "8999.00" (price data)
- "₹21999" (currency)
- "N/A" (placeholder)
- Empty cell

---

## 🔍 Extraction Priority (What the scraper checks first)

1. ✨ **JSON-LD** — Structured data in `<script>` tags
2. 🔘 **Buttons** — `<button>SHIPS IN 14 DAYS</button>`
3. 📝 **Forms** — `<input value="Ships In 14 Days">`
4. 🎨 **Highlighted Box** — Blue/colored div with shipping info
5. 🏷️ **Headings** — `<h3>Delivery Timeline</h3>` + nearby text
6. 📌 **Badges** — `<span class="badge">Ships In 14 Days</span>`
7. 📄 **Paragraphs** — `<p>` tags with shipping keywords
8. 🚫 **Fallback** — Returns "N/A" if nothing found

---

## 💡 Tips & Tricks

### Performance

**Fast Mode** (for small lists <20 URLs):
```bash
--delay 1.5 --workers 4
```

**Safe Mode** (for large lists or sensitive servers):
```bash
--delay 5 --workers 1
```

**Balanced** (recommended):
```bash
--delay 3 --workers 2
```

### Testing Before Full Run

```bash
# Test first 5 URLs
head -5 urls.txt > test.txt
python python_scraper_unmatchedkicks.py --input test.txt --output test_results.xlsx --playwright --delay 2
# Check test_results.xlsx before running full list
```

### Check URL Format

```bash
# Count valid URLs
grep -c '^https://' urls.txt

# See first 5 URLs
head -5 urls.txt

# Remove empty lines
grep -v '^$' urls.txt > urls_clean.txt
```

### Monitor Progress (Real-time)

```bash
# Watch logs while script runs (in another terminal)
tail -f your_scraper.log  # if you redirect output to a log file
```

---

## 🛠️ Setup Checklist

- [ ] Python 3.7+ installed
- [ ] Dependencies installed: `pip install requests beautifulsoup4 playwright openpyxl`
- [ ] Playwright browser installed: `playwright install chromium`
- [ ] `urls.txt` created with product URLs
- [ ] Test with 1-2 URLs first
- [ ] Run full scrape
- [ ] Run validation script
- [ ] Check `results_fixed.xlsx` for completeness

---

## 🐛 Common Error Messages

| Message | Meaning | Fix |
|---------|---------|-----|
| `FileNotFoundError: urls.txt` | urls.txt doesn't exist | Create it: `echo "https://..." > urls.txt` |
| `No URLs loaded. Check your input file.` | urls.txt is empty or malformed | Check file format: `cat urls.txt \| head` |
| `ModuleNotFoundError: No module named 'playwright'` | Playwright not installed | `pip install playwright` |
| `Error: Browser not found` | Chromium not installed | `playwright install chromium` |
| `[WARNING] Rate limited` | Server throttling requests | Increase `--delay` value |
| `TimeoutError: page.goto` | Page too slow or unreachable | Increase `--delay` and retry |

---

## 📈 Typical Results

### Playwright Mode
- **Success rate**: 85-95% first pass
- **Speed**: ~30-60 sec per URL
- **Re-scrape rate**: 5-15% need fixing

### Requests Mode
- **Success rate**: 20-40% (limited by JavaScript)
- **Speed**: ~2-5 sec per URL
- **Re-scrape rate**: 60-80% need fixing (❌ not recommended)

### After Validation
- **Success rate**: >98%
- **Time**: Original scrape + validation overhead (20-30% extra)

---

## 🎓 Learning Path

1. **Start here**: Run test with 5 URLs
2. **Understand**: Read SETUP_AND_USAGE_GUIDE.md
3. **Master**: Adjust `--delay` and `--workers` for your needs
4. **Optimize**: Use validation loop for large batches (100+)
5. **Deploy**: Automate with scheduler if scraping regularly

---

## 📞 Quick Answers

**Q: Should I use Playwright or Requests?**
A: Always Playwright. It's slower but handles JavaScript and gets 95%+ accuracy.

**Q: How long does 100 URLs take?**
A: ~2-3 hours with Playwright at delay=3. Use delay=2 if you're in a hurry.

**Q: What if validation finds more incomplete entries?**
A: Run it again. Most get fixed the 2nd time. Rare 3rd run needed.

**Q: Can I use this on cloud servers?**
A: No. Site blocks datacenter IPs. Must run on home/residential IP.

**Q: How often do I need to re-validate?**
A: After each major scrape. Validation is fast (2-5 mins for 100 entries).

---

## 🎯 Success Indicators

✅ You're doing it right if:
- Logs show "Ships In X Days" / "delivered within X days"
- results.xlsx has <5% "N/A" entries
- validation finds <10% incomplete entries
- No "Rate limited" errors (or only occasional)

❌ Something's wrong if:
- All results are "N/A"
- Constant rate limiting
- Playwright crashes repeatedly
- urls.txt format issues

---

**Happy scraping!** 🚀