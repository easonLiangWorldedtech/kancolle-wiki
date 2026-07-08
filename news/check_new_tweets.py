#!/usr/bin/env python3
"""Check for new tweets from @KanColle_STAFF RSS feed and compare with processed IDs."""

import xml.etree.ElementTree as ET
import json
import os
import sys
from datetime import datetime, timezone

NEWS_DIR = r'C:\work\kancolle-wiki\news'
PROCESSED_FILE = os.path.join(NEWS_DIR, '.processed_tweet_ids.json')
LOCK_FILE = os.path.join(NEWS_DIR, '.lock')
FEED_URL = 'https://fxtwitter.com/KanColle_STAFF/feed.xml'
NEW_IDS_FILE = os.path.join(NEWS_DIR, '.new_tweet_ids.json')

# Active period keywords to flag
ACTIVE_KEYWORDS = ['イベント', '改修', 'メンテナンス', '先行', '更新', 'コラボ']

def load_processed_ids():
    """Load previously processed tweet IDs."""
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            data = json.load(f)
        return set(data.get('processed_ids', []))
    return set()

def parse_rss_feed(feed_path):
    """Parse RSS feed and extract tweet items."""
    tree = ET.parse(feed_path)
    channel = tree.find('.//channel')
    if channel is None:
        print("ERROR: No channel found in RSS feed")
        return []
    
    items = channel.findall('item')
    tweets = []
    for item in items:
        title_el = item.find('title')
        link_el = item.find('link')
        pub_date_el = item.find('pubDate')
        
        if title_el is None or link_el is None:
            continue
        
        title = title_el.text or ''
        link = link_el.text or ''
        pub_date = pub_date_el.text if pub_date_el is not None else ''
        
        # Extract tweet ID from URL (e.g., status/2072954628770329010)
        tweet_id = ''
        if '/status/' in link:
            tweet_id = link.split('/')[-1]
        
        tweets.append({
            'id': tweet_id,
            'title': title,
            'link': link,
            'pub_date': pub_date
        })
    
    return tweets

def check_keywords(text):
    """Check if text contains active period keywords."""
    found = []
    for kw in ACTIVE_KEYWORDS:
        if kw in text:
            found.append(kw)
    return found

def main():
    # Load processed IDs
    existing_ids = load_processed_ids()
    
    # Parse RSS feed
    tweets = parse_rss_feed(os.path.join(NEWS_DIR, 'kancolle_feed.xml'))
    
    print(f"Total items in feed: {len(tweets)}")
    print(f"Existing processed IDs: {len(existing_ids)}")
    
    # Find new tweets (by ID)
    new_tweets = []
    for t in tweets:
        if t['id'] and t['id'] not in existing_ids:
            keywords = check_keywords(t['title'])
            new_tweets.append({
                'id': t['id'],
                'title': t['title'],
                'link': t['link'],
                'pub_date': t['pub_date'],
                'keywords': keywords
            })
    
    print(f"New tweets found: {len(new_tweets)}")
    
    # Output new tweet IDs for the cron job to use
    if new_tweets:
        for t in new_tweets:
            pub_dt = ''
            try:
                dt = datetime.strptime(t['pub_date'], '%a, %d %b %Y %H:%M:%S %Z')
                dt_jst = dt + __import__('datetime').timedelta(hours=9)
                pub_dt = dt_jst.strftime('%Y-%m-%d %H:%M')
            except:
                pub_dt = t['pub_date']
            
            print(f"\n--- NEW TWEET ---")
            print(f"ID: {t['id']}")
            print(f"Date (JST): {pub_dt}")
            print(f"Title: {t['title'][:300]}")
            print(f"Link: {t['link']}")
            if t['keywords']:
                print(f"Keywords: {', '.join(t['keywords'])}")
        
        # Output new IDs to a temp file for the main script to pick up
        new_ids = [t['id'] for t in new_tweets]
        with open(os.path.join(NEWS_DIR, '.new_tweet_ids.json'), 'w') as f:
            json.dump({'new_ids': new_ids}, f)
        
        print(f"\n--- SUMMARY ---")
        print(f"New tweets: {len(new_tweets)}")
        for t in new_tweets:
            keywords = check_keywords(t['title'])
            flag = f" [{', '.join(keywords)}]" if keywords else ""
            try:
                dt = datetime.strptime(t['pub_date'], '%a, %d %b %Y %H:%M:%S %Z')
                dt_jst = dt + __import__('datetime').timedelta(hours=9)
                pub_dt = dt_jst.strftime('%Y-%m-%d %H:%M')
            except:
                pub_dt = t['pub_date']
            print(f"  - [{pub_dt}] {t['title'][:120]}{flag}")
    else:
        # Write empty file to signal no new tweets
        with open(os.path.join(NEWS_DIR, '.new_tweet_ids.json'), 'w') as f:
            json.dump({'new_ids': []}, f)
        print("\nNo new tweets found.")

if __name__ == '__main__':
    main()
