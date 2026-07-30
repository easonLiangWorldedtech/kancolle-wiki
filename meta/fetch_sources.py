#!/usr/bin/env python3
import urllib.request, re, sys
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

sources = [
    ('Moegirlpedia - 艦隊編成', 'https://zh.moegirl.org.cn/Kantai_Collection/%E8%89%87%E9%98%9F%E7%B7%A8%E6%88%90'),
    ('KC3Kai Wiki - Ship Stats (kcdb)', 'https://kcdb.zmoe.eu/extra/stats'),
]

for name, url in sources:
    print(f'Fetching {name}...', file=sys.stderr)
    html = fetch(url)
    if html and len(html) > 100:
        imgs = extract_images(html, url)
        downloaded = []
        for img_url in imgs[:5]:
            sp = download_image(img_url, IMAGES_DIR)
            if sp:
                downloaded.append(sp)
        img_refs = ''
        if downloaded:
            img_refs = '\n   📸 Images: ' + ', '.join(downloaded)
        print(f'- [{name}] (URL: {url}) - Content fetched{img_refs}')
    else:
        print(f'- [{name}] (URL: {url}) - No content or too short ({len(html) if html else 0} chars)', file=sys.stderr)

print('DONE', file=sys.stderr)
