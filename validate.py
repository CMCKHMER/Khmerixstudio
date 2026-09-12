#!/usr/bin/env python3
"""Validate Khmerix Studio HTML files and links."""
import os
import re
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
EXTERNAL_LINKS = set()
INTERNAL_LINKS = set()
FILES = ['index.html', 'studio.html', 'highlights.html']

def extract_links(html, filename):
    """Extract href and src links from HTML."""
    # href links
    for m in re.finditer(r'href="([^"]+)"', html):
        link = m.group(1)
        if link.startswith('http'):
            EXTERNAL_LINKS.add((link, filename))
        elif not link.startswith('#') and not link.startswith('javascript:') and not link.startswith('mailto:') and '${' not in link:
            INTERNAL_LINKS.add((link, filename))
    # src links
    for m in re.finditer(r'src="([^"]+)"', html):
        link = m.group(1)
        if link.startswith('http'):
            EXTERNAL_LINKS.add((link, filename))
        elif not link.startswith('blob:') and not link.startswith('data:') and '${' not in link:
            INTERNAL_LINKS.add((link, filename))

def check_external(url):
    """Check external URL returns 200."""
    try:
        # Google Fonts blocks HEAD; use GET for those
        method = 'GET' if 'fonts.googleapis.com' in url or 'fonts.gstatic.com' in url else 'HEAD'
        req = urllib.request.Request(url, method=method, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return str(e)

def main():
    print("=" * 60)
    print("KHMERIX STUDIO — VALIDATION REPORT")
    print("=" * 60)

    # Parse all HTML files
    for fname in FILES:
        fpath = BASE_DIR / fname
        if not fpath.exists():
            print(f"\n[MISSING] {fname}")
            continue
        html = fpath.read_text(encoding='utf-8')
        extract_links(html, fname)
        # Basic well-formed check: count opening/closing tags roughly
        open_html = html.count('<html')
        close_html = html.count('</html>')
        open_body = html.count('<body')
        close_body = html.count('</body>')
        open_head = html.count('<head>')
        close_head = html.count('</head>')
        status = "OK" if open_html == close_html == 1 and open_body == close_body == 1 and open_head == close_head == 1 else "STRUCTURE WARNING"
        print(f"\n[FILE] {fname:20s} -> {status}")

    # Check internal links
    print("\n" + "-" * 60)
    print("INTERNAL LINKS")
    print("-" * 60)
    internal_ok = True
    for link, src in sorted(INTERNAL_LINKS):
        # Strip query/fragment
        clean = link.split('?')[0].split('#')[0]
        if clean.endswith('/'):
            clean += 'index.html'
        target = BASE_DIR / clean
        exists = target.exists()
        mark = "OK" if exists else "MISSING"
        if not exists:
            internal_ok = False
        print(f"  [{mark:7s}] {link:40s} (from {src})")

    # Check external links
    print("\n" + "-" * 60)
    print("EXTERNAL LINKS")
    print("-" * 60)
    external_ok = True
    for url, src in sorted(EXTERNAL_LINKS):
        # Skip preconnect-only domains that are not meant to be accessed directly
        if url in ('https://fonts.googleapis.com', 'https://fonts.gstatic.com'):
            print(f"  [{ 'SKIP':12s}] {url:50s} (from {src})  [preconnect hint]")
            continue
        status = check_external(url)
        if status == 200:
            mark = "OK"
        else:
            mark = f"FAIL ({status})"
            external_ok = False
        print(f"  [{mark:12s}] {url:50s} (from {src})")

    print("\n" + "=" * 60)
    if internal_ok and external_ok:
        print("RESULT: ALL CHECKS PASSED [PASS]")
        return 0
    else:
        print("RESULT: SOME CHECKS FAILED [FAIL]")
        return 1

if __name__ == '__main__':
    exit(main())
