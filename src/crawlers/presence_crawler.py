import requests
import requests.exceptions as rexcepts
import re
import logging
import time
from enum import IntEnum
from urllib.parse import urlparse
from typing import List, Tuple, Optional, Dict, Any
from concurrent.futures import TimeoutError as CTimeoutError

from pebble import ProcessPool
from pebble.common import ProcessExpired

logger = logging.getLogger("presence-crawl")

# Cookiebot CDN domain patterns
cb_base_pat = re.compile(r"https://consent\.cookiebot\.(com|eu)/", re.IGNORECASE)
cb_script_name = re.compile(r"cb-main\.js", re.IGNORECASE)

# OneTrust CDN patterns
onetrust_patterns = (
    re.compile(r"https://cdn-apac\.onetrust\.com", re.IGNORECASE),
    re.compile(r"https://cdn-ukwest\.onetrust\.com", re.IGNORECASE),
    re.compile(r"https://cmp-cdn\.cookielaw\.org", re.IGNORECASE),
    re.compile(r"https://cdn\.cookielaw\.org", re.IGNORECASE),
    re.compile(r"https://optanon\.blob\.core\.windows\.net", re.IGNORECASE),
    re.compile(r"https://cookie-cdn\.cookiepro\.com", re.IGNORECASE),
    re.compile(r"https://cookiepro\.blob\.core\.windows\.net", re.IGNORECASE),
)

# Termly CDN domain
termly_url_pattern = re.compile(r"https://app\.termly\.io/", re.IGNORECASE)

# Timeout settings
connect_timeout = 20
load_timeout = 30
parse_timeout = 120

# Configuration
check_cmp = True
debug_mode = False


class QuickCrawlResult(IntEnum):
    """Result codes for presence crawling"""
    CRAWL_TIMEOUT = -1
    OK = 0
    CONNECT_FAIL = 1
    HTTP_ERROR = 2
    BOT = 3
    NOCMP = 4
    COOKIEBOT = 5
    ONETRUST = 6
    TERMLY = 7


