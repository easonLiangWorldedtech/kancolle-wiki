#!/usr/bin/env python3
"""Fetch KanColle research sources - improved extraction."""
import urllib.request
import re
from pathlib import Path

META_DIR = Path("/c/work/kancolle-wiki/meta")
TODAY_FILE = META_DIR / "2026-08-01-research.md"

# Try multiple URLs for each source
sources = [
    ("Wikipedia - Kantai Collection", "https://en.wikipedia.org/wiki/Kantai_Collection"),
    ("Moegirlpedia - 艦隊編成 (alt)", "https://zh.moegirl.org.cn/index.php?title=Kantai_Collection/%E8%89%87%E9%98%9F%E7%B7%A8%E6%88%90&action=edit"),
    ("Moegirlpedia - 艦これ攻略Wiki", "https://zh.moegirl.org.cn/Kantai_Collection"),
    ("KCDB Extra Stats (alt)", "https://kcdb.zmoe.eu/extra/stats"),
    ("Fandom Wiki - Kantai Collection", "https://kancolle.fandom.com/wiki/Main_Page"),
]

results = []
for name, url in sources:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8")
        
        if len(html) > 200:
            results.append((name, url, html))
            print(f"OK {name}: {len(html)} bytes")
        else:
            print(f"WARN {name}: too short ({len(html)})")
    except Exception as e:
        print(f"ERR {name}: {e}")

print("\n=== EXTRACTING KEY INFO ===\n")

# Extract from Wikipedia
for name, url, html in results:
    if "Wikipedia" in name:
        # Strip HTML tags to get text content
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        
        print(f"--- {name} ---")
        print(text[:3000])

    elif "Moegirlpedia" in name or "Fandom" in name:
        # Strip HTML tags to get text content  
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        
        print(f"\n--- {name} ---")
        if len(text) > 200:
            # Look for relevant sections
            if "艦隊編成" in text or "fleet" in text.lower():
                # Find fleet composition info
                idx = text.find("艦隊編成")
                if idx >= 0:
                    print(text[max(0,idx-200):idx+800])
                else:
                    print(text[:1500])
            elif "攻略" in text or "event" in text.lower() or "map" in text.lower():
                idx = text.find("攻略")
                if idx >= 0:
                    print(text[max(0,idx-200):idx+800])
                else:
                    print(text[:1500])
            else:
                print(text[:1500])

print("\n=== DONE ===")
