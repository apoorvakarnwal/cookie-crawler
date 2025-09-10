"""
Takes as input a list of text files containing one valid URL per line,
and attempts to prune duplicate netlocs (i.e. duplicate domains).
Outputs a filtered list of domains (one per line).

Usage:
    filter_duplicate_netlocs.py [--file <FILE>]... [--csv <FILE>]... (--out <OUT>)

Options:
    -f --file <FILE>   File to draw domains from (1 per line)
    -c --csv <FILE>    CSV to draw domains from (comma separated, second entry)
    -o --out <OUT>     Outfile path
    -h --help          Display this information.
"""
import re
import os
import tldextract

from urllib.parse import urlparse
from docopt import docopt
from typing import Optional

domains = set()
urls = list()

# tldextract instance (uses public suffix list)
extract = tldextract.TLDExtract()


def normalize_domain_from_line(line: str) -> Optional[str]:
    """
    Given an input line (which may be 'example.com', 'http://example.com/path',
    'https://www.example.com:8080', etc.), return the normalized registered domain
    (e.g. example.com or example.co.uk). Returns None on failure.
    """
    if not line:
        return None
    s = line.strip()
    if not s:
        return None

    # If input contains multiple comma-separated fields (accident), don't treat whole line here.
    # Caller should split CSVs; here we'll accept a single token.
    # Ensure there's a scheme so urlparse gives us netloc
    if "://" not in s:
        candidate = "http://" + s
    else:
        candidate = s

    try:
        p = urlparse(candidate)
        host = p.netloc or p.path.split("/")[0]  # fallback if netloc empty
        host = host.lower().strip()

        # strip common noise
        host = re.sub(r"^www\.", "", host)
        host = re.sub(r":[0-9]+$", "", host)  # remove port if any

        if not host:
            return None

        # Use tldextract to get registered domain
        te = extract(host)
        if te.domain and te.suffix:
            reg_domain = te.domain + "." + te.suffix
        elif te.domain:
            reg_domain = te.domain
        else:
            reg_domain = host

        reg_domain = reg_domain.strip(".")
        if not reg_domain:
            return None

        return reg_domain
    except Exception:
        return None


def unique_extract(line: str):
    reg = normalize_domain_from_line(line)
    if not reg:
        return
    if reg not in domains:
        domains.add(reg)
        urls.append(reg)
    else:
        print(f"duplicate domain for: {line.strip()}")


def main() -> int:
    argv = None
    args = docopt(__doc__, argv=argv)

    valid_paths = []
    csv_paths = []
    output_path = args["--out"]

    # docopt with "..." options returns None or list depending on invocation; guard it:
    file_args = args.get("--file") or []
    csv_args = args.get("--csv") or []

    for fpath in file_args:
        if os.path.exists(fpath):
            valid_paths.append(fpath)
        else:
            print(f"Skipping (not found): {fpath}")

    for fpath in csv_args:
        if os.path.exists(fpath):
            csv_paths.append(fpath)
        else:
            print(f"Skipping (not found): {fpath}")

    for v in valid_paths:
        with open(v, 'r', encoding="utf-8", errors="ignore") as fd:
            for l in fd:
                unique_extract(l)

    for c in csv_paths:
        with open(c, 'r', encoding="utf-8", errors="ignore") as fd:
            for l in fd:
                parts = [p.strip().strip('"').strip("'") for p in l.split(",")]
                if len(parts) >= 2:
                    # second column is expected to contain the domain/url
                    unique_extract(parts[1])
                elif len(parts) == 1:
                    unique_extract(parts[0])
                else:
                    continue

    print(f"Number of unique domains: {len(urls)}")

    # write plain domains (no scheme) — easy to consume downstream
    with open(output_path, 'w', encoding="utf-8") as fd:
        for u in urls:
            fd.write(u + "\n")

    return 0


if __name__ == "__main__":
    main()