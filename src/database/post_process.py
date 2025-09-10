import sqlite3
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger("db-processor")


class DatabaseProcessor:
    """Post-process and analyze crawl databases"""
    
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
    
    def backup_database(self, backup_suffix: str = "_backup") -> str:
        """Create a backup of the database"""
        db_path = Path(self.db_path)
        backup_path = db_path.parent / f"{db_path.stem}{backup_suffix}{db_path.suffix}"
        
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Database backed up to {backup_path}")
        
        return str(backup_path)
    
    def clean_database(self) -> Dict[str, int]:
        """Clean the database by removing invalid entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cleanup_stats = {}
        
        # Remove cookies with empty names
        cursor.execute("DELETE FROM cookies WHERE name IS NULL OR name = ''")
        cleanup_stats["empty_cookie_names_removed"] = cursor.rowcount
        
        # Remove consent data with empty cookie names
        cursor.execute("DELETE FROM consent_data WHERE cookie_name IS NULL OR cookie_name = ''")
        cleanup_stats["empty_consent_names_removed"] = cursor.rowcount
        
        # Remove orphaned cookies (crawl_id doesn't exist)
        cursor.execute("""
            DELETE FROM cookies 
            WHERE crawl_id NOT IN (SELECT id FROM crawl_results)
        """)
        cleanup_stats["orphaned_cookies_removed"] = cursor.rowcount
        
        # Remove orphaned consent data
        cursor.execute("""
            DELETE FROM consent_data 
            WHERE crawl_id NOT IN (SELECT id FROM crawl_results)
        """)
        cleanup_stats["orphaned_consent_data_removed"] = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database cleaned: {cleanup_stats}")
        return cleanup_stats
    
    def create_analysis_views(self) -> None:
        """Create SQL views for easier data analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # View: Cookie summary with consent data
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS cookie_summary AS
            SELECT 
                c.name as cookie_name,
                c.domain as cookie_domain,
                c.path,
                c.secure,
                c.http_only,
                c.same_site,
                cr.domain as crawl_domain,
                cr.cmp_type,
                cd.purpose_category,
                cd.purpose_description,
                COUNT(*) as occurrence_count
            FROM cookies c
            JOIN crawl_results cr ON c.crawl_id = cr.id
            LEFT JOIN consent_data cd ON (
                c.crawl_id = cd.crawl_id AND 
                c.name = cd.cookie_name AND 
                c.domain = cd.cookie_domain
            )
            WHERE cr.success = 1
            GROUP BY c.name, c.domain, cr.cmp_type, cd.purpose_category
        """)
        
        # View: Crawl success summary
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS crawl_summary AS
            SELECT 
                cmp_type,
                COUNT(*) as total_crawls,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_crawls,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_crawls,
                ROUND(AVG(cookies_collected), 2) as avg_cookies_per_crawl
            FROM crawl_results
            GROUP BY cmp_type
        """)
        
        # View: Purpose category distribution
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS purpose_distribution AS
            SELECT 
                purpose_category,
                cmp_type,
                COUNT(*) as count,
                COUNT(DISTINCT cookie_name || cookie_domain) as unique_cookies
            FROM consent_data
            GROUP BY purpose_category, cmp_type
            ORDER BY count DESC
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Analysis views created")
    
    def generate_statistics_report(self) -> Dict[str, Any]:
        """Generate comprehensive statistics report"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        report = {
            "generation_time": datetime.now().isoformat(),
            "database_path": self.db_path
        }
        
        # Basic crawl statistics
        cursor.execute("SELECT COUNT(*) FROM crawl_results")
        report["total_crawls"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM crawl_results WHERE success = 1")
        report["successful_crawls"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM crawl_results WHERE success = 0")
        report["failed_crawls"] = cursor.fetchone()[0]
        
        # Success rate
        if report["total_crawls"] > 0:
            report["success_rate"] = report["successful_crawls"] / report["total_crawls"]
        else:
            report["success_rate"] = 0
        
        # CMP distribution
        cursor.execute("""
            SELECT cmp_type, COUNT(*) 
            FROM crawl_results 
            WHERE success = 1 
            GROUP BY cmp_type
        """)
        report["cmp_distribution"] = dict(cursor.fetchall())
        
        # Cookie statistics
        cursor.execute("SELECT COUNT(*) FROM cookies")
        report["total_cookies"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT name || domain) FROM cookies")
        report["unique_cookies"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(cookies_collected) FROM crawl_results WHERE success = 1")
        avg_cookies = cursor.fetchone()[0]
        report["average_cookies_per_crawl"] = round(avg_cookies, 2) if avg_cookies else 0
        
        # Consent data statistics
        cursor.execute("SELECT COUNT(*) FROM consent_data")
        report["total_consent_entries"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT crawl_id) FROM consent_data")
        report["crawls_with_consent_data"] = cursor.fetchone()[0]
        
        # Purpose category distribution
        cursor.execute("""
            SELECT purpose_category, COUNT(*) 
            FROM consent_data 
            GROUP BY purpose_category 
            ORDER BY COUNT(*) DESC
        """)
        report["purpose_categories"] = dict(cursor.fetchall())
        
        # Error analysis
        cursor.execute("""
            SELECT error_message, COUNT(*) 
            FROM crawl_results 
            WHERE success = 0 AND error_message IS NOT NULL
            GROUP BY error_message 
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        report["common_errors"] = dict(cursor.fetchall())
        
        # Cookie attributes analysis
        cursor.execute("SELECT COUNT(*) FROM cookies WHERE secure = 1")
        report["secure_cookies"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cookies WHERE http_only = 1")
        report["http_only_cookies"] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT same_site, COUNT(*) 
            FROM cookies 
            WHERE same_site IS NOT NULL 
            GROUP BY same_site
        """)
        report["same_site_distribution"] = dict(cursor.fetchall())
        
        conn.close()
        
        logger.info("Statistics report generated")
        return report
    
    def analyze_cookie_consent_matching(self) -> Dict[str, Any]:
        """Analyze how well cookies match with consent declarations"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get matching statistics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT c.name || c.domain) as total_unique_cookies,
                COUNT(DISTINCT CASE WHEN cd.cookie_name IS NOT NULL 
                      THEN c.name || c.domain END) as matched_cookies
            FROM cookies c
            JOIN crawl_results cr ON c.crawl_id = cr.id
            LEFT JOIN consent_data cd ON (
                c.crawl_id = cd.crawl_id AND 
                c.name = cd.cookie_name AND 
                c.domain = cd.cookie_domain
            )
            WHERE cr.success = 1
        """)
        
        result = cursor.fetchone()
        total_unique = result["total_unique_cookies"]
        matched = result["matched_cookies"]
        
        matching_analysis = {
            "total_unique_cookies": total_unique,
            "matched_with_consent": matched,
            "unmatched_cookies": total_unique - matched,
            "matching_rate": matched / total_unique if total_unique > 0 else 0
        }
        
        # Analyze by CMP type
        cursor.execute("""
            SELECT 
                cr.cmp_type,
                COUNT(DISTINCT c.name || c.domain) as total_cookies,
                COUNT(DISTINCT CASE WHEN cd.cookie_name IS NOT NULL 
                      THEN c.name || c.domain END) as matched_cookies
            FROM cookies c
            JOIN crawl_results cr ON c.crawl_id = cr.id
            LEFT JOIN consent_data cd ON (
                c.crawl_id = cd.crawl_id AND 
                c.name = cd.cookie_name AND 
                c.domain = cd.cookie_domain
            )
            WHERE cr.success = 1
            GROUP BY cr.cmp_type
        """)
        
        cmp_matching = {}
        for row in cursor.fetchall():
            cmp_type = row["cmp_type"]
            total = row["total_cookies"]
            matched = row["matched_cookies"]
            
            cmp_matching[cmp_type] = {
                "total_cookies": total,
                "matched_cookies": matched,
                "matching_rate": matched / total if total > 0 else 0
            }
        
        matching_analysis["by_cmp_type"] = cmp_matching
        
        conn.close()
        return matching_analysis
    
    def export_report(self, output_path: str) -> None:
        """Export comprehensive analysis report to JSON"""
        report = {
            "statistics": self.generate_statistics_report(),
            "cookie_consent_matching": self.analyze_cookie_consent_matching()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis report exported to {output_path}")


def main():
    """Command line interface for database processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Post-process consent crawl database")
    parser.add_argument("database", help="Path to SQLite database file")
    parser.add_argument("--backup", action="store_true",
                       help="Create backup before processing")
    parser.add_argument("--clean", action="store_true",
                       help="Clean invalid data from database")
    parser.add_argument("--views", action="store_true",
                       help="Create analysis views")
    parser.add_argument("-o", "--output", default="analysis_report.json",
                       help="Output report file path")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    try:
        processor = DatabaseProcessor(args.database)
        
        if args.backup:
            processor.backup_database()
        
        if args.clean:
            processor.clean_database()
        
        if args.views:
            processor.create_analysis_views()
        
        # Always generate report
        processor.export_report(args.output)
        
        print(f"Database processing completed")
        print(f"Analysis report: {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
