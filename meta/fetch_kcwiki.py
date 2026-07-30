#!/usr/bin/env python3
import urllib.request, re, sys, json
from pathlib import Path
from urllib.parse import urljoin

IMAGES_DIR = Path('C:/work/kancolle-wiki/meta/images')
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'FETCH ERROR {url}: {e}', file=sys.stderr)
        return None

def download_image(url, save_dir):
    try:
        fn = url.split('/')[-1].split('?')[0]
        if not fn or '.' not in fn:
            fn = f'image_{len(list(save_dir.glob("*"))+1)}.jpg'
        fn = ''.join(c for c in fn if c.isalnum() or c in '._-')
        fp = save_dir / fn
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read()
            if len(data) > 1000:
                fp.write_bytes(data)
                return str(fp.relative_to(save_dir.parent))
    except Exception as e:
        print(f'IMG ERROR {url}: {e}', file=sys.stderr)
    return None

def extract_images(html, base_url):
    imgs = []
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', html):
        u = m.group(1)
        if not u.startswith('http'):
            u = urljoin(base_url, u)
        imgs.append(u)
    return list(set(imgs))

# Try multiple alternative sources for new content
sources = [
    ('kcwiki.org - 2026夏活メイン', 'https://zh.kcwiki.org/wiki/%E6%94%BB%E7%95%A5:2026%E5%B9%B4%E5%A4%8F%E5%AD%A3%E6%B4%BB%E5%8B%95%E6%94%BB%E7%95%A5'),
    ('kcwiki.org - E1', 'https://zh.kcwiki.org/wiki/%E6%94%BB%E7%95%A5:2026%E5%B9%B4%E5%A4%8F%E5%AD%A3%E6%B4%BB%E5%8B%95%E6%94%BB%E7%95%A5/E1'),
    ('kcwiki.org - E2', 'https://zh.kcwiki.org/wiki/%E6%94%BB%E7%95%A5:2026%E5%B9%B4%E5%A4%8F%E5%AD%A3%E6%B4%BB%E5%8B%95%E6%94%BB%E7%95%A5/E2'),
    ('kcwiki.org - E3', 'https://zh.kcwiki.org/wiki/%E6%94%BB%E7%95%A5:2026%E5%B9%B4%E5%A4%8F%E5%AD%A3%E6%B4%BB%E5%8B%95%E6%94%BB%E7%95%A5/E3'),
    ('kcwiki.org - E4', 'https://zh.kcwiki.org/wiki/%E6%94%BB%E7%95%A5:2026%E5%B9%B4%E5%A4%8F%E5%AD%A3%E6%B4%BB%E5%8B%95%E6%94%BB%E7%95%A5/E4'),
    ('kcwiki.org - E5', 'https://zh.kcwiki.org/wiki/%E6%94%BB%E7%95%A5:2026%E5%B9%B4%E5%A4%8F%E5%AD%A3%E6%B4%BB%E5%8B%95%E6%94%BB%E7%95%A5/E5'),
    ('kcwiki.org - 艦種', 'https://zh.kcwiki.org/wiki/%E8%89%87%E7%A8%AE'),
    ('kcwiki.org - 裝備', 'https://zh.kcwiki.org/wiki/%E8%A3%9D%E5%82%99'),
]

found_new = False
for name, url in sources:
    print(f'Fetching {name}...', file=sys.stderr)
    html = fetch(url)
    if html and len(html) > 100:
        # Check for last-modified info
        modified_match = re.search(r'<span[^>]*class=["\']?lastmod[^>]*>(.*?)</span>', html, re.IGNORECASE)
        mod_text = ''
        if modified_match:
            mod_text = ' — Last updated: ' + modified_match.group(1).strip()[:80]
        
        imgs = extract_images(html, url)
        downloaded = []
        for img_url in imgs[:3]:
            sp = download_image(img_url, IMAGES_DIR)
            if sp:
                downloaded.append(sp)
        img_refs = ''
        if downloaded:
            img_refs = '\n   📸 Images: ' + ', '.join(downloaded)
        
        status = '✅' if len(html) > 500 else '⚠️'
        print(f'- [{name}] (URL: {url}) - Content fetched{mod_text} {status}{img_refs}')
        found_new = True
    else:
        print(f'- [{name}] (URL: {url}) - No content ({len(html) if html else 0} chars)', file=sys.stderr)

if not found_new:
    print('NO_NEW_UPDATES', file=sys.stderr)
else:
    print('HAS_UPDATES', file=sys.stderr)
