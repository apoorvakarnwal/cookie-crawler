import json
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict
from datetime import datetime

logger = logging.getLogger("cookie-stats")


class CookieStatsAnalyzer:
    """Analyze cookie data and generate comprehensive statistics"""
    
    def __init__(self, data_path: str = None, data: Dict = None):
        """
        Initialize analyzer with either file path or data dictionary
        
        @param data_path: Path to JSON file with extracted cookie data
        @param data: Cookie data dictionary (alternative to file path)
        """
        if data_path:
            with open(data_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        elif data:
            self.data = data
        else:
            raise ValueError("Either data_path or data must be provided")
        
        self.cookies = self.data.get("cookies", {})
        self.setup_logger()
    
    def setup_logger(self):
        """Set up logger"""
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    def get_basic_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about the cookie dataset"""
        stats = {
            "total_unique_cookies": len(self.cookies),
            "total_cookie_instances": sum(len(cookie["variable_data"]) for cookie in self.cookies.values()),
            "analysis_date": datetime.now().isoformat()
        }
        
        # Count by CMP origin
        cmp_distribution = Counter()
        label_distribution = Counter()
        domain_distribution = Counter()
        
        for cookie in self.cookies.values():
            cmp_origin = cookie.get("cmp_origin", -1)
            label = cookie.get("label", -1)
            domain = cookie.get("domain", "unknown")
            
            cmp_distribution[cmp_origin] += 1
            label_distribution[label] += 1
            domain_distribution[domain] += 1
        
        # Map numeric codes to names
        cmp_names = {0: "cookiebot", 1: "onetrust", 2: "termly", -1: "unknown"}
        label_names = {0: "necessary", 1: "functional", 2: "analytics", 3: "advertising", 4: "social", -1: "unknown"}
        
        stats["cmp_distribution"] = {cmp_names.get(k, f"cmp_{k}"): v for k, v in cmp_distribution.items()}
        stats["label_distribution"] = {label_names.get(k, f"label_{k}"): v for k, v in label_distribution.items()}
        stats["top_domains"] = dict(domain_distribution.most_common(20))
        
        return stats
    
    def analyze_cookie_names(self) -> Dict[str, Any]:
        """Analyze cookie name patterns and frequencies"""
        name_analysis = {}
        
        # Cookie name frequency
        name_counter = Counter()
        name_length_stats = []
        
        for cookie in self.cookies.values():
            name = cookie.get("name", "")
            name_counter[name] += 1
            name_length_stats.append(len(name))
        
        name_analysis["most_common_names"] = dict(name_counter.most_common(50))
        name_analysis["unique_names"] = len(name_counter)
        name_analysis["name_length_stats"] = {
            "mean": float(np.mean(name_length_stats)),
            "median": float(np.median(name_length_stats)),
            "std": float(np.std(name_length_stats)),
            "min": int(np.min(name_length_stats)),
            "max": int(np.max(name_length_stats))
        }
        
        # Analyze name patterns
        patterns = {
            "contains_underscore": sum(1 for name in name_counter if "_" in name),
            "contains_dash": sum(1 for name in name_counter if "-" in name),
            "contains_digits": sum(1 for name in name_counter if any(c.isdigit() for c in name)),
            "all_uppercase": sum(1 for name in name_counter if name.isupper()),
            "all_lowercase": sum(1 for name in name_counter if name.islower()),
            "starts_with_underscore": sum(1 for name in name_counter if name.startswith("_")),
        }
        
        name_analysis["name_patterns"] = patterns
        
        return name_analysis
    
    def analyze_cookie_values(self) -> Dict[str, Any]:
        """Analyze cookie value characteristics"""
        value_analysis = {}
        
        value_lengths = []
        encoding_patterns = {
            "empty_values": 0,
            "numeric_only": 0,
            "contains_base64": 0,
            "contains_json": 0,
            "contains_url_encoding": 0,
            "contains_semicolon": 0
        }
        
        for cookie in self.cookies.values():
            for var_data in cookie.get("variable_data", []):
                value = var_data.get("value", "")
                value_lengths.append(len(value))
                
                # Analyze value patterns
                if not value:
                    encoding_patterns["empty_values"] += 1
                elif value.isdigit():
                    encoding_patterns["numeric_only"] += 1
                
                if "%" in value:
                    encoding_patterns["contains_url_encoding"] += 1
                if ";" in value:
                    encoding_patterns["contains_semicolon"] += 1
                if value.startswith("{") or value.startswith("["):
                    encoding_patterns["contains_json"] += 1
                
                # Simple base64 detection (basic heuristic)
                if len(value) > 10 and value.replace("+", "").replace("/", "").replace("=", "").isalnum():
                    if len(value) % 4 == 0:
                        encoding_patterns["contains_base64"] += 1
        
        if value_lengths:
            value_analysis["value_length_stats"] = {
                "mean": float(np.mean(value_lengths)),
                "median": float(np.median(value_lengths)),
                "std": float(np.std(value_lengths)),
                "min": int(np.min(value_lengths)),
                "max": int(np.max(value_lengths))
            }
        else:
            value_analysis["value_length_stats"] = {}
        
        value_analysis["encoding_patterns"] = encoding_patterns
        
        return value_analysis
    
    def analyze_security_attributes(self) -> Dict[str, Any]:
        """Analyze cookie security attributes"""
        security_stats = {
            "secure": 0,
            "http_only": 0,
            "secure_and_http_only": 0,
            "same_site_strict": 0,
            "same_site_lax": 0,
            "same_site_none": 0,
            "same_site_not_set": 0
        }
        
        total_instances = 0
        
        for cookie in self.cookies.values():
            for var_data in cookie.get("variable_data", []):
                total_instances += 1
                
                secure = var_data.get("secure", False)
                http_only = var_data.get("http_only", False)
                same_site = var_data.get("same_site", "").lower()
                
                if secure:
                    security_stats["secure"] += 1
                if http_only:
                    security_stats["http_only"] += 1
                if secure and http_only:
                    security_stats["secure_and_http_only"] += 1
                
                if same_site == "strict":
                    security_stats["same_site_strict"] += 1
                elif same_site == "lax":
                    security_stats["same_site_lax"] += 1
                elif same_site == "none" or same_site == "no_restriction":
                    security_stats["same_site_none"] += 1
                else:
                    security_stats["same_site_not_set"] += 1
        
        # Convert to percentages
        security_percentages = {}
        for key, value in security_stats.items():
            security_percentages[key] = {
                "count": value,
                "percentage": (value / total_instances * 100) if total_instances > 0 else 0
            }
        
        return {
            "total_cookie_instances": total_instances,
            "security_attributes": security_percentages
        }
    
    def analyze_purpose_consistency(self) -> Dict[str, Any]:
        """Analyze consistency of purpose labels across same cookie names"""
        consistency_analysis = {}
        
        # Group cookies by name
        cookies_by_name = defaultdict(list)
        for cookie_id, cookie in self.cookies.items():
            name = cookie.get("name", "")
            cookies_by_name[name].append(cookie)
        
        consistent_cookies = 0
        inconsistent_cookies = 0
        inconsistency_examples = []
        
        for name, cookie_list in cookies_by_name.items():
            if len(cookie_list) > 1:
                labels = set(cookie.get("label", -1) for cookie in cookie_list)
                if len(labels) == 1:
                    consistent_cookies += 1
                else:
                    inconsistent_cookies += 1
                    if len(inconsistency_examples) < 10:  # Limit examples
                        inconsistency_examples.append({
                            "cookie_name": name,
                            "labels_found": list(labels),
                            "domains": [cookie.get("domain", "") for cookie in cookie_list]
                        })
        
        consistency_analysis["cookies_with_multiple_instances"] = consistent_cookies + inconsistent_cookies
        consistency_analysis["consistent_labeling"] = consistent_cookies
        consistency_analysis["inconsistent_labeling"] = inconsistent_cookies
        consistency_analysis["consistency_rate"] = (
            consistent_cookies / (consistent_cookies + inconsistent_cookies) 
            if (consistent_cookies + inconsistent_cookies) > 0 else 0
        )
        consistency_analysis["inconsistency_examples"] = inconsistency_examples
        
        return consistency_analysis
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analysis report"""
        logger.info("Generating comprehensive cookie analysis report")
        
        report = {
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "analyzer_version": "1.0.0",
                "data_source": getattr(self, "data_path", "provided_data")
            },
            "basic_statistics": self.get_basic_statistics(),
            "cookie_names": self.analyze_cookie_names(),
            "cookie_values": self.analyze_cookie_values(),
            "security_attributes": self.analyze_security_attributes(),
            "purpose_consistency": self.analyze_purpose_consistency()
        }
        
        logger.info("Analysis report completed")
        return report
    
    def export_report(self, output_path: str) -> None:
        """Export comprehensive analysis report to JSON file"""
        report = self.generate_comprehensive_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis report exported to {output_path}")
    
    def print_summary(self) -> None:
        """Print a summary of key statistics"""
        stats = self.get_basic_statistics()
        
        print("\n" + "="*50)
        print("COOKIE ANALYSIS SUMMARY")
        print("="*50)
        print(f"Total unique cookies: {stats['total_unique_cookies']:,}")
        print(f"Total cookie instances: {stats['total_cookie_instances']:,}")
        
        print(f"\nCMP Distribution:")
        for cmp, count in stats['cmp_distribution'].items():
            percentage = count / stats['total_unique_cookies'] * 100
            print(f"  {cmp}: {count:,} ({percentage:.1f}%)")
        
        print(f"\nPurpose Label Distribution:")
        for label, count in stats['label_distribution'].items():
            percentage = count / stats['total_unique_cookies'] * 100
            print(f"  {label}: {count:,} ({percentage:.1f}%)")
        
        security = self.analyze_security_attributes()
        print(f"\nSecurity Attributes:")
        print(f"  Secure cookies: {security['security_attributes']['secure']['percentage']:.1f}%")
        print(f"  HttpOnly cookies: {security['security_attributes']['http_only']['percentage']:.1f}%")
        print(f"  SameSite=Strict: {security['security_attributes']['same_site_strict']['percentage']:.1f}%")


def main():
    """Command line interface for cookie statistics analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze cookie data statistics")
    parser.add_argument("data_file", help="Path to JSON file with extracted cookie data")
    parser.add_argument("-o", "--output", default="cookie_analysis_report.json",
                       help="Output report file path")
    parser.add_argument("--summary", action="store_true",
                       help="Print summary to console")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    try:
        analyzer = CookieStatsAnalyzer(args.data_file)
        
        if args.summary:
            analyzer.print_summary()
        
        analyzer.export_report(args.output)
        
        print(f"\nAnalysis completed successfully!")
        print(f"Report saved to: {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
