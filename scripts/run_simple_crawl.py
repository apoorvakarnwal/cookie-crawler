#!/usr/bin/env python3
"""
Simplified crawler that can run in fast mode (requests-only) or browser mode.

Usage:
    run_simple_crawl.py -n <NUM> (-f <fpath> | -u <url> | -p <fpkl> | -c <csvpath>)... [--browser] [--headless]
    run_simple_crawl.py -h | --help

Options:
    -n --numthreads <NUM>       Number of worker processes/threads.
    -u --url <u>                Domain string to check.
    -p --pkl <fpkl>             Path to pickled domains.
    -f --file <fpath>           Path to file containing one domain per line.
    -c --csv <csvpath>          Path to csv containing domains in second column.
    --browser                   Use real browser (Selenium + Firefox) instead of requests.
    --headless                  When using --browser, run Firefox in headless mode.
    -h --help                   Display this help message.

Examples:
    # Fast mode (requests-only)
    python scripts/run_simple_crawl.py -n 4 -f data/domains/sample_domains.txt

    # Browser mode (slower but more accurate)
    python scripts/run_simple_crawl.py -n 1 -f data/domains/sample_domains.txt --browser
"""

import sys
import os
import logging
from docopt import docopt

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from crawlers.shared_utils import retrieve_cmdline_urls, filter_bad_urls_and_sort, setup_output_directory
from crawlers.presence_crawler import PresenceCrawler
from crawlers.consent_crawler import ConsentCrawler


def run_fast_mode(domains, num_threads, output_dir):
    """Run fast presence-only crawl"""
    print(f"Running in FAST mode with {num_threads} threads")
    
    crawler = PresenceCrawler(num_threads=num_threads, output_dir=output_dir)
    results = crawler.crawl_domains(domains)
    crawler.save_results(results)
    
    return results


def run_browser_mode(domains, num_browsers, headless, output_dir):
    """Run browser-based crawl with cookie collection"""
    print(f"Running in BROWSER mode with {num_browsers} browser(s)")
    print(f"Headless mode: {headless}")
    
    crawler = ConsentCrawler(
        num_browsers=num_browsers,
        headless=headless,
        output_dir=output_dir
    )
    results = crawler.crawl_domains(domains)
    
    return results, crawler.db_path


def main():
    """Main function for simple crawler"""
    args = docopt(__doc__)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Retrieve and process URLs
    sites = retrieve_cmdline_urls(args)
    filtered_sites = filter_bad_urls_and_sort(sites)
    
    if not filtered_sites:
        print("Error: No valid domains to crawl. Please check your input.", file=sys.stderr)
        return 1
    
    # Configuration
    num_threads = int(args["--numthreads"])
    browser_mode = args.get("--browser", False)
    headless = args.get("--headless", False)
    
    output_dir = setup_output_directory("./data/results")
    
    print(f"Starting crawl of {len(filtered_sites)} domains")
    print(f"Output directory: {output_dir}")
    
    if browser_mode and num_threads > 2:
        print("Warning: Using more than 2 browsers simultaneously may consume significant resources.")
        print("Consider reducing the number of threads for browser mode.")
    
    try:
        if browser_mode:
            # Browser-based crawl
            results, db_path = run_browser_mode(filtered_sites, num_threads, headless, output_dir)
            
            print("\n" + "="*50)
            print("BROWSER CRAWL SUMMARY")
            print("="*50)
            print(f"Total domains: {results['total_domains']}")
            print(f"Successful crawls: {results['successful_crawls']}")
            print(f"Failed crawls: {results['failed_crawls']}")
            print(f"Total cookies collected: {results['total_cookies']}")
            print(f"Domains with consent data: {results['domains_with_consent_data']}")
            
            if results.get('cmp_types'):
                print(f"\nCMP Distribution:")
                for cmp_type, count in results['cmp_types'].items():
                    print(f"  {cmp_type}: {count}")
            
            print(f"\nDatabase: {db_path}")
            print("="*50)
            
        else:
            # Fast presence crawl
            results = run_fast_mode(filtered_sites, num_threads, output_dir)
            
            print("\n" + "="*50)
            print("PRESENCE CRAWL SUMMARY")
            print("="*50)
            for result_type, urls in results.items():
                if result_type != 'uncrawled':
                    print(f"{result_type.capitalize()}: {len(urls)}")
            print("="*50)
        
        print(f"\nResults saved to: {output_dir}")
        return 0
        
    except KeyboardInterrupt:
        print("\nCrawl interrupted by user")
        return 1
    except Exception as e:
        print(f"Error during crawl: {e}", file=sys.stderr)
        logging.exception("Detailed error information:")
        return 1


if __name__ == "__main__":
    exit(main())
