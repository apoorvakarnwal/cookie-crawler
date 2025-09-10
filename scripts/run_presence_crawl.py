#!/usr/bin/env python3
"""
Fast presence crawl to check whether websites use supported CMPs.

Usage:
    run_presence_crawl.py -n <NUM> (-f <fpath> | -u <url> | -p <fpkl> | -c <csvpath>)... [-b <BCOUNT>]
    run_presence_crawl.py -h | --help

Options:
    -n --numthreads <NUM>       Number of worker processes.
    -b --batches <BCOUNT>       Number of batches to split the input into. [default: 1]
    -u --url <u>                Domain string to check for reachability.
    -p --pkl <fpkl>             Path to pickled domains.
    -f --file <fpath>           Path to file containing one domain per line.
    -c --csv <csvpath>          Path to csv containing domains in second column. Separator is ",".
    -h --help                   Display this help message.

Examples:
    python scripts/run_presence_crawl.py -n 4 -f data/domains/sample_domains.txt
    python scripts/run_presence_crawl.py -n 8 -u https://example.com -u https://test.org
"""

import sys
import os
import logging
from docopt import docopt

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from crawlers.shared_utils import retrieve_cmdline_urls, filter_bad_urls_and_sort, setup_output_directory
from crawlers.presence_crawler import PresenceCrawler


def main():
    """Main function for presence crawler"""
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
    num_threads = int(args["--numthreads"])
    batches = int(args.get("--batches", 1))
    
    output_dir = setup_output_directory("./data/results")
    crawler = PresenceCrawler(num_threads=num_threads, output_dir=output_dir)
    
    print(f"Starting presence crawl of {len(filtered_sites)} domains")
    print(f"Using {num_threads} threads and {batches} batches")
    print(f"Output directory: {output_dir}")
    
    try:
        # Run the crawl
        results = crawler.crawl_domains(filtered_sites, batches=batches)
        
        # Save results
        crawler.save_results(results)
        
        # Print summary
        print("\n" + "="*50)
        print("CRAWL SUMMARY")
        print("="*50)
        for result_type, urls in results.items():
            if result_type != 'uncrawled':
                print(f"{result_type.capitalize()}: {len(urls)}")
        print("="*50)
        
        return 0
        
    except KeyboardInterrupt:
        print("\nCrawl interrupted by user")
        return 1
    except Exception as e:
        print(f"Error during crawl: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit(main())