class PresenceCrawler:
    """Fast HTTP-based crawler to check CMP presence on websites"""
    
    def __init__(self, num_threads: int = 4, output_dir: str = "./data/results"):
        self.num_threads = num_threads
        self.output_dir = output_dir
        self.setup_logger()
    
    def setup_logger(self):
        """Set up logger for presence crawler"""
        logger.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    def check_cookiebot_presence(self, resp: requests.Response) -> bool:
        """Check whether Cookiebot is referenced on the website"""
        psource = resp.text
        return (cb_base_pat.search(psource) is not None or 
                cb_script_name.search(psource) is not None)
    
    def check_onetrust_presence(self, resp: requests.Response) -> bool:
        """Check whether a OneTrust pattern is referenced on the website"""
        psource = resp.text
        for pattern in onetrust_patterns:
            if pattern.search(psource):
                return True
        return False
    
    def check_termly_presence(self, resp: requests.Response) -> bool:
        """Check whether a Termly pattern is referenced on the website"""
        psource = resp.text
        return termly_url_pattern.search(psource) is not None
    
    def run_reachability_check(self, input_domain: str) -> Tuple[Optional[str], int]:
        """
        Try to retrieve the webpage at the given domain and detect CMP presence.
        
        @param input_domain: domain to attempt to connect to
        @return: Tuple of (final_url, status_code)
        """
        # Handle URL prefixes
        component_tuple = urlparse(input_domain)
        if component_tuple.scheme in ("http", "https"):
            url_suffix = input_domain
            prefix_list = [""]
        else:
            url_suffix = re.sub(r"^www\.", "", input_domain)
            prefix_list = ["https://www.", "https://", "http://"]
        
        final_url = None
        r = None
        
        # Try different URL prefixes
        for prefix in prefix_list:
            completed_url = prefix + url_suffix
            
            try:
                headers = {
                    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
                }
                r = requests.get(completed_url, timeout=(connect_timeout, load_timeout), headers=headers)
            except (rexcepts.TooManyRedirects, rexcepts.SSLError, 
                    rexcepts.URLRequired, rexcepts.MissingSchema):
                if debug_mode:
                    logger.debug(f"SSL/Schema error for: '{completed_url}'")
                return input_domain, QuickCrawlResult.CONNECT_FAIL
            except (rexcepts.ConnectionError, rexcepts.Timeout):
                if debug_mode:
                    logger.debug(f"Connection/timeout error for: '{completed_url}'")
                continue
            except Exception as ex:
                if debug_mode:
                    logger.error(f"Unexpected error for '{completed_url}': {ex}")
                return input_domain, QuickCrawlResult.CONNECT_FAIL
            
            if r is None:
                continue
            elif not r.ok:
                # Bot detection responses
                if r.status_code in (403, 406):
                    return completed_url, QuickCrawlResult.BOT
                else:
                    return completed_url, QuickCrawlResult.HTTP_ERROR
            else:
                final_url = r.url
                break
        
        # Check for CMP presence if we got a successful response
        if final_url is not None and check_cmp and r is not None:
            # Check each CMP type
            if self.check_cookiebot_presence(r):
                return final_url, QuickCrawlResult.COOKIEBOT
            elif self.check_onetrust_presence(r):
                return final_url, QuickCrawlResult.ONETRUST
            elif self.check_termly_presence(r):
                return final_url, QuickCrawlResult.TERMLY
            else:
                return final_url, QuickCrawlResult.NOCMP
        elif final_url is not None:
            return final_url, QuickCrawlResult.OK
        else:
            return input_domain, QuickCrawlResult.CONNECT_FAIL
    
    def crawl_domains(self, domains: List[str], batches: int = 1) -> Dict[str, List[str]]:
        """
        Crawl a list of domains using multiprocessing.
        
        @param domains: list of domains to crawl
        @param batches: number of batches to split processing into
        @return: dictionary mapping result types to lists of URLs
        """
        results = {
            'cookiebot': [],
            'onetrust': [],
            'termly': [],
            'nocmp': [],
            'failed': [],
            'http_error': [],
            'bot': [],
            'timeout': []
        }
        
        logger.info(f"Starting crawl of {len(domains)} domains with {self.num_threads} threads")
        start_time = time.time()
        
        # Split into batches
        num_sites = len(domains)
        chunksize = max(1, num_sites // batches)
        chunks = [domains[i:min(i+chunksize, num_sites)] for i in range(0, num_sites, chunksize)]
        
        finished_domains = set()
        
        try:
            with ProcessPool(self.num_threads) as pool:
                for batch_num, chunk in enumerate(chunks, 1):
                    logger.info(f"Processing batch {batch_num}/{len(chunks)} ({len(chunk)} domains)")
                    
                    future = pool.map(self.run_reachability_check, chunk, timeout=parse_timeout)
                    it = future.result()
                    
                    processed = 0
                    try:
                        while True:
                            try:
                                final_domain, status_code = next(it)
                            except (CTimeoutError, ProcessExpired) as ex:
                                logger.error(f"Process timeout/crash for domain {processed}: {ex}")
                                results['timeout'].append(chunk[processed])
                                finished_domains.add(chunk[processed])
                                processed += 1
                                continue
                            
                            # Categorize results
                            if status_code == QuickCrawlResult.COOKIEBOT:
                                results['cookiebot'].append(final_domain)
                            elif status_code == QuickCrawlResult.ONETRUST:
                                results['onetrust'].append(final_domain)
                            elif status_code == QuickCrawlResult.TERMLY:
                                results['termly'].append(final_domain)
                            elif status_code == QuickCrawlResult.NOCMP:
                                results['nocmp'].append(final_domain)
                            elif status_code == QuickCrawlResult.BOT:
                                results['bot'].append(final_domain)
                            elif status_code == QuickCrawlResult.HTTP_ERROR:
                                results['http_error'].append(final_domain)
                            else:
                                results['failed'].append(final_domain)
                            
                            finished_domains.add(chunk[processed])
                            processed += 1
                            
                            # Progress reporting
                            if processed % 50 == 0:
                                logger.info(f"Batch {batch_num}: {processed}/{len(chunk)} completed")
                    
                    except StopIteration:
                        logger.info(f"Completed batch {batch_num}: {processed} domains processed")
        
        except KeyboardInterrupt:
            remaining = set(domains) - finished_domains
            logger.warning(f"Crawl interrupted. {len(remaining)} domains not processed.")
            results['uncrawled'] = list(remaining)
        
        elapsed = time.time() - start_time
        logger.info(f"Crawl completed in {elapsed:.2f}s")
        
        return results
    
    def save_results(self, results: Dict[str, List[str]]) -> None:
        """Save crawl results to output files"""
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        
        file_mapping = {
            'cookiebot': 'cookiebot_responses.txt',
            'onetrust': 'onetrust_responses.txt', 
            'termly': 'termly_responses.txt',
            'nocmp': 'nocmp_responses.txt',
            'failed': 'failed_urls.txt',
            'http_error': 'http_responses.txt',
            'bot': 'bot_responses.txt',
            'timeout': 'crawler_timeouts.txt'
        }
        
        for result_type, filename in file_mapping.items():
            if result_type in results:
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'w') as f:
                    for url in results[result_type]:
                        f.write(url + "\n")
                logger.info(f"Saved {len(results[result_type])} {result_type} results to {filepath}")
        
        # Save summary
        summary_path = os.path.join(self.output_dir, "crawl_summary.txt")
        with open(summary_path, 'w') as f:
            f.write("CMP Presence Crawl Summary\n")
            f.write("=" * 30 + "\n\n")
            for result_type, urls in results.items():
                f.write(f"{result_type.capitalize()}: {len(urls)}\n")
        
        logger.info(f"Crawl summary saved to {summary_path}")


# Function for backward compatibility
def run_reachability_check(input_domain: str) -> Tuple[Optional[str], int]:
    """Standalone function for multiprocessing compatibility"""
    crawler = PresenceCrawler()
    return crawler.run_reachability_check(input_domain)
