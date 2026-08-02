#!/usr/bin/env python3
"""Fetch KanColle research sources and extract key info."""
import urllib.request
import re
from pathlib import Path

META_DIR = Path("/c/work/kancolle-wiki/meta")
TODAY_FILE = META_DIR / "2026-08-01-research.md"

urls = [
    ("Wikipedia - Kantai Collection", "https://en.wikipedia.org/wiki/Kantai_Collection"),
    ("Moegirlpedia - 艦隊編成", "https://zh.moegirl.org.cn/Kantai_Collection/%E8%89%87%E9%98%9F%E7%B7%A8%E6%88%90"),
    ("KC3Kai Wiki - Ship Stats", "https://kcdb.zmoe.eu/extra/stats"),
]

results = []
for name, url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")
        
        if len(html) > 200:
            results.append((name, url, html))
            print(f"OK {name}: {len(html)} bytes fetched")
        else:
            print(f"WARN {name}: too short ({len(html)} bytes)")
    except Exception as e:
        print(f"ERR {name}: {e}")

# Now extract meaningful content from each source
print("\n=== EXTRACTING CONTENT ===\n")

for name, url, html in results:
    if "Wikipedia" in name:
        paragraphs = re.split(r'\n\s*\n', html)
        
        key_sections = []
        for para in paragraphs:
            stripped = para.strip()
            if not stripped or len(stripped) < 50:
                continue
            
            lower = stripped.lower()
            if any(kw in lower for kw in ['gameplay', 'mechanics', 'fleet', 'combat', 'equipment', 'event', 'map', 'strategy']):
                key_sections.append(stripped[:500])
        
        print(f"--- {name} ---")
        for i, sec in enumerate(key_sections[:8]):
            clean = re.sub(r'\[.*?\]', '', sec)
            clean = re.sub(r'<[^>]+>', '', clean)
            print(f"\n[{i+1}] {clean[:300]}...")

    elif "Moegirlpedia" in name:
        text_content = re.sub(r'<[^>]+>', ' ', html)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        print(f"--- {name} ---")
        if any(kw in text_content for kw in ['艦隊編成', '海域攻略', '裝備', '火力', '雷裝', '爆装']):
            sentences = re.split(r'[。；]', text_content)
            relevant = [s.strip() for s in sentences if len(s.strip()) > 30 and 
                       any(kw in s for kw in ['艦隊編成', '海域攻略', '裝備', '火力', '雷裝', '爆装', '機動', '索敵', '対空', '対潜', '航程'])]
            for i, sent in enumerate(relevant[:10]):
                print(f"\n[{i+1}] {sent}")

    elif "KC3Kai" in name:
        text_content = re.sub(r'<[^>]+>', ' ', html)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        print(f"--- {name} ---")
        if len(text_content) > 100:
            ship_pattern = r'([^\d<>]{2,30})\s+([\d]+)\s+([\d]+)\s+([\d]+)'
            ships = re.findall(ship_pattern, text_content[:5000])
            if ships:
                print(f"Found {len(ships)} ship entries")
                for ship in ships[:10]:
                    print(f"  Ship: {ship[0]}, Stats: {ship[1]}/{ship[2]}/{ship[3]}")
            else:
                print(text_content[:500])

print("\n=== DONE ===")
