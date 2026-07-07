#!/usr/bin/env python3
"""Check @KanColle_STAFF for new tweets and update news file."""

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

NEWS_DIR = Path(r"C:/work/kancolle-wiki/news")
X_USERNAME = "KanColle_STAFF"
EVENT_KEYWORDS = ["イベント", "改修", "メンテナンス", "先行", "更新", "コラボ"]


def fetch_tweet_ids():
    """Extract tweet IDs from x.com HTML."""
    url = f"https://x.com/{X_USERNAME}"
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html',
    })
    with urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    pattern = rf'/{X_USERNAME}/status/(\d{{15,}})'
    tweet_ids = re.findall(pattern, html)
    return list(dict.fromkeys(tweet_ids))  # deduplicate preserving order


def fetch_tweet_detail(tweet_id):
    """Fetch a single tweet via fxtwitter API."""
    url = f"https://api.fxtwitter.com/status/{tweet_id}"
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    })
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data


def parse_tweet_date(created_at_str):
    """Convert tweet created_at to datetime."""
    from email.utils import parsedate_to_datetime
    try:
        dt = parsedate_to_datetime(created_at_str)
        # Convert to JST (UTC+9)
        dt_jst = dt.astimezone(timezone(timedelta(hours=9)))
        return dt_jst.strftime('%Y-%m-%d %H:%M'), dt_jst.strftime('%Y-%m-%d')
    except Exception:
        now = datetime.now(timezone(timedelta(hours=9)))
        return now.strftime('%Y-%m-%d %H:%M'), now.strftime('%Y-%m-%d')


def check_keywords(text):
    """Check for active period keywords."""
    found = []
    for kw in EVENT_KEYWORDS:
        if kw in text:
            found.append(kw)
    return found


def load_existing_ids():
    """Load previously processed tweet IDs."""
    ids_file = NEWS_DIR / ".processed_tweet_ids.json"
    if not ids_file.exists():
        return set()
    try:
        data = json.loads(ids_file.read_text('utf-8'))
        return set(data.get('processed_ids', []))
    except Exception:
        return set()


def load_existing_news_entries():
    """Load existing tweet IDs from today's news file."""
    today = datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d')
    # Find today's news files
    candidates = []
    for f in NEWS_DIR.glob(f"{today}-*.md"):
        if f.name != ".lock":
            candidates.append(f)

    existing_ids = set()
    for fpath in candidates:
        try:
            content = fpath.read_text('utf-8', errors='ignore')
            # Look for tweet IDs in the file
            ids = re.findall(r'(\d{15,})', content)
            existing_ids.update(ids)
        except Exception:
            pass

    return existing_ids


