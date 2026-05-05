"""
Shipping Timeline Scraper — unmatchedkicks.in
=============================================
Run this script on YOUR LOCAL MACHINE (not a cloud server).
The site blocks datacenter IPs; residential/home IPs work fine.

USAGE
-----
# Install dependencies (once):
    pip install requests beautifulsoup4 playwright
    playwright install chromium        # only needed if --playwright flag is used

# Basic (requests + BS4, fastest):
    python scraper_unmatchedkicks.py --input urls.txt --output results.csv

# Playwright mode (handles JS-rendered pages):
    python scraper_unmatchedkicks.py --input urls.txt --output results.csv --playwright

# All options:
    python scraper_unmatchedkicks.py \
        --input urls.txt \
        --output results.csv \
        --failed failed_urls.txt \
        --workers 5 \
        --delay 1.5 \
        --retries 3

INPUT FILE FORMAT (urls.txt)
-----------------------------
One URL per line. Lines starting with # or blank lines are skipped.
Example:
    https://unmatchedkicks.in/products/sp5der-sp555-tee-black
    https://unmatchedkicks.in/products/hellstar-warm-up-t-shirt-black

OUTPUT
------
  results.csv       — product_url, shipping_timeline
  failed_urls.txt   — URLs that failed after all retries
"""

import argparse
import asyncio
import csv
import logging
import random
import re
import sys
import time
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scraper")

# ── Constants ─────────────────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}

# Patterns to strip from Pattern-1 text
STRIP_PREFIXES = re.compile(
    r"(?i)^(this product will be shipped (within|in)\s*|shipped (within|in)\s*|ships in\s*)",
    re.IGNORECASE,
)


# ── Extraction Logic ──────────────────────────────────────────────────────────

def extract_shipping(html: str) -> str:
    """
    Parse HTML and extract shipping timeline.
    Priority: Pattern 2 → Pattern 1 → "N/A"
    """
    soup = BeautifulSoup(html, "html.parser")

    # ── Pattern 2a: <legend> → <span data-selected-value> ──────────────────
    span = soup.select_one("legend.form__label span[data-selected-value]")
    if span:
        text = span.get_text(strip=True)
        if text:
            return clean_text(text)

    # ── Pattern 2b: <input value="Ships In ..."> ────────────────────────────
    inp = soup.select_one('input[value*="Ships"], input[value*="ships"]')
    if inp:
        text = inp.get("value", "").strip()
        if text:
            return clean_text(text)

    # ── Pattern 2c: any element containing "Ships In" (broader fallback) ────
    for tag in soup.find_all(string=re.compile(r"Ships\s+[Ii]n\s+\d", re.I)):
        text = tag.strip()
        if text:
            return clean_text(text)

    # ── Pattern 1: .text-truncator p ────────────────────────────────────────
    p = soup.select_one(".text-truncator p")
    if p:
        text = p.get_text(strip=True)
        if text:
            return clean_text(text)

    # ── Broader Pattern 1 fallback: any <p> mentioning shipping ─────────────
    for p_tag in soup.find_all("p"):
        text = p_tag.get_text(strip=True)
        if re.search(r"ship(ped|ping|s)?\s+(within|in)\s+\d", text, re.I):
            return clean_text(text)

    return "N/A"


def clean_text(text: str) -> str:
    """Remove known boilerplate prefixes and normalise whitespace."""
    text = text.strip()
    # Remove "Delivery Timeline:" prefix (from legend label text leaking in)
    text = re.sub(r"(?i)^delivery\s+timeline\s*:\s*", "", text).strip()
    # Remove "This product will be shipped within"
    text = re.sub(r"(?i)^this product will be shipped (within|in)\s*", "", text).strip()
    # Remove "shipped within / shipped in"
    text = re.sub(r"(?i)^shipped (within|in)\s*", "", text).strip()
    # Remove standalone "Ships In" only if followed by something (keep "Ships In 14 Days")
    # We keep "Ships In X Days" as-is — it's already clean
    # Normalise internal whitespace
    text = " ".join(text.split())
    return text if text else "N/A"


# ── HTTP Scraper (requests) ───────────────────────────────────────────────────

class RequestsScraper:
    def __init__(self, retries: int = 3, delay: float = 1.5):
        self.retries = retries
        self.delay = delay
        self.session = requests.Session()
        # Warm up session with a homepage hit (gets cookies)
        try:
            self.session.get(
                "https://unmatchedkicks.in/",
                headers=self._headers(),
                timeout=15,
            )
        except Exception:
            pass

    def _headers(self) -> dict:
        h = dict(BASE_HEADERS)
        h["User-Agent"] = random.choice(USER_AGENTS)
        return h

    def fetch(self, url: str) -> Optional[str]:
        for attempt in range(1, self.retries + 1):
            try:
                resp = self.session.get(
                    url,
                    headers=self._headers(),
                    timeout=20,
                    allow_redirects=True,
                )
                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code in (429, 503):
                    wait = self.delay * (2 ** attempt) + random.uniform(0, 1)
                    log.warning(f"Rate limited ({resp.status_code}) on {url}. Waiting {wait:.1f}s…")
                    time.sleep(wait)
                elif resp.status_code == 404:
                    log.warning(f"404 Not Found: {url}")
                    return None
                else:
                    log.warning(f"HTTP {resp.status_code} for {url} (attempt {attempt})")
            except requests.exceptions.RequestException as e:
                log.warning(f"Request error on {url} attempt {attempt}: {e}")
                if attempt < self.retries:
                    time.sleep(self.delay * attempt)
        return None

    def scrape(self, url: str) -> str:
        html = self.fetch(url)
        if html is None:
            return None  # signal failure
        return extract_shipping(html)


