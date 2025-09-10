# Cookie-Crawler - Complete Usage Guide

## Table of Contents
1. [Setup and Installation](#setup-and-installation)
2. [Understanding the Codebase](#understanding-the-codebase)
3. [Usage Examples](#usage-examples)
4. [Advanced Configuration](#advanced-configuration)
5. [Output Analysis](#output-analysis)
6. [Troubleshooting](#troubleshooting)

## Setup and Installation

### Prerequisites
- **macOS** (tested on macOS 15.0+)
- **Python 3.8+** (tested with Python 3.9.19)
- **Firefox browser** (will be managed automatically by webdriver-manager)
- **4GB+ RAM** (recommended for browser crawling)

### 1. Virtual Environment Setup (Recommended)

```bash
# Navigate to the project directory
cd /path/to/cookie-data-crawler

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify Python version
python --version  # Should show Python 3.8+
```

### 2. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Install the package in development mode
pip install -e .

# Verify installation
python -c "import selenium; print('Selenium version:', selenium.__version__)"
```

## Understanding the Codebase

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Cookie Data Crawler                     │
├─────────────────────────────────────────────────────────────┤
│  Entry Points (scripts/)                                   │
│  ├── run_presence_crawl.py   # Fast HTTP-based detection   │
│  ├── run_consent_crawl.py    # Full browser-based crawl    │
│  └── run_simple_crawl.py     # Unified interface           │
├─────────────────────────────────────────────────────────────┤
│  Core Crawlers (src/crawlers/)                             │
│  ├── presence_crawler.py     # HTTP requests + regex       │
│  ├── consent_crawler.py      # Selenium + Firefox          │
│  └── shared_utils.py         # Common utilities            │
├─────────────────────────────────────────────────────────────┤
│  Data Processing (src/database/ & src/analysis/)           │
│  ├── extract_cookies.py      # Database extraction         │
│  ├── post_process.py         # Data cleanup                │
│  └── cookie_stats.py         # Statistical analysis        │
├─────────────────────────────────────────────────────────────┤
│  Configuration (config/)                                   │
│  ├── crawler_config.py       # Main settings               │
│  └── browser_profiles/       # Firefox profiles            │
└─────────────────────────────────────────────────────────────┘
```

### Code Flow

#### 1. Presence Crawler Flow
```
Input URLs → HTTP Requests → Regex Matching → CMP Detection → Results Files
```

#### 2. Browser Crawler Flow
```
Input URLs → Firefox Launch → Page Load → Cookie Collection → CMP Detection → SQLite Database
```

### Supported CMPs (Consent Management Providers)
- **Cookiebot**: consent.cookiebot.com, cb-main.js
- **OneTrust**: onetrust.com, cookielaw.org, optanon, cookiepro
- **Termly**: app.termly.io

## Usage Examples

### 1. Quick CMP Detection (Fast)

```bash
# Activate virtual environment
source venv/bin/activate

# Check sample domains for CMP presence
python scripts/run_presence_crawl.py -n 4 -f data/domains/sample_domains.txt

# Check specific URLs
python scripts/run_presence_crawl.py -n 2 -u cnn.com -u github.com

# Check with custom domain list
python scripts/run_presence_crawl.py -n 4 -f data/domains/test_domains.txt
```

**Output**: Creates categorized files in `./data/results/`:
- `cookiebot_responses.txt` - Sites using Cookiebot
- `onetrust_responses.txt` - Sites using OneTrust
- `termly_responses.txt` - Sites using Termly
- `nocmp_responses.txt` - Sites without supported CMPs
- `failed_urls.txt` - Connection failures

### 2. Full Browser Crawling (Detailed)

```bash
# Basic browser crawl (visible Firefox)
python scripts/run_simple_crawl.py -n 1 -u github.com --browser

# Headless browser crawl (recommended for automation)
python scripts/run_simple_crawl.py -n 1 -f data/domains/test_domains.txt --browser --headless

# Multiple domains with consent analysis
python scripts/run_consent_crawl.py all -n 1 -f data/domains/sample_domains.txt
```

**Output**: Creates SQLite database with:
- `crawl_results` table - Success/failure status
- `cookies` table - Collected cookie data
- `consent_data` table - CMP consent information

### 3. Data Analysis and Extraction

```bash
# Extract cookies from database
python src/database/extract_cookies.py ./data/results/consent_crawl_*.sqlite

# Generate statistics
python src/analysis/cookie_stats.py extracted_cookies.json --summary

# Process and clean database
python src/database/post_process.py ./data/results/consent_crawl_*.sqlite
```

### 4. Programmatic Usage

```python
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, 'src')

from crawlers.presence_crawler import PresenceCrawler
from crawlers.consent_crawler import ConsentCrawler

# Quick presence check
presence_crawler = PresenceCrawler(num_threads=4)
domains = ["github.com", "stackoverflow.com", "cnn.com"]
results = presence_crawler.crawl_domains(domains)
presence_crawler.save_results(results)

# Full browser crawl
consent_crawler = ConsentCrawler(num_browsers=1, headless=True)
detailed_results = consent_crawler.crawl_domains(domains[:2])
print(f"Database saved to: {consent_crawler.db_path}")
```

## Advanced Configuration

### 1. Browser Configuration

Edit `config/crawler_config.py`:

```python
# Timeout settings (seconds)
CONNECT_TIMEOUT = 20
LOAD_TIMEOUT = 30
BROWSER_PAGE_TIMEOUT = 30

# Firefox preferences
FIREFOX_PREFERENCES = {
    "network.cookie.maxNumber": 10000,
    "privacy.trackingprotection.enabled": False,
    # Add custom preferences here
}
```

### 2. Custom Domain Lists

Create domain files in `data/domains/`:

```text
# my_domains.txt
# Format: one domain per line
# Comments start with #

example.com
test-site.org
my-website.com
```

### 3. Performance Tuning

```bash
# For presence crawling
python scripts/run_presence_crawl.py -n 8 -b 4 -f domains.txt
# -n: number of threads (CPU cores × 2)
# -b: number of batches

# For browser crawling (use fewer browsers)
python scripts/run_simple_crawl.py -n 1 --browser --headless -f domains.txt
# Note: More than 2 browsers can cause resource issues
```

## Output Analysis

### 1. Presence Crawl Results

```bash
# View CMP distribution
cat data/results/crawl_summary.txt

# Check specific CMP users
head -10 data/results/onetrust_responses.txt
head -10 data/results/cookiebot_responses.txt

# Check failed crawls
cat data/results/failed_urls.txt
cat data/results/bot_responses.txt
```

### 2. Browser Crawl Analysis

```bash
# Basic database query
sqlite3 data/results/consent_crawl_*.sqlite "SELECT domain, cmp_type, cookies_collected FROM crawl_results;"

# Extract and analyze cookies
python src/database/extract_cookies.py data/results/consent_crawl_*.sqlite
python src/analysis/cookie_stats.py extracted_cookies.json

# View detailed statistics
cat database_stats.json | python -m json.tool
```

### 3. Generate Reports

```python
# Custom analysis script
import json
import sqlite3

# Load extracted data
with open('extracted_cookies.json', 'r') as f:
    data = json.load(f)

# Print summary
stats = data['statistics']
print(f"Total unique cookies: {stats['total_unique_cookies']}")
print(f"Matched with consent: {stats['matched_cookies']}")
print(f"Analysis date: {stats['extraction_date']}")
```

## Troubleshooting

### Common Issues

#### 1. Firefox/Selenium Issues
```bash
# Problem: "executable_path" error
# Solution: Already fixed in the codebase (uses Service class)

# Problem: Firefox not found
# Solution: Install Firefox or let webdriver-manager handle it
brew install firefox  # macOS with Homebrew
```

#### 2. Permission/Access Issues
```bash
# Problem: Permission denied on virtual environment
# Solution: Check directory permissions
chmod -R 755 venv/

# Problem: Cannot write to results directory
# Solution: Create directory manually
mkdir -p data/results
chmod 755 data/results
```

#### 3. Memory/Performance Issues
```bash
# Problem: Browser crawl consuming too much memory
# Solution: Reduce number of browsers and use headless mode
python scripts/run_simple_crawl.py -n 1 --browser --headless

# Problem: Presence crawl timing out
# Solution: Reduce batch size and increase timeout
# Edit config/crawler_config.py: CONNECT_TIMEOUT = 30
```

#### 4. Network/Connection Issues
```bash
# Problem: Many "failed_urls"
# Solution: Check network connectivity and reduce thread count
python scripts/run_presence_crawl.py -n 2 -f domains.txt

# Problem: "Bot detection" responses
# Solution: Add delays or use different user agents
# Edit config/crawler_config.py: USER_AGENT = "..."
```

### Debug Mode

Enable debug logging by editing scripts:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help

1. **Check logs**: `data/results/consent_crawl.log`
2. **Verify setup**: Run `examples/basic_crawl.py`
3. **Test components**: Use individual crawler classes
4. **Monitor resources**: Use Activity Monitor (macOS) during crawls

## Best Practices

### 1. Ethical Usage
- Respect `robots.txt` files
- Use reasonable delays between requests
- Don't overload servers
- Follow website terms of service

### 2. Data Management
- Regularly clean up old result files
- Archive databases before analysis
- Use meaningful filenames for domain lists

### 3. Performance Optimization
- Use presence crawl for initial screening
- Use browser crawl only for detailed analysis
- Run browser crawls during off-peak hours
- Monitor memory usage with large domain lists

### 4. Result Validation
- Cross-check presence and browser results
- Manually verify CMP detections
- Review failed crawls for patterns

## Example Workflow

```bash
# 1. Set up environment
source venv/bin/activate

# 2. Create domain list
echo -e "github.com\nstackoverflow.com\ncnn.com\nbbc.com" > my_test_domains.txt

# 3. Quick CMP check
python scripts/run_presence_crawl.py -n 4 -f my_test_domains.txt

# 4. Detailed analysis of CMP users
python scripts/run_simple_crawl.py -n 1 -f data/results/onetrust_responses.txt --browser --headless

# 5. Extract and analyze data
python src/database/extract_cookies.py data/results/consent_crawl_*.sqlite
python src/analysis/cookie_stats.py extracted_cookies.json

# 6. Review results
cat database_stats.json
```

This guide provides everything needed to successfully use the Cookie Data Crawler on macOS in an isolated environment!
