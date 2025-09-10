# #!/usr/bin/env python3
# """
# Cookiepedia Multi-Scraper (Cloudflare bypass enabled)

# Scrapes Cookiepedia for multiple cookie names (CMPs + analytics cookies).

# Outputs a raw domain list for each cookie as well as a combined file.

# Usage:
#     cookiepedia_scraper.py --cookies <cookies> --threads <threads> --max_pages <max_pages> --outdir <outdir>

# Options:
#     --cookies <cookies>    Comma-separated cookie names (e.g., CookieConsent,OptanonConsent,_ga,_fbp)
#     --threads <threads>    (unused in sequential mode, kept for compatibility)
#     --max_pages <max_pages> Max number of pages per cookie [default: 200]
#     --outdir <outdir>      Output directory for results [default: sources]
# """

# import os
# import re
# import logging
# import cloudscraper
# from bs4 import BeautifulSoup
# from docopt import docopt
# from typing import Optional, Set

# BASE_URL = "https://cookiepedia.co.uk/cookies/"
# STOP_MSG = "Sorry, your search returned no matches"

# # Create a Cloudflare-aware session
# scraper = cloudscraper.create_scraper()

# HEADERS = {
#     "User-Agent": (
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) "
#         "Chrome/122.0.0.0 Safari/537.36"
#     ),
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
#     "Accept-Language": "en-US,en;q=0.9",
#     "Connection": "keep-alive",
# }

# logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
# logger = logging.getLogger("cookiepedia-scraper")


# def fetch(url: str) -> Optional[str]:
#     """Fetch HTML content with Cloudflare bypass."""
#     try:
#         r = scraper.get(url, headers=HEADERS, timeout=30)
#         if r.status_code == 200:
#             return r.text
#         logger.warning(f"Failed {url} → {r.status_code}")
#         return None
#     except Exception as e:
#         logger.error(f"Error fetching {url}: {e}")
#         return None


# def parse(html: str) -> Set[str]:
#     """Parse domains from Cookiepedia search results page."""
#     soup = BeautifulSoup(html, "html.parser")
#     if soup.find("h2", string=re.compile(STOP_MSG)):
#         return set()
#     results = set()
#     for a in soup.find_all("a", href=re.compile(r"^/cookie/\d+")):
#         text = (a.get_text() or "").strip().lower()
#         if text:
#             results.add(text)
#     return results


# def crawl(cookie: str, max_pages: int) -> Set[str]:
#     """Sequential crawl to avoid rate-limiting."""
#     domains = set()
#     for page in range(max_pages):
#         url = f"{BASE_URL}{cookie}/{page}"
#         html = fetch(url)
#         if not html:
#             logger.warning(f"[{cookie}] No response at page {page}, stopping.")
#             break
#         new = parse(html)
#         if not new:
#             logger.info(f"[{cookie}] Reached end at page {page}.")
#             break
#         domains.update(new)
#     logger.info(f"[{cookie}] Collected {len(domains)} domains")
#     return domains


# def save(outdir: str, cookie: str, domains: Set[str]):
#     """Save domains to file."""
#     os.makedirs(outdir, exist_ok=True)
#     outfile = os.path.join(outdir, f"cookiepedia_{cookie}.txt")
#     with open(outfile, "w") as f:
#         for d in sorted(domains):
#             f.write(d + "\n")
#     logger.info(f"Saved → {outfile}")
#     return outfile


# def main():
#     args = docopt(__doc__)
#     cookies = args["--cookies"].split(",")
#     max_pages = int(args["--max_pages"])
#     outdir = args["--outdir"]

#     all_domains = set()
#     for cookie in cookies:
#         cookie = cookie.strip()
#         domains = crawl(cookie, max_pages)
#         all_domains.update(domains)
#         save(outdir, cookie, domains)

#     combined = os.path.join(outdir, "cookiepedia_all.txt")
#     with open(combined, "w") as f:
#         for d in sorted(all_domains):
#             f.write(d + "\n")
#     logger.info(f"Combined total: {len(all_domains)} domains → {combined}")


# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
"""
Cookiepedia CMP Scraper (batch mode with Cloudflare bypass)

Extracts domains for Cookiebot (CookieConsent) and OneTrust (OptanonConsent).
Crawls Cookiepedia in batches to avoid rate limits.

Usage:
    cookiepedia_cmp_scraper.py (cookiebot|onetrust) --num_threads <NT> --max_pages <MP>

Options:
    cookiebot               Extract potential candidates for the Cookiebot CMP
    onetrust                Extract potential candidates for the OneTrust CMP
    --num_threads <NT>      Number of parallel requests per batch
    --max_pages <MP>        Maximum number of pages to crawl
"""

import logging
import re
import time
import cloudscraper
from bs4 import BeautifulSoup
from docopt import docopt
from typing import Set, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Base URLs
cp_cookiebot = "https://cookiepedia.co.uk/cookies/CookieConsent/"
cp_onetrust = "https://cookiepedia.co.uk/cookies/OptanonConsent/"
stop_page = "Sorry, your search returned no matches"

# Cloudflare-aware session
scraper = cloudscraper.create_scraper()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

logger = logging.getLogger("cookiepedia-cmp")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def fetch(url: str) -> Optional[str]:
    try:
        r = scraper.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.text
        return None
    except Exception:
        return None


def parse(html: str) -> Set[str]:
    soup = BeautifulSoup(html, "html.parser")
    if soup.find("h2", string=re.compile(stop_page)):
        return set()
    results = set()
    for a in soup.find_all("a", href=re.compile(r"^/cookie/\d+")):
        text = (a.get_text() or "").strip()
        if text:
            results.add(text)
    return results


def crawl_batch(base_url: str, start: int, end: int, threads: int) -> Tuple[Set[str], bool]:
    """Crawl a batch of pages in parallel. Returns (domains, stop_flag)."""
    domains = set()
    stop_flag = False
    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_map = {executor.submit(fetch, f"{base_url}{i}"): i for i in range(start, end)}
        for future in as_completed(future_map):
            html = future.result()
            if not html:
                continue
            new = parse(html)
            if not new:  # stop condition
                stop_flag = True
            else:
                domains.update(new)
    return domains, stop_flag


def main():
    args = docopt(__doc__)
    if args["cookiebot"]:
        base_url = cp_cookiebot
        outfile = "cookiepedia_cookiebot_domains.txt"
    elif args["onetrust"]:
        base_url = cp_onetrust
        outfile = "cookiepedia_onetrust_domains.txt"
    else:
        raise ValueError("Invalid CMP Type")

    threads = int(args["--num_threads"])
    max_pages = int(args["--max_pages"])

    all_domains = set()
    batch_size = threads
    page = 0
    while page < max_pages:
        start = page
        end = min(page + batch_size, max_pages)
        logger.info(f"Crawling pages {start}–{end-1}...")
        batch_domains, stop = crawl_batch(base_url, start, end, threads)
        all_domains.update(batch_domains)
        page += batch_size
        if stop:
            logger.info(f"Reached end of list at page {page}")
            break
        time.sleep(2)  # politeness delay between batches

    logger.info(f"Total unique domains collected: {len(all_domains)}")

    with open(outfile, "w") as f:
        for d in sorted(all_domains):
            f.write(d + "\n")

    logger.info(f"Saved → {outfile}")


if __name__ == "__main__":
    main()
