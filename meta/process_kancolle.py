#!/usr/bin/env python3
"""Process Kantalle research data and extract key findings."""
import json
import re
from pathlib import Path

# Read the raw wiki content
raw = Path("C:/work/kancolle-wiki/meta/kancolle_raw.json").read_text(encoding="utf-8")
data = json.loads(raw)
pages = data["query"]["pages"]
page_id = list(pages.keys())[0]
wiki_content = pages[page_id]["revisions"][0]["*"]

# Strip wiki markup for readability
def clean_wiki(text):
    text = re.sub(r'\{\{[^}]*\}\}', '', text)
    text = re.sub(r'\[\[([^\]|]+)\|?[^\]]*\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]|]*)\]\]', r'\1', text)
    text = re.sub(r'\[[^\s]+\s([^\]]*)\]', r'\1', text)
    text = re.sub(r'==[^=]+==', '', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()
    return text

clean = clean_wiki(wiki_content)

# Write cleaned content for analysis
Path("C:/work/kancolle-wiki/meta/kancolle_clean.txt").write_text(clean, encoding="utf-8")

print(f"Cleaned wiki length: {len(clean)} chars")
print("\n=== FIRST 5000 CHARS ===")
print(clean[:5000])

# Look for key sections
key_sections = ["Gameplay", "Combat", "Fleet composition", "Ship types", 
                "Equipment", "Events", "Maps", "Strategy", "Mechanics"]
for section in key_sections:
    pattern = f"==\\s*{section}\\s*=="
    match = re.search(pattern, wiki_content)
    if match:
        start = match.end()
        next_section = re.search(r'== [^=]', wiki_content[start:])
        end = next_section.start() + start if next_section else min(start + 8000, len(wiki_content))
        section_text = clean_wiki(wiki_content[start:end])
        print(f"\n\n=== SECTION: {section} ===")
        print(section_text[:4000])
