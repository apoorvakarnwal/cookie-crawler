#!/usr/bin/env python3
"""
Browser-based crawler that collects detailed cookie and consent data.

Usage:
    run_consent_crawl.py -n <NUM> (-f <fpath> | -u <url> | -p <fpkl> | -c <csvpath>)... [--headless]
    run_consent_crawl.py -h | --help

Options:
    -n --num_browsers <NUM>     Number of browser instances to use (recommend 1-2).
    -u --url <u>                URL string to crawl.
    -p --pkl <fpkl>             Path to pickled list of urls to crawl.
    -f --file <fpath>           Path to file containing one URL per line.
    -c --csv <csvpath>          Path to csv containing domains in second column.
    --headless                  Run browsers in headless mode.
    -h --help                   Display this help message.

Examples:
    python scripts/run_consent_crawl.py -n 1 -f data/domains/sample_domains.txt
    python scripts/run_consent_crawl.py -n 2 -u https://example.com --headless
"""

import sys
import os
import logging
from docopt import docopt

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from crawlers.shared_utils import retrieve_cmdline_urls, filter_bad_urls_and_sort, setup_output_directory
from crawlers.consent_crawler import ConsentCrawler


def main():
    """Main function for consent crawler"""
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
    
    # Set up crawler
    num_browsers = int(args["--num_browsers"])
    headless = args.get("--headless", False)
    
    output_dir = setup_output_directory("./data/results")
    
    print(f"Starting consent crawl of {len(filtered_sites)} domains")
    print(f"Using {num_browsers} browser(s), headless: {headless}")
    print(f"Output directory: {output_dir}")
    print("\nNote: This may take a while as each domain is crawled with a real browser...")
    
    try:
        crawler = ConsentCrawler(
            num_browsers=num_browsers,
            headless=headless,
            output_dir=output_dir
        )
        
        # Run the crawl
        results = crawler.crawl_domains(filtered_sites)
        
        # Print summary
        print("\n" + "="*50)
        print("CONSENT CRAWL SUMMARY")
        print("="*50)
        print(f"Total domains: {results['total_domains']}")
        print(f"Successful crawls: {results['successful_crawls']}")
        print(f"Failed crawls: {results['failed_crawls']}")
        print(f"Total cookies collected: {results['total_cookies']}")
        print(f"Domains with consent data: {results['domains_with_consent_data']}")
        print(f"Crawl time: {results['crawl_time_seconds']:.2f} seconds")
        
        if results.get('cmp_types'):
            print(f"\nCMP Distribution:")
            for cmp_type, count in results['cmp_types'].items():
                print(f"  {cmp_type}: {count}")
        
        print(f"\nDatabase location: {crawler.db_path}")
        print("="*50)
        
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
