#!/usr/bin/env python3
"""kancolle-meta-researcher.py - Research KanColle mechanics, strategies & known builds
Features: file locking, atomic writes, auto image fetching
Only outputs when there are NEW updates (silent otherwise)
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

# Configuration
WIKI_ROOT = Path("C:/work/kancolle-wiki")
META_DIR = WIKI_ROOT / "meta"
IMAGES_DIR = META_DIR / "images"
META_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y-%m-%d")
TODAY_FILE = META_DIR / f"{TIMESTAMP}-research.md"
LOCK_FILE = TODAY_FILE.with_suffix(".lock")


def acquire_lock(timeout=5):
    """Acquire file lock to prevent concurrent writes"""
    import time
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            time.sleep(0.5)
    
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            os.kill(pid, 0)
        except (ProcessLookupError, ValueError):
            LOCK_FILE.unlink(missing_ok=True)
            return acquire_lock()
    
    return False


def release_lock():
    """Release file lock"""
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def fetch_wiki_content(url):
    """Fetch content from a wiki URL"""
    try:
        import urllib.request
        
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        print(f"⚠️ Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def extract_images(html_content, base_url):
    """Extract image URLs from HTML content"""
    import re
    
    images = []
    
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
    for match in re.finditer(img_pattern, html_content):
        img_url = match.group(1)
        
        if not img_url.startswith('http'):
            img_url = urljoin(base_url, img_url)
        
        images.append(img_url)
    
    return list(set(images))


def download_image(url, save_dir):
    """Download an image and save it locally"""
    try:
        import urllib.request
        
        filename = url.split('/')[-1].split('?')[0]
        if not filename or '.' not in filename:
            filename = f"image_{len(list(save_dir.glob('*')) + 1)}.jpg"
        
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        filepath = save_dir / filename
        
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            
            if len(data) > 1000:
                filepath.write_bytes(data)
                return str(filepath.relative_to(save_dir.parent))
    
    except Exception as e:
        print(f"⚠️ Failed to download {url}: {e}", file=sys.stderr)
    
    return None


def load_existing_research():
    """Load existing research from today's file"""
    if not TODAY_FILE.exists():
        return []
    
    with open(TODAY_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    items = []
    for line in content.split("\n"):
        if line.startswith("- ["):
            parts = line.split("] ", 1)
            if len(parts) == 2:
                items.append({
                    "date": parts[0].replace("- [", "").strip(),
                    "content": parts[1].strip()
                })
    
    return items


def save_research_atomic(content):
    """Save content using atomic write"""
    fd, tmp_path = tempfile.mkstemp(dir=META_DIR, suffix=".tmp")
    
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        
        TODAY_FILE.unlink(missing_ok=True)
        Path(tmp_path).rename(TODAY_FILE)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def check_for_updates():
    """Main function to research KanColle"""
    print("🔍 Researching KanColle mechanics & strategies...", file=sys.stderr)
    
    # Working sources (verified)
    sources = [
        ("Wikipedia - Kantai Collection", "https://en.wikipedia.org/wiki/Kantai_Collection"),
        ("Moegirlpedia - 艦隊編成", "https://zh.moegirl.org.cn/Kantai_Collection/%E8%89%87%E9%98%9F%E7%B7%A8%E6%88%90"),
        ("KC3Kai Wiki - Ship Stats (kcdb)", "https://kcdb.zmoe.eu/extra/stats"),
    ]
    
    existing_items = load_existing_research()
    
    if len(existing_items) == 0:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        content_parts = [f"# KanColle Research - {TIMESTAMP}\n\n", "## New Findings\n\n"]
        
        for name, url in sources:
            print(f"  Fetching {name}...", file=sys.stderr)
            html_content = fetch_wiki_content(url)
            
            if html_content and len(html_content) > 100:
                images = extract_images(html_content, url)
                
                downloaded = []
                for img_url in images[:5]:
                    saved_path = download_image(img_url, IMAGES_DIR)
                    if saved_path:
                        downloaded.append(saved_path)
                
                image_refs = ""
                if downloaded:
                    image_refs = f"\n   📸 Images: {', '.join(downloaded)}"
                
                content_parts.append(f"- [{now_str}] {name} (URL: {url}) - Content fetched{image_refs}\n\n")
        
        save_research_atomic("".join(content_parts))
        
        with open(TODAY_FILE, "r", encoding="utf-8") as f:
            return f.read()
    
    print("✅ No new research updates detected", file=sys.stderr)
    return None


if __name__ == "__main__":
    if not acquire_lock():
        print("⚠️ Lock already held, skipping", file=sys.stderr)
        sys.exit(0)
    
    try:
        result = check_for_updates()
        
        if result:
            print(result)
    finally:
        release_lock()
