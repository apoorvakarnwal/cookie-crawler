# Project Structure

## Complete File Structure

```
cookie-collection/
├── README.md                           # Main project documentation
├── requirements.txt                    # Python dependencies
├── setup.py                           # Package installation script
├── LICENSE                            # GPL v3 license
├── .gitignore                         # Git ignore rules
├── PROJECT_STRUCTURE.md               # This file
│
├── src/                               # Source code
│   ├── __init__.py                    # Package initialization
│   ├── crawlers/                      # Crawler modules
│   │   ├── __init__.py               # Crawler package init
│   │   ├── shared_utils.py           # Shared utilities
│   │   ├── presence_crawler.py       # Fast HTTP-based presence check
│   │   └── consent_crawler.py        # Browser-based consent crawler
│   ├── database/                      # Database processing
│   │   ├── __init__.py               # Database package init
│   │   ├── extract_cookies.py        # Extract cookies from DB
│   │   └── post_process.py           # Database cleanup and analysis
│   └── analysis/                      # Data analysis
│       ├── __init__.py               # Analysis package init
│       └── cookie_stats.py           # Cookie statistics analysis
│
├── scripts/                           # Executable scripts
│   ├── run_presence_crawl.py         # Main presence crawler script
│   ├── run_consent_crawl.py          # Main consent crawler script
│   └── run_simple_crawl.py           # Unified simple interface
│
├── config/                            # Configuration files
│   ├── crawler_config.py             # Main configuration settings
│   └── browser_profiles/             # Firefox browser profiles
│       ├── accept_all/               # Profile that accepts all cookies
│       ├── accept_none/              # Profile that rejects all cookies
│       └── without_consentomatic/    # Profile without automation
│
├── data/                              # Data directory
│   ├── domains/                      # Domain lists
│   │   └── sample_domains.txt        # Sample domains for testing
│   ├── results/                      # Crawler output (created at runtime)
│   └── examples/                     # Example datasets
│
├── examples/                          # Usage examples
│   └── basic_crawl.py                # Demonstrates programmatic usage
│
└── docs/                             # Documentation
    ├── installation.md               # Installation instructions
    └── usage.md                      # Usage guide
```

## Key Features

### 🚀 **Simple Installation**
```bash

pip install -e .
```

### ⚡ **Easy Usage**
```bash
# Fast presence check
python scripts/run_presence_crawl.py -n 4 -f data/domains/sample_domains.txt

# Full browser crawl
python scripts/run_consent_crawl.py -n 1 -f data/domains/sample_domains.txt

# Unified interface
python scripts/run_simple_crawl.py -n 4 -f data/domains/sample_domains.txt
```

### 📊 **Data Analysis**
```bash
# Extract cookies from database
python src/database/extract_cookies.py crawl_data.sqlite

# Analyze cookie statistics  
python src/analysis/cookie_stats.py extracted_cookies.json --summary
```

## Supported CMPs

- **Cookiebot** - Consent platform used by many European sites
- **OneTrust** - Includes OptAnon, CookiePro, and CookieLaw domains
- **Termly** - Privacy management platform

## Output Data

### Presence Crawler
- Categorized domain lists by CMP type
- Connection success/failure reports
- Bot detection responses

### Consent Crawler  
- SQLite database with cookies and consent data
- Structured JSON export for analysis
- Comprehensive crawl statistics

### Analysis Tools
- Cookie name and value pattern analysis
- Security attribute statistics (Secure, HttpOnly, SameSite)
- Purpose category consistency analysis
- CMP comparison reports

## Simplified vs Original

| Aspect | Original | Simplified |
|--------|----------|------------|
| **Size** | ~350 files, 50MB+ | ~25 files, <1MB |
| **Setup** | Complex OpenWPM installation | `pip install -e .` |
| **Dependencies** | Full OpenWPM stack | Essential packages only |
| **Structure** | Research prototype layout | Standard Python package |
| **Documentation** | Scattered README files | Organized docs/ folder |
| **Examples** | Hidden in comments | Clear examples/ directory |
| **Configuration** | Hardcoded in scripts | Centralized config/ |

## What Was Removed

- Full OpenWPM repository (kept only essential functionality)
- Large binary files and sample databases
- Duplicate domain sources and utilities
- Legacy code and unused features
- Development artifacts and logs

## What Was Added

- Standard Python package structure
- Comprehensive documentation
- Working examples
- Centralized configuration
- Clean installation process
- Simplified command-line interface

## Getting Started

1. **Install**: Follow [docs/installation.md](docs/installation.md)
2. **Run Examples**: Try [examples/basic_crawl.py](examples/basic_crawl.py)
3. **Read Usage**: Check [docs/usage.md](docs/usage.md)
4. **Test**: Use [data/domains/sample_domains.txt](data/domains/sample_domains.txt)

## Benefits

✅ **90% smaller** repository size
✅ **Professional** Python package structure  
✅ **Simple** installation and setup
✅ **Clear** documentation and examples
✅ **Modular** design for easy extension
✅ **Standard** development practices
✅ **Ready** for GitHub and PyPI publication

This simplified version maintains all the core functionality while making it much more accessible and maintainable for research use.
