# Usage Guide

This guide explains how to use the Cookie-Crawler for different research scenarios.

## Quick Start

### 1. Presence Crawl (Fast)

Check which websites use supported CMPs:

```bash
# Crawl domains from a file
python scripts/run_presence_crawl.py -n 4 -f data/domains/sample_domains.txt

# Crawl specific URLs
python scripts/run_presence_crawl.py -n 4 -u cnn.com -u bbc.com -u github.com

# Results will be saved to data/results/
```

### 2. Consent Crawl (Detailed)

Collect actual cookies and consent data:

```bash
# Browser-based crawl (slower but comprehensive)
python scripts/run_consent_crawl.py -n 1 -f data/domains/sample_domains.txt

# Run in headless mode
python scripts/run_consent_crawl.py -n 1 -f data/domains/sample_domains.txt --headless
```

### 3. Simple Unified Crawl

Use the simplified interface:

```bash
# Fast mode (requests-only)
python scripts/run_simple_crawl.py -n 4 -f data/domains/sample_domains.txt

# Browser mode
python scripts/run_simple_crawl.py -n 1 -f data/domains/sample_domains.txt --browser
```

## Input Formats

### Domain Files
```
# One domain per line
cnn.com
bbc.com
github.com

# Comments start with #
# example.com
```

### CSV Files
```
1,cnn.com
2,bbc.com
3,github.com
```

### Command Line URLs
```bash
python scripts/run_presence_crawl.py -n 4 -u cnn.com -u bbc.com
```

## Output Structure

### Presence Crawl Output

Results saved to `data/results/`:
- `cookiebot_responses.txt` - Sites using Cookiebot
- `onetrust_responses.txt` - Sites using OneTrust  
- `termly_responses.txt` - Sites using Termly
- `nocmp_responses.txt` - Sites without supported CMPs
- `failed_urls.txt` - Connection failures
- `bot_responses.txt` - Bot detection responses
- `crawl_summary.txt` - Summary statistics

### Consent Crawl Output

Creates SQLite database with tables:
- `crawl_results` - Overall crawl status per domain
- `cookies` - Collected browser cookies
- `consent_data` - Extracted consent information

## Data Processing

### Extract Cookie Data

```bash
# Extract cookies from database
python src/database/extract_cookies.py crawl_data.sqlite -o extracted_cookies.json

# Include unmatched cookies
python src/database/extract_cookies.py crawl_data.sqlite --include-unmatched
```

### Analyze Results

```bash
# Generate statistics report
python src/analysis/cookie_stats.py extracted_cookies.json -o analysis_report.json

# Print summary to console
python src/analysis/cookie_stats.py extracted_cookies.json --summary
```

### Post-process Database

```bash
# Clean and analyze database
python src/database/post_process.py crawl_data.sqlite --clean --views -o report.json
```

## Advanced Usage

### Custom Configuration

Create custom configuration:

```python
# config/custom_config.py
from config.crawler_config import *

# Override settings
DEFAULT_NUM_THREADS = 8
CONNECT_TIMEOUT = 30
```

Use in scripts:
```python
import sys
sys.path.append('config')
from custom_config import *
```

### Programmatic Usage

```python
from src.crawlers.presence_crawler import PresenceCrawler
from src.crawlers.consent_crawler import ConsentCrawler

# Presence crawl
crawler = PresenceCrawler(num_threads=4)
results = crawler.crawl_domains(['cnn.com', 'bbc.com'])
crawler.save_results(results)

# Consent crawl
crawler = ConsentCrawler(num_browsers=1, headless=True)
results = crawler.crawl_domains(['github.com'])
```

### Batch Processing

Process large domain lists:

```bash
# Split large file and process in batches
python scripts/run_presence_crawl.py -n 8 -f large_domains.txt -b 10
```

### Resume Interrupted Crawls

```bash
# Use existing database to continue
python scripts/run_consent_crawl.py -n 1 -f remaining_domains.txt -d existing_crawl.sqlite
```

## Performance Optimization

### Presence Crawl
- Use 4-8 threads for good performance
- More threads = faster but higher resource usage
- Batch processing for very large lists

### Consent Crawl  
- Use 1-2 browsers maximum (resource intensive)
- Headless mode for better performance
- Consider running overnight for large datasets

### System Resources
```bash
# Monitor resource usage
htop
free -h
df -h
```

## Research Workflows

### 1. Large-Scale Study
```bash
# Step 1: Quick filtering
python scripts/run_presence_crawl.py -n 8 -f all_domains.txt

# Step 2: Crawl promising sites
python scripts/run_consent_crawl.py -n 2 -f cookiebot_responses.txt --headless

# Step 3: Analysis
python src/database/extract_cookies.py results.sqlite
python src/analysis/cookie_stats.py extracted_cookies.json
```

### 2. CMP Comparison
```bash
# Crawl each CMP type separately
python scripts/run_consent_crawl.py -n 1 -f cookiebot_sites.txt
python scripts/run_consent_crawl.py -n 1 -f onetrust_sites.txt
python scripts/run_consent_crawl.py -n 1 -f termly_sites.txt

# Compare results
python src/analysis/cookie_stats.py data1.json
python src/analysis/cookie_stats.py data2.json
```

### 3. Longitudinal Study
```bash
# Regular crawls
python scripts/run_consent_crawl.py -n 1 -f target_sites.txt
# Schedule with cron for regular collection
```

## Best Practices

### Rate Limiting
- Use reasonable delays between requests
- Respect robots.txt files
- Don't overload target servers

### Data Management
- Regular backups of databases
- Compress large result files
- Clean up temporary files

### Legal Compliance
- Only collect data for legitimate research
- Respect website terms of service
- Consider GDPR implications for data storage

### Reproducibility
- Document crawler versions and settings
- Save domain lists and configuration
- Version control analysis scripts

## Troubleshooting

### Common Issues

#### Slow Performance
```bash
# Reduce parallelism
python scripts/run_presence_crawl.py -n 2 -f domains.txt

# Use batches
python scripts/run_presence_crawl.py -n 4 -f domains.txt -b 5
```

#### Memory Issues
```bash
# Run headless
python scripts/run_consent_crawl.py -n 1 -f domains.txt --headless

# Reduce browser count
python scripts/run_consent_crawl.py -n 1 -f domains.txt
```

#### Connection Issues
- Check internet connection
- Use VPN if geo-blocked
- Verify domain list format

#### Browser Issues
```bash
# Update webdriver
python -c "from webdriver_manager.firefox import GeckoDriverManager; GeckoDriverManager().install()"

# Check Firefox installation
firefox --version
```

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Getting Help

- Check [Installation Guide](installation.md)
- Review [Examples](../examples/)
