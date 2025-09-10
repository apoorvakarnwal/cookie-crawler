import logging
import time
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service

logger = logging.getLogger("consent-crawl")


@dataclass
class CrawlResult:
    """Result of a single domain crawl"""
    domain: str
    success: bool
    cmp_type: str
    cookies_collected: int
    consent_data: List[Dict]
    error_message: Optional[str] = None


class ConsentCrawler:
    """Browser-based crawler for collecting cookie consent data"""
    
    def __init__(self, num_browsers: int = 1, headless: bool = False, 
                 output_dir: str = "./data/results"):
        self.num_browsers = num_browsers
        self.headless = headless
        self.output_dir = output_dir
        self.setup_logger()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize database
        self.db_path = os.path.join(output_dir, f"consent_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite")
        self.init_database()
    
    def setup_logger(self):
        """Set up logger for consent crawler"""
        logger.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler
        log_path = os.path.join(self.output_dir, "consent_crawl.log")
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for storing crawl results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN NOT NULL,
                cmp_type TEXT,
                cookies_collected INTEGER DEFAULT 0,
                error_message TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cookies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crawl_id INTEGER,
                name TEXT NOT NULL,
                domain TEXT NOT NULL,
                value TEXT,
                path TEXT,
                expiry DATETIME,
                secure BOOLEAN,
                http_only BOOLEAN,
                same_site TEXT,
                FOREIGN KEY (crawl_id) REFERENCES crawl_results (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consent_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crawl_id INTEGER,
                cookie_name TEXT NOT NULL,
                cookie_domain TEXT NOT NULL,
                purpose_category TEXT,
                purpose_description TEXT,
                cmp_type TEXT,
                FOREIGN KEY (crawl_id) REFERENCES crawl_results (id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")
    
    def create_driver(self) -> webdriver.Firefox:
        """Create and configure Firefox WebDriver"""
        options = FirefoxOptions()
        
        if self.headless:
            options.add_argument("--headless")
        
        # Performance and privacy settings
        options.set_preference("network.cookie.maxNumber", 10000)
        options.set_preference("network.cookie.maxPerHost", 10000)
        options.set_preference("privacy.trackingprotection.enabled", False)
        options.set_preference("privacy.donottrackheader.enabled", False)
        
        # Disable images for faster loading (optional)
        # options.set_preference("permissions.default.image", 2)
        
        try:
            service = Service(GeckoDriverManager().install())
            driver = webdriver.Firefox(
                service=service,
                options=options
            )
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            return driver
        except Exception as e:
            logger.error(f"Failed to create Firefox driver: {e}")
            raise
    
    def detect_cmp_type(self, driver: webdriver.Firefox) -> str:
        """Detect which CMP is being used on the current page"""
        try:
            page_source = driver.page_source.lower()
            
            # Check for Cookiebot
            if "cookiebot" in page_source or "consent.cookiebot" in page_source:
                return "cookiebot"
            
            # Check for OneTrust
            if any(pattern in page_source for pattern in [
                "onetrust", "cookielaw", "optanon", "cookiepro"
            ]):
                return "onetrust"
            
            # Check for Termly
            if "termly" in page_source or "app.termly.io" in page_source:
                return "termly"
            
            return "unknown"
        except Exception as e:
            logger.warning(f"Error detecting CMP type: {e}")
            return "error"
    
    def collect_cookies(self, driver: webdriver.Firefox) -> List[Dict[str, Any]]:
        """Collect all cookies from the current browser session"""
        try:
            cookies = driver.get_cookies()
            logger.debug(f"Collected {len(cookies)} cookies")
            return cookies
        except Exception as e:
            logger.error(f"Error collecting cookies: {e}")
            return []
    
    def extract_consent_data_cookiebot(self, driver: webdriver.Firefox) -> List[Dict[str, Any]]:
        """Extract consent data from Cookiebot CMP"""
        consent_data = []
        try:
            # Look for Cookiebot declaration
            declaration_elements = driver.find_elements(By.CSS_SELECTOR, "[data-cookiefirst-category]")
            
            for element in declaration_elements:
                try:
                    name = element.get_attribute("data-cookiefirst-name") or "unknown"
                    domain = element.get_attribute("data-cookiefirst-domain") or "unknown"
                    category = element.get_attribute("data-cookiefirst-category") or "unknown"
                    purpose = element.text.strip() if element.text else "No description"
                    
                    consent_data.append({
                        "name": name,
                        "domain": domain,
                        "category": category,
                        "purpose": purpose,
                        "cmp": "cookiebot"
                    })
                except Exception as e:
                    logger.warning(f"Error extracting Cookiebot data: {e}")
                    
        except Exception as e:
            logger.warning(f"No Cookiebot consent data found: {e}")
        
        return consent_data
    
    def extract_consent_data_onetrust(self, driver: webdriver.Firefox) -> List[Dict[str, Any]]:
        """Extract consent data from OneTrust CMP"""
        consent_data = []
        try:
            # Look for OneTrust cookie list
            cookie_elements = driver.find_elements(By.CSS_SELECTOR, ".ot-sdk-cookie")
            
            for element in cookie_elements:
                try:
                    name_elem = element.find_element(By.CSS_SELECTOR, ".ot-sdk-cookie-policy-name")
                    category_elem = element.find_element(By.CSS_SELECTOR, ".ot-sdk-cookie-policy-category")
                    
                    name = name_elem.text.strip() if name_elem else "unknown"
                    category = category_elem.text.strip() if category_elem else "unknown"
                    
                    # Try to get domain and purpose
                    domain = element.get_attribute("data-domain") or "unknown"
                    purpose_elem = element.find_element(By.CSS_SELECTOR, ".ot-sdk-cookie-policy-description")
                    purpose = purpose_elem.text.strip() if purpose_elem else "No description"
                    
                    consent_data.append({
                        "name": name,
                        "domain": domain,
                        "category": category,
                        "purpose": purpose,
                        "cmp": "onetrust"
                    })
                except Exception as e:
                    logger.warning(f"Error extracting OneTrust data: {e}")
                    
        except Exception as e:
            logger.warning(f"No OneTrust consent data found: {e}")
        
        return consent_data
    
    def crawl_domain(self, domain: str) -> CrawlResult:
        """Crawl a single domain and collect cookie consent data"""
        logger.info(f"Crawling domain: {domain}")
        
        driver = None
        try:
            # Create browser driver
            driver = self.create_driver()
            
            # Navigate to domain
            if not domain.startswith(("http://", "https://")):
                domain = f"https://{domain}"
            
            driver.get(domain)
            
            # Wait for page to load
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Detect CMP type
            cmp_type = self.detect_cmp_type(driver)
            logger.info(f"Detected CMP: {cmp_type} for {domain}")
            
            # Extract consent data based on CMP type
            consent_data = []
            if cmp_type == "cookiebot":
                consent_data = self.extract_consent_data_cookiebot(driver)
            elif cmp_type == "onetrust":
                consent_data = self.extract_consent_data_onetrust(driver)
            
            # Collect cookies
            cookies = self.collect_cookies(driver)
            
            # Interact with consent banner if present (accept all)
            try:
                # Look for common accept buttons
                accept_selectors = [
                    "[id*='accept']", "[class*='accept']",
                    "[id*='agree']", "[class*='agree']",
                    "[aria-label*='Accept']", "[aria-label*='Agree']"
                ]
                
                for selector in accept_selectors:
                    try:
                        button = driver.find_element(By.CSS_SELECTOR, selector)
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            logger.debug(f"Clicked consent button: {selector}")
                            time.sleep(2)  # Wait for consent processing
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug(f"No consent banner interaction needed: {e}")
            
            # Collect cookies again after consent
            final_cookies = self.collect_cookies(driver)
            
            return CrawlResult(
                domain=domain,
                success=True,
                cmp_type=cmp_type,
                cookies_collected=len(final_cookies),
                consent_data=consent_data
            )
            
        except TimeoutException:
            return CrawlResult(
                domain=domain,
                success=False,
                cmp_type="unknown",
                cookies_collected=0,
                consent_data=[],
                error_message="Page load timeout"
            )
        except Exception as e:
            return CrawlResult(
                domain=domain,
                success=False,
                cmp_type="unknown", 
                cookies_collected=0,
                consent_data=[],
                error_message=str(e)
            )
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def save_crawl_result(self, result: CrawlResult) -> int:
        """Save crawl result to database and return the crawl ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert crawl result
        cursor.execute("""
            INSERT INTO crawl_results (domain, success, cmp_type, cookies_collected, error_message)
            VALUES (?, ?, ?, ?, ?)
        """, (result.domain, result.success, result.cmp_type, 
              result.cookies_collected, result.error_message))
        
        crawl_id = cursor.lastrowid
        
        # Insert consent data
        for consent in result.consent_data:
            cursor.execute("""
                INSERT INTO consent_data (crawl_id, cookie_name, cookie_domain, 
                                        purpose_category, purpose_description, cmp_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (crawl_id, consent.get("name"), consent.get("domain"),
                  consent.get("category"), consent.get("purpose"), consent.get("cmp")))
        
        conn.commit()
        conn.close()
        
        return crawl_id
    
    def crawl_domains(self, domains: List[str]) -> Dict[str, Any]:
        """Crawl multiple domains and return summary statistics"""
        logger.info(f"Starting consent crawl of {len(domains)} domains")
        
        results = {
            "total_domains": len(domains),
            "successful_crawls": 0,
            "failed_crawls": 0,
            "cmp_types": {},
            "total_cookies": 0,
            "domains_with_consent_data": 0
        }
        
        start_time = time.time()
        
        for i, domain in enumerate(domains, 1):
            logger.info(f"Progress: {i}/{len(domains)} - {domain}")
            
            result = self.crawl_domain(domain)
            self.save_crawl_result(result)
            
            # Update statistics
            if result.success:
                results["successful_crawls"] += 1
                results["total_cookies"] += result.cookies_collected
                
                if result.consent_data:
                    results["domains_with_consent_data"] += 1
                
                cmp_type = result.cmp_type
                results["cmp_types"][cmp_type] = results["cmp_types"].get(cmp_type, 0) + 1
            else:
                results["failed_crawls"] += 1
                logger.warning(f"Failed to crawl {domain}: {result.error_message}")
            
            # Small delay between crawls
            time.sleep(1)
        
        elapsed = time.time() - start_time
        results["crawl_time_seconds"] = elapsed
        
        logger.info(f"Crawl completed in {elapsed:.2f}s")
        logger.info(f"Results: {results['successful_crawls']} successful, {results['failed_crawls']} failed")
        
        return results
