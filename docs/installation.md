# Installation Guide

This guide will help you install and set up the  Consent Crawler.

## Requirements

### System Requirements
- **Operating System**: Linux (Ubuntu 18.04+), macOS, or Windows 10+
- **Python**: 3.8 or higher
- **Memory**: 4GB+ RAM recommended
- **Storage**: 1GB+ free space (more for large crawls)

### Browser Requirements
- **Firefox**: Will be automatically downloaded by webdriver-manager
- **Gecko Driver**: Automatically managed by webdriver-manager

## Installation Options

### Option 1: Package Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/Cookie-Crawler.git
cd Cookie-Crawler

# Install as a package
pip install -e .
```

### Option 2: Direct Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/Cookie-Crawler.git
cd Cookie-Crawler

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Virtual Environment (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/Cookie-Crawler.git
cd Cookie-Crawler

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Verification

Test your installation by running:

```bash
# Test presence crawler
python scripts/run_presence_crawl.py -n 2 -u github.com -u stackoverflow.com

# Test package import
python -c "from src.crawlers import PresenceCrawler; print('Installation successful!')"
```

## Platform-Specific Notes

### Linux (Ubuntu/Debian)

Install system dependencies:
```bash
sudo apt update
sudo apt install python3 python3-pip firefox
```

For headless mode, install virtual display:
```bash
sudo apt install xvfb
pip install pyvirtualdisplay
```

### macOS

Install using Homebrew:
```bash
brew install python firefox
pip install -r requirements.txt
```

### Windows

1. Install Python 3.8+ from [python.org](https://python.org)
2. Install Firefox from [mozilla.org](https://mozilla.org)
3. Run installation commands in Command Prompt or PowerShell

## Troubleshooting

### Common Issues

#### 1. Firefox/Gecko Driver Issues
```bash
# Clear webdriver cache
python -c "from webdriver_manager.firefox import GeckoDriverManager; GeckoDriverManager().install()"
```

#### 2. Permission Errors
```bash
# Install with user permissions
pip install --user -r requirements.txt
```

#### 3. SSL Certificate Issues
```bash
# Upgrade certificates
pip install --upgrade certifi
```

#### 4. Memory Issues
- Reduce number of parallel browsers/threads
- Use headless mode for browser crawling
- Increase system swap space

### Advanced Configuration

#### Custom Firefox Profile
```bash
# Copy browser profile to config directory
cp -r /path/to/firefox/profile config/browser_profiles/custom/
```

#### Environment Variables
```bash
export COOKIE_OUTPUT_DIR="/path/to/output"
export COOKIE_THREADS=8
```

## Development Installation

For contributors and developers:

```bash
# Clone with development dependencies
git clone https://github.com/yourusername/Cookie-Crawler.git
cd Cookie-Crawler

# Install with development extras
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/
```

## Docker Installation (Optional)

```dockerfile
FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    firefox-esr \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "scripts/run_presence_crawl.py", "--help"]
```

```bash
# Build and run
docker build -t cookie-crawler .
docker run cookie-crawler
```

## Next Steps

After installation:
1. Read the [Usage Guide](usage.md)
2. Try the [Basic Examples](../examples/basic_crawl.py)
3. Check the [Configuration](../config/crawler_config.py)

## Getting Help

If you encounter issues:
1. Check this troubleshooting section
2. Search existing [GitHub Issues](https://github.com/yourusername/Cookie-Crawler/issues)
3. Create a new issue with your system details and error messages
