# Cookie Crawler

A research tool for collecting cookie consent data from websites to analyze GDPR compliance and cookie usage patterns.

## Overview

This project contains web crawlers that automatically detect and extract cookie consent information from websites using popular Consent Management Providers (CMPs).

### Supported CMPs
- **Cookiebot**
- **OneTrust** (includes OptAnon, CookiePro, CookieLaw)
- **Termly**

## Features

- **Fast Presence Detection**: Quickly identify websites using supported CMPs
- **Full Browser Crawling**: Extract detailed cookie and consent data using Firefox
- **Data Analysis**: Process and analyze collected cookie data
- **Multiple Input Formats**: Support for URLs, files, CSV, and pickle files
- **Scalable**: Multi-threaded/multi-process execution

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Cookie-Crawler.git
cd Cookie-Crawler

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### Basic Usage

#### 1. Check Website Presence (Fast)
```bash
# Check if websites use supported CMPs
python scripts/run_presence_crawl.py -n 4 -f data/domains/sample_domains.txt
```

#### 2. Full Consent Crawl (Detailed)
```bash
# Extract full cookie and consent data
python scripts/run_consent_crawl.py all -n 2 -f data/domains/sample_domains.txt
```

#### 3. Simple Browser Crawl
```bash
# Simplified crawling with browser automation
python scripts/run_simple_crawl.py -n 1 -f data/domains/sample_domains.txt --browser
```

## Project Structure

```
├── src/                     # Core source code
│   ├── crawlers/           # Crawler implementations
│   ├── database/           # Database processing tools
│   └── analysis/           # Data analysis utilities
├── scripts/                # Executable scripts
├── config/                 # Configuration files
├── data/                   # Data and results
└── docs/                   # Documentation
```

## Output

### Presence Crawler
Creates files in `./data/results/`:
- `cookiebot_responses.txt` - Sites using Cookiebot
- `onetrust_responses.txt` - Sites using OneTrust
- `termly_responses.txt` - Sites using Termly
- `nocmp_responses.txt` - Sites without supported CMPs
- `failed_urls.txt` - Connection failures

### Consent Crawler
Creates SQLite database with tables:
- `consent_data` - Declared cookies with consent labels
- `javascript_cookies` - Observed browser cookies
- `consent_crawl_results` - Crawl success/failure status

## Requirements

- **Python**: 3.8+
- **Operating System**: Linux (Ubuntu 18.04+) or macOS
- **Memory**: 4GB+ RAM recommended
- **Storage**: Varies by crawl size (databases can be large)

### Dependencies
- Firefox browser (automatically downloaded by webdriver-manager)
- Selenium WebDriver
- Requests library for HTTP operations