# ── Playwright Scraper (async) ────────────────────────────────────────────────

async def playwright_scrape_batch(urls: list[str], delay: float = 1.5, retries: int = 3):
    """Scrape a list of URLs using Playwright (headless Chromium)."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    results = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            locale="en-IN",
            extra_http_headers={
                "Accept-Language": "en-IN,en;q=0.9",
            },
        )
        page = await context.new_page()

        for url in urls:
            for attempt in range(1, retries + 1):
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    # Wait for shipping-related element or settle
                    try:
                        await page.wait_for_selector(
                            "legend.form__label, .text-truncator",
                            timeout=5000,
                        )
                    except Exception:
                        pass  # element may not exist; continue with what loaded
                    html = await page.content()
                    shipping = extract_shipping(html)
                    results[url] = shipping
                    log.info(f"[PW] {url} → {shipping}")
                    await asyncio.sleep(delay + random.uniform(0, 0.5))
                    break
                except Exception as e:
                    log.warning(f"[PW] Error on {url} attempt {attempt}: {e}")
                    if attempt == retries:
                        results[url] = None
                    else:
                        await asyncio.sleep(delay * attempt)

        await browser.close()
    return results


# ── Main Orchestration ────────────────────────────────────────────────────────

def load_urls(path: str) -> list[str]:
    urls = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Accept bare slugs too
                if not line.startswith("http"):
                    line = f"https://unmatchedkicks.in/products/{line}"
                urls.append(line)
    return urls


def run_requests_mode(
    urls: list[str],
    output_path: str,
    failed_path: str,
    workers: int,
    delay: float,
    retries: int,
):
    scraper = RequestsScraper(retries=retries, delay=delay)
    results = []
    failed = []
    total = len(urls)

    log.info(f"Starting requests mode | {total} URLs | {workers} workers | delay={delay}s")

    def process(url: str):
        # Jitter to avoid synchronized bursts across threads
        time.sleep(random.uniform(0, delay))
        shipping = scraper.scrape(url)
        return url, shipping

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(process, url): url for url in urls}
        done = 0
        for future in as_completed(futures):
            url, shipping = future.result()
            done += 1
            if shipping is None:
                failed.append(url)
                log.error(f"[{done}/{total}] FAILED: {url}")
            else:
                results.append({"product_url": url, "shipping_timeline": shipping})
                log.info(f"[{done}/{total}] {url} → {shipping}")
            # Throttle: sleep between completions regardless of threads
            time.sleep(delay / workers)

    write_csv(results, output_path)
    write_failed(failed, failed_path)
    log.info(f"\n✅ Done. {len(results)} scraped | {len(failed)} failed")
    log.info(f"   Output:  {output_path}")
    log.info(f"   Failed:  {failed_path}")


def run_playwright_mode(
    urls: list[str],
    output_path: str,
    failed_path: str,
    delay: float,
    retries: int,
):
    log.info(f"Starting Playwright mode | {len(urls)} URLs | delay={delay}s")
    results_map = asyncio.run(playwright_scrape_batch(urls, delay=delay, retries=retries))

    results = []
    failed = []
    for url, shipping in results_map.items():
        if shipping is None:
            failed.append(url)
        else:
            results.append({"product_url": url, "shipping_timeline": shipping})

    write_csv(results, output_path)
    write_failed(failed, failed_path)
    log.info(f"\n✅ Done. {len(results)} scraped | {len(failed)} failed")
    log.info(f"   Output:  {output_path}")
    log.info(f"   Failed:  {failed_path}")


def write_csv(rows: list[dict], path: str):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["product_url", "shipping_timeline"],
            quoting=csv.QUOTE_ALL,  # always quote — prevents "Ships In 14 Days" splitting on comma
        )
        writer.writeheader()
        writer.writerows(rows)


def write_failed(urls: list[str], path: str):
    with open(path, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Scrape shipping timelines from unmatchedkicks.in",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--input", required=True, help="Path to text file with one URL per line")
    p.add_argument("--output", default="results.csv", help="Output CSV path (default: results.csv)")
    p.add_argument("--failed", default="failed_urls.txt", help="Path to write failed URLs (default: failed_urls.txt)")
    p.add_argument("--workers", type=int, default=4, help="Concurrent workers for requests mode (default: 4)")
    p.add_argument("--delay", type=float, default=1.5, help="Seconds between requests per worker (default: 1.5)")
    p.add_argument("--retries", type=int, default=3, help="Retry attempts per URL (default: 3)")
    p.add_argument("--playwright", action="store_true", help="Use Playwright (headless browser) instead of requests")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    urls = load_urls(args.input)
    if not urls:
        log.error("No URLs loaded. Check your input file.")
        sys.exit(1)

    log.info(f"Loaded {len(urls)} URLs from {args.input}")

    if args.playwright:
        run_playwright_mode(
            urls=urls,
            output_path=args.output,
            failed_path=args.failed,
            delay=args.delay,
            retries=args.retries,
        )
    else:
        run_requests_mode(
            urls=urls,
            output_path=args.output,
            failed_path=args.failed,
            workers=args.workers,
            delay=args.delay,
            retries=args.retries,
        )


if __name__ == "__main__":
    main()