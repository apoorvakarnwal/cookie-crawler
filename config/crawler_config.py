"""
Configuration settings for Consent Crawler
"""

import os

# Base configuration
DEFAULT_OUTPUT_DIR = "./data/results"
DEFAULT_NUM_THREADS = 4
DEFAULT_NUM_BROWSERS = 1

# Timeout settings (seconds)
CONNECT_TIMEOUT = 20
LOAD_TIMEOUT = 30
PARSE_TIMEOUT = 120
BROWSER_PAGE_TIMEOUT = 30

# User agent string for HTTP requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"

# Browser profile paths
BROWSER_PROFILES = {
    "accept_all": "./config/browser_profiles/accept_all/",
    "accept_none": "./config/browser_profiles/accept_none/", 
    "without_consentomatic": "./config/browser_profiles/without_consentomatic/"
}

# Firefox preferences for consent crawling
FIREFOX_PREFERENCES = {
    "xpinstall.signatures.required": False,
    "privacy.resistFingerprinting": False,
    "privacy.trackingprotection.pbmode.enabled": False,
    "privacy.trackingprotection.enabled": False,
    "network.cookie.maxNumber": 10000,
    "network.cookie.maxPerHost": 10000,
    "network.cookie.quotaPerHost": 10000,
    "privacy.socialtracking.block_cookies.enabled": False,
    "network.cookie.thirdparty.sessionOnly": False,
    "network.cookie.sameSite.laxByDefault": True,
}

# CMP detection patterns
CMP_PATTERNS = {
    "cookiebot": [
        r"https://consent\.cookiebot\.(com|eu)/",
        r"cb-main\.js"
    ],
    "onetrust": [
        r"https://cdn-apac\.onetrust\.com",
        r"https://cdn-ukwest\.onetrust\.com", 
        r"https://cmp-cdn\.cookielaw\.org",
        r"https://cdn\.cookielaw\.org",
        r"https://optanon\.blob\.core\.windows\.net",
        r"https://cookie-cdn\.cookiepro\.com",
        r"https://cookiepro\.blob\.core\.windows\.net"
    ],
    "termly": [
        r"https://app\.termly\.io/"
    ]
}

# Purpose category mappings
PURPOSE_CATEGORIES = {
    0: "necessary",
    1: "functional", 
    2: "analytics",
    3: "advertising",
    4: "social",
    -1: "unknown"
}

# CMP type mappings
CMP_TYPES = {
    0: "cookiebot",
    1: "onetrust", 
    2: "termly",
    -1: "unknown"
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG", 
            "formatter": "standard",
            "filename": os.path.join(DEFAULT_OUTPUT_DIR, "crawler.log"),
            "mode": "a"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}