def update_news_file(new_tweets_data):
    """Append new tweets to today's news file atomically."""
    now_jst = datetime.now(timezone(timedelta(hours=9)))
    date_str = now_jst.strftime('%Y-%m-%d')

    # Find or create today's news file
    target_file = None
    for f in NEWS_DIR.glob(f"{date_str}-*.md"):
        if f.name != ".lock":
            target_file = f
            break

    if not target_file:
        target_file = NEWS_DIR / f"{date_str}-kancolle-staff.md"

    # Build new content to append
    lines = []
    for tweet_id, tweet_data in new_tweets_data.items():
        tweet = tweet_data.get('tweet', {})
        text = tweet.get('text', '') or ''
        created_at = tweet.get('created_at', '')
        time_str, _ = parse_tweet_date(created_at)

        keywords = check_keywords(text)
        kw_str = f" [{', '.join(keywords)}]" if keywords else ""

        lines.append(f"- [{time_str}] Tweet {tweet_id}: {text}{kw_str}")

    new_section = "\n## New Posts\n\n" + "\n".join(lines) + "\n"

    # Read existing content
    existing_content = ""
    if target_file.exists():
        try:
            existing_content = target_file.read_text('utf-8')
        except Exception:
            pass

    # Check if "## New Posts" section already exists; append after it or at end
    if "## New Posts" in existing_content:
        # Insert before ## Notes or at the end of ## New Posts section
        parts = existing_content.split("## New Posts")
        if len(parts) >= 2:
            new_content = parts[0] + "## New Posts\n\n" + "\n".join(lines) + "\n\n" + parts[1]
        else:
            new_content = existing_content + new_section
    else:
        # Prepend the section header if file has content, otherwise just write it
        if existing_content.strip():
            new_content = existing_content.rstrip() + "\n\n" + "## New Posts\n\n" + "\n".join(lines) + "\n"
        else:
            new_content = f"# @KanColle_STAFF Updates - {date_str}\n\n## New Posts\n\n" + "\n".join(lines) + "\n"

    # Atomic write via temp file + rename
    fd, tmp_path = tempfile.mkstemp(dir=str(NEWS_DIR), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(new_content)
        os.rename(tmp_path, str(target_file))
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    return target_file


def update_processed_ids(tweet_ids):
    """Save processed tweet IDs."""
    ids_file = NEWS_DIR / ".processed_tweet_ids.json"
    existing = load_existing_ids()
    for tid in tweet_ids:
        existing.add(tid)
    data = {"processed_ids": list(existing)}
    fd, tmp_path = tempfile.mkstemp(dir=str(NEWS_DIR), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.rename(tmp_path, str(ids_file))
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def main():
    print(f"[INFO] Checking @{X_USERNAME} for new tweets...")

    # Load existing IDs
    existing_ids = load_existing_ids()
    news_existing = load_existing_news_entries()
    all_known = existing_ids | news_existing

    # Fetch tweet IDs from x.com HTML
    tweet_ids = fetch_tweet_ids()
    print(f"[INFO] Found {len(tweet_ids)} tweets on profile page")

    if not tweet_ids:
        print("[WARN] No tweet IDs extracted. X.com may have changed structure.")
        return False

    # Find new tweets (not in existing IDs)
    new_tweet_ids = [tid for tid in tweet_ids if tid not in all_known]
    print(f"[INFO] {len(new_tweet_ids)} potentially new tweets")

    if not new_tweet_ids:
        print("[INFO] No new tweets found. All tweets already processed.")
        return False

    # Fetch details for new tweets (limit to 5 most recent)
    new_tweets_data = {}
    for tid in new_tweet_ids[:5]:
        try:
            data = fetch_tweet_detail(tid)
            if data and 'tweet' in data:
                tweet = data['tweet']
                text = tweet.get('text', '') or ''
                created_at = tweet.get('created_at', '')

                # Check date - only include tweets from last 7 days
                try:
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(created_at)
                    now = datetime.now(timezone.utc)
                    if (now - dt).days > 7:
                        print(f"  [SKIP] Tweet {tid} is older than 7 days")
                        continue
                except Exception:
                    pass

                new_tweets_data[tid] = data
                keywords = check_keywords(text)
                kw_str = f" [{', '.join(keywords)}]" if keywords else ""
                print(f"  [NEW] Tweet {tid}: {text[:100]}...{kw_str}")
        except Exception as e:
            print(f"  [ERROR] Failed to fetch tweet {tid}: {e}")

    if not new_tweets_data:
        print("[INFO] No new tweets within active period.")
        return False

    # Update news file
    target = update_news_file(new_tweets_data)
    print(f"[INFO] Updated news file: {target.name}")

    # Save processed IDs
    all_new_ids = list(new_tweets_data.keys())
    update_processed_ids(all_new_ids)

    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: Found {len(new_tweets_data)} new tweet(s)")
    for tid, data in new_tweets_data.items():
        tweet = data.get('tweet', {})
        text = tweet.get('text', '') or ''
        created_at = tweet.get('created_at', '')
        keywords = check_keywords(text)

        time_str, _ = parse_tweet_date(created_at)
        print(f"\n  [{time_str}] Tweet {tid}")
        print(f"    Text: {text[:200]}")
        if keywords:
            print(f"    Keywords: {', '.join(keywords)}")

    return True


if __name__ == '__main__':
    result = main()
    sys.exit(0 if result else 1)
