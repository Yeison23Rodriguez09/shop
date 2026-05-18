"""Crawl base/home/navbar/footer/sidebar links and report any non-2xx/3xx."""
import re
import sys
import urllib.request
import urllib.error

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8770'
PAGES = ['/', '/productos/', '/servicios/']


def head(url: str) -> int:
    try:
        req = urllib.request.Request(url, method='GET')
        return urllib.request.urlopen(req, timeout=5).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


seen = set()
for page in PAGES:
    try:
        html = urllib.request.urlopen(BASE + page, timeout=5).read().decode('utf-8', 'replace')
    except Exception as e:
        print(f'CANNOT_FETCH {page}: {e}')
        continue
    for href in re.findall(r'href="(/[^"#?]+)"', html):
        seen.add(href)

bad = []
for h in sorted(seen):
    code = head(BASE + h)
    if code in (200, 301, 302):
        continue
    bad.append((code, h))

print(f'tested={len(seen)} bad={len(bad)}')
for code, h in bad:
    print(f'  {code}  {h}')
sys.exit(1 if bad else 0)
