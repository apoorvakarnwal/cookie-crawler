import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("cookie-extractor")


class CookieExtractor:
    """Extract and process cookie data from crawl databases"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.setup_logger()
    
    def setup_logger(self):
        """Set up logger"""
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    def extract_cookies_with_consent(self, include_unmatched: bool = False) -> Dict[str, Any]:
        """
        Extract cookies and match them with consent data.
        
        @param include_unmatched: Include cookies without consent data
        @return: Dictionary with extracted cookie data
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()
        
        # Get all crawl results with their cookies and consent data
        query = """
        SELECT 
            cr.id as crawl_id,
            cr.domain,
            cr.cmp_type,
            cr.success,
            c.name as cookie_name,
            c.domain as cookie_domain,
            c.value as cookie_value,
            c.path as cookie_path,
            c.expiry as cookie_expiry,
            c.secure as cookie_secure,
            c.http_only as cookie_http_only,
            c.same_site as cookie_same_site,
            cd.purpose_category,
            cd.purpose_description
        FROM crawl_results cr
        LEFT JOIN cookies c ON cr.id = c.crawl_id
        LEFT JOIN consent_data cd ON (
            cr.id = cd.crawl_id AND 
            c.name = cd.cookie_name AND 
            c.domain = cd.cookie_domain
        )
        WHERE cr.success = 1
        ORDER BY cr.domain, c.name
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        extracted_data = {}
        matched_cookies = 0
        unmatched_cookies = 0
        
        for row in rows:
            if not row['cookie_name']:  # Skip if no cookies found
                continue
            
            # Create unique cookie ID
            cookie_id = f"{row['cookie_domain']}_{row['cookie_name']}"
            
            # Check if we have consent data for this cookie
            has_consent_data = bool(row['purpose_category'])
            
            if not has_consent_data and not include_unmatched:
                unmatched_cookies += 1
                continue
            
            if has_consent_data:
                matched_cookies += 1
            else:
                unmatched_cookies += 1
            
            # Create cookie entry
            cookie_entry = {
                "name": row['cookie_name'],
                "domain": row['cookie_domain'],
                "path": row['cookie_path'] or "/",
                "cmp_origin": self._map_cmp_type(row['cmp_type']),
                "label": self._map_purpose_category(row['purpose_category']),
                "purpose_description": row['purpose_description'] or "",
                "crawl_domain": row['domain'],
                "variable_data": [{
                    "value": row['cookie_value'] or "",
                    "expiry": row['cookie_expiry'] or "",
                    "secure": bool(row['cookie_secure']),
                    "http_only": bool(row['cookie_http_only']),
                    "same_site": row['cookie_same_site'] or "no_restriction"
                }]
            }
            
            # If cookie already exists, append to variable_data
            if cookie_id in extracted_data:
                extracted_data[cookie_id]["variable_data"].append(cookie_entry["variable_data"][0])
            else:
                extracted_data[cookie_id] = cookie_entry
        
        conn.close()
        
        logger.info(f"Extracted {len(extracted_data)} unique cookies")
        logger.info(f"Matched with consent data: {matched_cookies}")
        logger.info(f"Unmatched cookies: {unmatched_cookies}")
        
        return {
            "cookies": extracted_data,
            "statistics": {
                "total_unique_cookies": len(extracted_data),
                "matched_cookies": matched_cookies,
                "unmatched_cookies": unmatched_cookies,
                "extraction_date": datetime.now().isoformat()
            }
        }
    
    def _map_cmp_type(self, cmp_type: Optional[str]) -> int:
        """Map CMP type string to numeric code"""
        mapping = {
            "cookiebot": 0,
            "onetrust": 1,
            "termly": 2
        }
        return mapping.get(cmp_type, -1)
    
    def _map_purpose_category(self, category: Optional[str]) -> int:
        """Map purpose category to numeric label"""
        if not category:
            return -1
        
        category_lower = category.lower()
        
        # Necessary/Essential cookies
        if any(term in category_lower for term in ["necessary", "essential", "required", "strictly"]):
            return 0
        
        # Functional cookies
        elif any(term in category_lower for term in ["functional", "preference", "personalization"]):
            return 1
        
        # Analytics/Performance cookies
        elif any(term in category_lower for term in ["analytics", "performance", "statistics", "measurement"]):
            return 2
        
        # Advertising/Marketing cookies
        elif any(term in category_lower for term in ["advertising", "marketing", "targeting", "ads"]):
            return 3
        
        # Social media cookies
        elif any(term in category_lower for term in ["social", "media"]):
            return 4
        
        # Uncategorized
        else:
            return -1
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get general statistics about the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total crawls
        cursor.execute("SELECT COUNT(*) FROM crawl_results")
        stats["total_crawls"] = cursor.fetchone()[0]
        
        # Successful crawls
        cursor.execute("SELECT COUNT(*) FROM crawl_results WHERE success = 1")
        stats["successful_crawls"] = cursor.fetchone()[0]
        
        # Failed crawls
        cursor.execute("SELECT COUNT(*) FROM crawl_results WHERE success = 0")
        stats["failed_crawls"] = cursor.fetchone()[0]
        
        # CMP type distribution
        cursor.execute("""
            SELECT cmp_type, COUNT(*) 
            FROM crawl_results 
            WHERE success = 1 
            GROUP BY cmp_type
        """)
        stats["cmp_distribution"] = dict(cursor.fetchall())
        
        # Total cookies
        cursor.execute("SELECT COUNT(*) FROM cookies")
        stats["total_cookies"] = cursor.fetchone()[0]
        
        # Unique cookies (by name + domain)
        cursor.execute("SELECT COUNT(DISTINCT name || domain) FROM cookies")
        stats["unique_cookies"] = cursor.fetchone()[0]
        
        # Consent data entries
        cursor.execute("SELECT COUNT(*) FROM consent_data")
        stats["consent_data_entries"] = cursor.fetchone()[0]
        
        # Domains with consent data
        cursor.execute("""
            SELECT COUNT(DISTINCT crawl_id) 
            FROM consent_data
        """)
        stats["domains_with_consent_data"] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def export_to_json(self, output_path: str, include_unmatched: bool = False) -> None:
        """Export extracted cookie data to JSON file"""
        data = self.extract_cookies_with_consent(include_unmatched)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported cookie data to {output_path}")
        
    def export_statistics(self, output_path: str) -> None:
        """Export database statistics to JSON file"""
        stats = self.get_database_statistics()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported statistics to {output_path}")


def main():
    """Command line interface for cookie extraction"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract cookies from consent crawl database")
    parser.add_argument("database", help="Path to SQLite database file")
    parser.add_argument("-o", "--output", default="extracted_cookies.json",
                       help="Output JSON file path")
    parser.add_argument("-s", "--stats", default="database_stats.json",
                       help="Statistics output file path")
    parser.add_argument("--include-unmatched", action="store_true",
                       help="Include cookies without consent data")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    try:
        extractor = CookieExtractor(args.database)
        
        # Export cookie data
        extractor.export_to_json(args.output, args.include_unmatched)
        
        # Export statistics
        extractor.export_statistics(args.stats)
        
        print(f"Successfully extracted data from {args.database}")
        print(f"Cookie data: {args.output}")
        print(f"Statistics: {args.stats}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
