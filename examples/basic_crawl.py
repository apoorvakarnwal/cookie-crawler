#!/usr/bin/env python3
"""
This example shows how to use the crawler programmatically.
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from crawlers.presence_crawler import PresenceCrawler
from crawlers.consent_crawler import ConsentCrawler


def example_presence_crawl():
    """Example of running a presence crawl"""
    print("="*50)
    print("PRESENCE CRAWL EXAMPLE")
    print("="*50)
    
    # Sample domains to test
    domains = [
        "cnn.com",
        "bbc.com", 
        "github.com",
        "stackoverflow.com"
    ]
    
    # Create crawler
    crawler = PresenceCrawler(num_threads=2, output_dir="./examples/output")
    
    # Run crawl
    results = crawler.crawl_domains(domains)
    
    # Print results
    print("\nResults:")
    for result_type, urls in results.items():
        if urls:
            print(f"{result_type}: {len(urls)} sites")
            for url in urls[:3]:  # Show first 3
                print(f"  - {url}")
            if len(urls) > 3:
                print(f"  ... and {len(urls) - 3} more")
    
    # Save results
    crawler.save_results(results)
    print(f"\nResults saved to: {crawler.output_dir}")


def example_consent_crawl():
    """Example of running a consent crawl"""
    print("\n" + "="*50)
    print("CONSENT CRAWL EXAMPLE")
    print("="*50)
    
    # Sample domains (fewer for browser crawl)
    domains = [
        "github.com",
        "stackoverflow.com"
    ]
    
    print("Running browser-based crawl (this may take a while)...")
    
    # Create crawler
    crawler = ConsentCrawler(
        num_browsers=1,
        headless=True,  # Run headless for example
        output_dir="./examples/output"
    )
    
    # Run crawl
    results = crawler.crawl_domains(domains)
    
    # Print results
    print("\nResults:")
    print(f"Total domains: {results['total_domains']}")
    print(f"Successful: {results['successful_crawls']}")
    print(f"Failed: {results['failed_crawls']}")
    print(f"Total cookies: {results['total_cookies']}")
    print(f"Domains with consent data: {results['domains_with_consent_data']}")
    
    if results.get('cmp_types'):
        print("CMP types found:")
        for cmp_type, count in results['cmp_types'].items():
            print(f"  {cmp_type}: {count}")
    
    print(f"\nDatabase saved to: {crawler.db_path}")


def example_data_analysis():
    """Example of analyzing crawl data"""
    print("\n" + "="*50)
    print("DATA ANALYSIS EXAMPLE")
    print("="*50)
    
    # This would analyze data from a previous crawl
    db_path = "./examples/output/consent_crawl_*.sqlite"
    
    # Note: This is a simplified example
    # In practice, you would use the database processing modules
    print("To analyze crawl data:")
    print(f"1. Extract cookies: python src/database/extract_cookies.py {db_path}")
    print("2. Analyze data: python src/analysis/cookie_stats.py extracted_cookies.json")
    print("3. Generate report: python src/database/post_process.py {db_path}")


def main():
    """Run all examples"""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create output directory
    os.makedirs("./examples/output", exist_ok=True)
    
    print("Cookie - Crawler - Basic Examples")
    print("This will demonstrate the main crawler functionality.")
    print("Note: The consent crawl requires Firefox to be installed.")
    
    try:
        # Run presence crawl example
        example_presence_crawl()
        
        # Ask user if they want to run browser crawl
        response = input("\nRun browser-based consent crawl example? (y/N): ")
        if response.lower().startswith('y'):
            example_consent_crawl()
        else:
            print("Skipping browser crawl example.")
        
        # Show analysis example
        example_data_analysis()
        
        print("\n" + "="*50)
        print("EXAMPLES COMPLETED")
        print("="*50)
        print("Check the ./examples/output directory for results.")
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user.")
    except Exception as e:
        print(f"Error running examples: {e}")
        logging.exception("Detailed error:")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
